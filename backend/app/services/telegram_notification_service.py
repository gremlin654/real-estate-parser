"""
Telegram Notification Service — сервис отправки уведомлений в Telegram.

Модуль предоставляет класс TelegramNotificationService для отправки
уведомлений о новых объявлениях пользователям Telegram с учётом
их подписок и предпочтений.

Особенности:
- Async/await паттерны для всех операций
- Retry с exponential backoff (5s, 10s, 20s)
- Обработка ошибок (Forbidden, RetryAfter, NetworkError)
- Логирование всех попыток отправки
- Отправка с фото если доступно

Пример использования:
    from app.services.telegram_notification_service import TelegramNotificationService

    async with AsyncSession() as session:
        service = TelegramNotificationService(session)
        try:
            result = await service.send_new_listings_notifications(new_listings)
            # result = {'sent': 5, 'failed': 1, 'blocked': 0, 'rate_limited': 0, 'skipped_no_match': 0}
        finally:
            await service.close()
"""

import asyncio
from typing import Any
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramNetworkError,
    TelegramAPIError,
)
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.config import settings
from app.core.redis_client import get_redis
from app.models.listing import Listing
from app.models.telegram_user import (
    TelegramUser,
    TelegramSubscription,
    TelegramNotificationLog,
    TelegramNotificationStatus,
    TelegramNotificationEventType,
)
from app.services.telegram_subscription_service import TelegramSubscriptionService
from app.services.telegram_message_builder import TelegramMessageBuilder
from app.services.telegram_exceptions import NotificationSendError


class TelegramNotificationService:
    """
    Сервис для отправки уведомлений в Telegram.

    Отвечает за:
    - Отправку уведомлений о новых объявлениях
    - Retry логику с exponential backoff
    - Обработку ошибок API Telegram
    - Логирование всех попыток отправки

    Attributes:
        db: Асинхронная сессия базы данных
        bot: Экземпляр Telegram Bot (или None если отключён)
        subscription_service: Сервис подписок для matching

    Class Attributes:
        _shared_bot: Shared bot instance установленный через set_shared_bot()
    """

    _shared_bot: Bot | None = None  # Class variable для shared instance

    def __init__(self, db_session: AsyncSession, bot: Bot | None = None):
        """
        Инициализирует сервис уведомлений.

        Args:
            db_session: Асинхронная сессия базы данных
            bot: Опциональный Bot instance. Если не указан, используется shared bot.
        """
        self.db = db_session
        self.bot: Bot | None = bot or self._shared_bot
        self.subscription_service = TelegramSubscriptionService(db_session)

        if self.bot:
            logger.debug("TelegramNotificationService initialized with bot instance")
        else:
            logger.warning(
                "TelegramNotificationService initialized without bot "
                "(TELEGRAM_BOT_ENABLED=False or shared bot not set)"
            )

    @classmethod
    def set_shared_bot(cls, bot: Bot):
        """
        Установить shared bot instance при старте приложения.

        Это позволяет избежать утечки ресурсов — bot создаётся один раз
        и переиспользуется всеми экземплярами сервиса.

        Args:
            bot: Экземпляр aiogram Bot
        """
        cls._shared_bot = bot
        logger.info("Shared Telegram bot instance configured")

    async def close(self):
        """Закрывает соединение с Telegram Bot API.

        НЕ закрывает shared bot — только если он создан локально.
        """
        # НЕ закрывать shared bot, только если он создан локально
        if self.bot and self.bot is not self._shared_bot:
            await self.bot.close()
            logger.info("Local Telegram bot connection closed")

    async def send_new_listings_notifications(
        self, new_listings: list[Listing]
    ) -> dict[str, int]:
        """
        Отправляет уведомления о новых объявлениях всем подходящим подписчикам.

        Args:
            new_listings: Список новых объявлений

        Returns:
            Словарь со статистикой отправки
        """
        return await self._send_listings_notifications(
            listings=new_listings,
            event_type="new_listing",
        )

    async def send_price_drop_notifications(
        self, price_drop_listings: list[Listing]
    ) -> dict[str, int]:
        """
        Отправляет уведомления о падении цены всем подходящим подписчикам.

        Args:
            price_drop_listings: Список объявлений с падением цены

        Returns:
            Словарь со статистикой отправки
        """
        return await self._send_listings_notifications(
            listings=price_drop_listings,
            event_type="price_drop",
        )

    async def _send_listings_notifications(
        self,
        listings: list[Listing],
        event_type: str,
    ) -> dict[str, int]:
        """
        Отправляет уведомления о объявлениях всем подходящим подписчикам.

        Для каждого объявления находит matching subscriptions
        и отправляет уведомления соответствующим пользователям.

        Args:
            listings: Список объявлений для отправки уведомлений
            event_type: Тип события уведомления (new_listing | price_drop)

        Returns:
            Словарь со статистикой отправки:
            - sent: Количество успешных отправок
            - failed: Количество неудачных отправок
            - blocked: Количество заблокированных пользователей
            - rate_limited: Количество rate limited ответов
            - skipped_no_match: Количество объявлений без подходящих подписок

        Example:
            >>> result = await service.send_new_listings_notifications([listing1, listing2])
            >>> print(result)
            {'sent': 5, 'failed': 1, 'blocked': 0, 'rate_limited': 0, 'skipped_no_match': 2}
        """
        if not self.bot:
            logger.warning("Telegram bot not configured, skipping notifications")
            return {
                "sent": 0,
                "failed": 0,
                "blocked": 0,
                "rate_limited": 0,
                "skipped_no_match": len(listings),
                "duplicate": 0,
                "ratelimited_user": 0,
            }

        logger.info(
            f"Processing {len(listings)} listings for Telegram notifications "
            f"(event_type={event_type})"
        )

        stats = {
            "sent": 0,
            "failed": 0,
            "blocked": 0,
            "rate_limited": 0,
            "skipped_no_match": 0,
            "duplicate": 0,
            "ratelimited_user": 0,
        }

        for listing in listings:
            try:
                # Находим подходящие подписки
                subscriptions = (
                    await self.subscription_service.get_matching_subscriptions(
                        listing,
                        event_type=event_type,
                    )
                )

                if not subscriptions:
                    stats["skipped_no_match"] += 1
                    logger.debug(
                        f"No matching subscriptions for listing {listing.kufar_id}"
                    )
                    continue

                logger.info(
                    f"Found {len(subscriptions)} matching subscriptions "
                    f"for listing {listing.kufar_id}"
                )

                # Отправляем каждому пользователю
                for subscription in subscriptions:
                    try:
                        user = await self.subscription_service.get_user_by_id(
                            subscription.user_id
                        )
                        if not user:
                            logger.warning(
                                f"User {subscription.user_id} not found for subscription {subscription.id}"
                            )
                            continue

                        # Пропускаем заблокированных
                        if user.blocked_by_user or not user.is_active:
                            logger.debug(
                                f"Skipping user {user.id} (blocked={user.blocked_by_user}, active={user.is_active})"
                            )
                            continue

                        status = await self.send_listing_to_user(
                            user, listing, subscription, event_type
                        )
                        stats[status] += 1

                    except Exception as e:
                        logger.error(
                            f"Error sending notification to user {subscription.user_id}: {e}"
                        )
                        stats["failed"] += 1

            except Exception as e:
                logger.error(f"Error processing listing {listing.kufar_id}: {e}")
                stats["failed"] += 1

        logger.info(
            f"Notification stats: sent={stats['sent']}, failed={stats['failed']}, "
            f"blocked={stats['blocked']}, rate_limited={stats['rate_limited']}, "
            f"duplicate={stats['duplicate']}, ratelimited_user={stats['ratelimited_user']}, "
            f"skipped={stats['skipped_no_match']}"
        )
        return stats

    async def send_listing_to_user(
        self,
        user: TelegramUser,
        listing: Listing,
        subscription: TelegramSubscription,
        event_type: str = "new_listing",
    ) -> str:
        """
        Отправляет одно объявление пользователю.

        Args:
            user: Объект пользователя Telegram
            listing: Объект объявления
            subscription: Объект подписки (для форматирования)
            event_type: Тип события (new_listing | price_drop)

        Returns:
            Статус отправки: 'sent' | 'failed' | 'blocked' | 'rate_limited' | 'duplicate' | 'ratelimited_user'

        Raises:
            Exception: При непредвиденных ошибках (логируется и возвращает 'failed')
        """
        if not self.bot:
            logger.error("Telegram bot not configured")
            return "failed"

        # Для new_listing дедупликация обязательна, чтобы не слать один и тот же лот повторно.
        # Для price_drop НЕ применяем "вечную" дедупликацию по listing_id: цена может
        # снижаться несколько раз в разные сканы и каждое снижение нужно отправлять.
        if event_type == "new_listing":
            already_sent = await self._is_duplicate_notification(
                user.id, listing.id, subscription.id, event_type
            )
            if already_sent:
                logger.info(
                    f"Skipping duplicate notification for user={user.id}, "
                    f"listing={listing.kufar_id}, event_type={event_type}"
                )
                return "duplicate"

        is_rate_limited = await self._check_user_rate_limit(user)
        if is_rate_limited:
            logger.info(
                f"Skipping rate-limited notification for user={user.id}, "
                f"listing={listing.kufar_id}"
            )
            return "ratelimited_user"

        # Форматируем сообщение
        message = self._format_listing_message(listing, subscription, event_type)
        keyboard = self._build_listing_keyboard(listing)

        # Определяем есть ли фото
        image_url = None
        if listing.images and len(listing.images) > 0:
            image_url = listing.images[0]

        try:
            # Отправляем с retry логикой
            message_id = await self._retry_with_backoff(
                self._send_message_with_photo,
                user.telegram_id,
                message,
                keyboard,
                image_url,
            )

            # Логируем успешную отправку
            await self._log_notification(
                user_id=user.id,
                listing_id=listing.id,
                subscription_id=subscription.id,
                status="sent",
                message_id=message_id,
                event_type=event_type,
            )

            logger.info(
                f"Successfully sent notification to user {user.telegram_id} "
                f"for listing {listing.kufar_id}"
            )
            return "sent"

        except TelegramForbiddenError as e:
            # Пользователь заблокировал бота
            logger.warning(f"User {user.telegram_id} blocked the bot: {e}")
            user.blocked_by_user = True
            await self.db.commit()

            await self._log_notification(
                user_id=user.id,
                listing_id=listing.id,
                subscription_id=subscription.id,
                status="blocked",
                error_message=str(e),
                event_type=event_type,
            )
            return "blocked"

        except TelegramRetryAfter as e:
            # Rate limit — ждём и пробуем снова
            logger.warning(
                f"Rate limited for user {user.telegram_id}, retry after {e.retry_after}s: {e}"
            )
            await self._log_notification(
                user_id=user.id,
                listing_id=listing.id,
                subscription_id=subscription.id,
                status="rate_limited",
                error_message=str(e),
                event_type=event_type,
            )
            return "rate_limited"

        except TelegramNetworkError as e:
            # Сетевая ошибка
            logger.error(f"Network error sending to user {user.telegram_id}: {e}")
            await self._log_notification(
                user_id=user.id,
                listing_id=listing.id,
                subscription_id=subscription.id,
                status="failed",
                error_message=str(e),
                event_type=event_type,
            )
            return "failed"

        except Exception as e:
            # Любая другая ошибка
            logger.error(f"Unexpected error sending to user {user.telegram_id}: {e}")
            await self._log_notification(
                user_id=user.id,
                listing_id=listing.id,
                subscription_id=subscription.id,
                status="failed",
                error_message=str(e),
                event_type=event_type,
            )
            return "failed"

    async def _send_message_with_photo(
        self,
        telegram_id: int,
        message: str,
        keyboard: InlineKeyboardMarkup,
        image_url: str | None = None,
    ) -> int | None:
        """
        Отправляет сообщение с фото или без.

        Args:
            telegram_id: Telegram ID пользователя
            message: Текст сообщения
            keyboard: Inline клавиатура
            image_url: URL фото (опционально)

        Returns:
            message_id отправленного сообщения
        """
        if image_url:
            # Отправляем фото с подписью
            msg = await self.bot.send_photo(
                chat_id=telegram_id,
                photo=image_url,
                caption=message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return msg.message_id
        else:
            # Отправляем текстовое сообщение
            msg = await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return msg.message_id

    async def _retry_with_backoff(
        self, func, *args, max_retries: int | None = None, **kwargs
    ):
        """
        Выполняет функцию с exponential backoff retry логикой.

        Интервалы: 5s, 10s, 20s (максимум 3 попытки по умолчанию)
        Для TelegramRetryAfter — ожидание ограничено максимум 60 секундами.

        Args:
            func: Async функция для вызова
            *args: Позиционные аргументы для функции
            max_retries: Максимальное количество попыток (по умолчанию из settings)
            **kwargs: Именованные аргументы для функции

        Returns:
            Результат выполнения функции

        Raises:
            TelegramForbiddenError: Немедленно (без retry)
            NotificationSendError: После исчерпания retry для RateLimit
            TelegramNetworkError: После исчерпания retry
            Exception: После исчерпания retry
        """
        if max_retries is None:
            max_retries = settings.TELEGRAM_MAX_RETRIES
        base_delay = settings.TELEGRAM_RETRY_DELAY_SECONDS

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except TelegramForbiddenError:
                # Не retry — пользователь заблокировал
                raise
            except TelegramRetryAfter as e:
                # Ограничить ожидание максимум 60 секундами
                wait_time = min(e.retry_after, 60)

                if attempt >= max_retries - 1:
                    logger.error(
                        f"Rate limited after {max_retries} attempts, giving up"
                    )
                    raise NotificationSendError(
                        f"Rate limited after {max_retries} attempts"
                    )

                logger.warning(
                    f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(wait_time)
                continue
            except TelegramNetworkError as e:
                if attempt >= max_retries - 1:
                    logger.error(f"Network error after {max_retries} attempts: {e}")
                    raise
                wait_time = base_delay * (2**attempt)
                logger.warning(
                    f"Network error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries}): {e}"
                )
                await asyncio.sleep(wait_time)
            except Exception:
                if attempt >= max_retries - 1:
                    logger.error(f"Unexpected error after {max_retries} attempts")
                    raise
                wait_time = base_delay * (2**attempt)
                logger.warning(
                    f"Unexpected error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(wait_time)

        raise NotificationSendError("Max retries exceeded")

    async def _handle_send_error(self, error: Exception, user: TelegramUser) -> str:
        """
        Обрабатывает ошибки отправки и возвращает статус.

        Args:
            error: Исключение которое произошло при отправке
            user: Объект пользователя (для обновления blocked_by_user)

        Returns:
            Статус: 'blocked' | 'rate_limited' | 'retry' | 'failed'
        """
        if isinstance(error, TelegramForbiddenError):
            user.blocked_by_user = True
            await self.db.commit()
            logger.warning(f"User {user.telegram_id} blocked the bot")
            return "blocked"

        elif isinstance(error, TelegramRetryAfter):
            logger.warning(
                f"Rate limited for user {user.telegram_id}, retry after {error.retry_after}s"
            )
            return "rate_limited"

        elif isinstance(error, TelegramNetworkError):
            logger.error(f"Network error for user {user.telegram_id}: {error}")
            return "retry"

        else:
            logger.error(f"Unexpected error for user {user.telegram_id}: {error}")
            return "failed"

    async def _log_notification(
        self,
        user_id: UUID,
        listing_id: UUID,
        subscription_id: UUID,
        status: str,
        error_message: str | None = None,
        retry_count: int = 0,
        message_id: int | None = None,
        event_type: str | None = None,
    ):
        """
        Записывает попытку отправки уведомления в лог.

        Args:
            user_id: UUID пользователя
            listing_id: UUID объявления
            subscription_id: UUID подписки
            status: Статус отправки (sent/failed/blocked/rate_limited)
            error_message: Текст ошибки (если была)
            retry_count: Количество повторных попыток
            message_id: ID сообщения в Telegram (при успешной отправке)
            event_type: Тип события (new_listing | price_drop) для дедупликации
        """
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = TelegramNotificationEventType(event_type)
            except ValueError:
                logger.warning(f"Unknown event_type '{event_type}', storing NULL")

        log_entry = TelegramNotificationLog(
            user_id=user_id,
            listing_id=listing_id,
            subscription_id=subscription_id,
            status=TelegramNotificationStatus(status),
            event_type=event_type_enum,
            error_message=error_message,
            retry_count=retry_count,
            response_message_id=message_id,
        )
        self.db.add(log_entry)

        try:
            await self.db.commit()
            logger.debug(
                f"Logged notification: user={user_id}, listing={listing_id}, "
                f"subscription={subscription_id}, status={status}"
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error logging notification: {e}")

    async def _is_duplicate_notification(
        self,
        user_id: UUID,
        listing_id: UUID,
        subscription_id: UUID,
        event_type: str,
    ) -> bool:
        """
        Проверяет, было ли уже отправлено уведомление для данной комбинации.

        Проверяет наличие записи в TelegramNotificationLog с теми же
        user_id, listing_id, subscription_id и event_type.

        Args:
            user_id: UUID пользователя
            listing_id: UUID объявления
            subscription_id: UUID подписки
            event_type: Тип события (new_listing | price_drop)

        Returns:
            True если уведомление уже было отправлено
        """
        if not event_type:
            return False

        try:
            event_type_enum = TelegramNotificationEventType(event_type)
        except ValueError:
            return False

        result = await self.db.execute(
            select(TelegramNotificationLog)
            .where(
                TelegramNotificationLog.user_id == user_id,
                TelegramNotificationLog.listing_id == listing_id,
                TelegramNotificationLog.subscription_id == subscription_id,
                TelegramNotificationLog.event_type == event_type_enum,
            )
            .limit(1)
        )
        existing = result.scalar_one_or_none()
        return existing is not None

    async def _check_user_rate_limit(self, user: TelegramUser) -> bool:
        """
        Проверяет, не превысил ли пользователь лимит уведомлений за час.

        Сначала пытается использовать Redis (fast path), если Redis недоступен —
        использует PostgreSQL как fallback (считает уведомления за последний час).

        Args:
            user: Объект пользователя Telegram

        Returns:
            True если лимит превышен (нужно пропустить отправку), False если можно отправлять
        """
        limit = settings.TELEGRAM_USER_RATE_LIMIT_PER_HOUR
        if limit <= 0:
            return False

        if user.telegram_id is None:
            return False

        try:
            redis = await get_redis()
            hour_key = datetime.utcnow().strftime("%Y%m%d%H")
            redis_key = f"telegram:ratelimit:user:{user.id}:{hour_key}"

            count = await redis.get(redis_key)
            if count is not None and int(count) >= limit:
                logger.info(
                    f"User {user.id} rate limited (Redis): {count}/{limit} in current hour"
                )
                return True

            pipe = redis.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, 3900)
            await pipe.execute()

        except Exception as redis_err:
            logger.warning(
                f"Redis rate limit check failed, falling back to DB: {redis_err}"
            )
            try:
                from datetime import timedelta
                from sqlalchemy import func, and_
                from app.models.telegram_user import TelegramNotificationLog

                one_hour_ago = datetime.utcnow() - timedelta(hours=1)
                result = await self.db.execute(
                    select(func.count(TelegramNotificationLog.id)).where(
                        and_(
                            TelegramNotificationLog.user_id == user.id,
                            TelegramNotificationLog.sent_at >= one_hour_ago,
                            TelegramNotificationLog.status
                            == TelegramNotificationStatus.sent,
                        )
                    )
                )
                count = result.scalar() or 0
                if count >= limit:
                    logger.info(
                        f"User {user.id} rate limited (DB): {count}/{limit} in last hour"
                    )
                    return True
            except Exception as db_err:
                logger.error(f"DB fallback rate limit check also failed: {db_err}")

        return False

    def _format_listing_message(
        self,
        listing: Listing,
        subscription: TelegramSubscription,
        event_type: str = "new_listing",
    ) -> str:
        """
        Форматирует сообщение для Telegram из данных объявления.

        Args:
            listing: Объект объявления
            subscription: Объект подписки (для определения валюты и фильтров)
            event_type: Тип события (new_listing | price_drop)

        Returns:
            Отформатированное сообщение для Telegram
        """
        # Определяем deal_percent и price_drop_percent если доступны
        deal_percent = getattr(listing, "deal_percent", None)
        price_drop_percent = getattr(listing, "drop_percent", None)
        price_drop_amount = getattr(listing, "price_drop_amount", None)

        # Цена за м² в USD
        price_per_m2_usd = 0.0
        if listing.price_per_m2_usd:
            price_per_m2_usd = float(listing.price_per_m2_usd)

        return TelegramMessageBuilder.build_listing_message(
            city=listing.city,
            address=listing.address or "Не указан",
            rooms=listing.rooms or 0,
            area=listing.area or 0.0,
            floor=listing.floor or 0,
            total_floors=listing.total_floors,
            price_byn=listing.price or 0,
            price_usd=listing.price_usd or 0,
            price_per_m2_usd=price_per_m2_usd,
            listing_url=listing.url,
            deal_percent=deal_percent,
            price_drop_percent=price_drop_percent,
            price_drop_amount=price_drop_amount,
            event_type=event_type,
        )

    def _build_listing_keyboard(self, listing: Listing) -> InlineKeyboardMarkup:
        """
        Создаёт inline клавиатуру для объявления.

        Кнопки:
        - 🔗 Открыть на Kufar (URL)
        - ⚙️ Настройки уведомлений (callback)

        Args:
            listing: Объект объявления

        Returns:
            InlineKeyboardMarkup с кнопками действий
        """
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔗 Открыть на Kufar",
                        url=listing.url,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Настройки уведомлений",
                        callback_data="settings",
                    )
                ],
            ]
        )
        return keyboard

    async def cleanup_old_logs(self, retention_days: int | None = None) -> int:
        """
        Удалить старые записи лога уведомлений.

        Args:
            retention_days: Количество дней хранения. Если None — из settings.

        Returns:
            Количество удалённых записей.
        """
        if retention_days is None:
            retention_days = settings.TELEGRAM_NOTIFICATION_LOG_RETENTION_DAYS

        cutoff = datetime.utcnow() - timedelta(days=retention_days)

        result = await self.db.execute(
            delete(TelegramNotificationLog).where(
                TelegramNotificationLog.sent_at < cutoff
            )
        )
        deleted = result.rowcount
        logger.info(
            f"Cleanup: deleted {deleted} TelegramNotificationLog records older than {retention_days} days"
        )
        return deleted
