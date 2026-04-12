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

from app.config import settings
from app.models.listing import Listing
from app.models.telegram_user import (
    TelegramUser,
    TelegramSubscription,
    TelegramNotificationLog,
    TelegramNotificationStatus,
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

        Для каждого нового объявления находит matching subscriptions
        и отправляет уведомления соответствующим пользователям.

        Args:
            new_listings: Список новых объявлений для отправки уведомлений

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
                "skipped_no_match": len(new_listings),
            }

        stats = {
            "sent": 0,
            "failed": 0,
            "blocked": 0,
            "rate_limited": 0,
            "skipped_no_match": 0,
        }

        for listing in new_listings:
            try:
                # Находим подходящие подписки
                subscriptions = (
                    await self.subscription_service.get_matching_subscriptions(listing)
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
                            user, listing, subscription
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
            f"skipped={stats['skipped_no_match']}"
        )
        return stats

    async def send_listing_to_user(
        self,
        user: TelegramUser,
        listing: Listing,
        subscription: TelegramSubscription,
    ) -> str:
        """
        Отправляет одно объявление пользователю.

        Args:
            user: Объект пользователя Telegram
            listing: Объект объявления
            subscription: Объект подписки (для форматирования)

        Returns:
            Статус отправки: 'sent' | 'failed' | 'blocked' | 'rate_limited'

        Raises:
            Exception: При непредвиденных ошибках (логируется и возвращает 'failed')
        """
        if not self.bot:
            logger.error("Telegram bot not configured")
            return "failed"

        # Форматируем сообщение
        message = self._format_listing_message(listing, subscription)
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

    async def _retry_with_backoff(self, func, *args, max_retries: int | None = None, **kwargs):
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
        """
        log_entry = TelegramNotificationLog(
            user_id=user_id,
            listing_id=listing_id,
            subscription_id=subscription_id,
            status=TelegramNotificationStatus(status),
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

    def _format_listing_message(
        self, listing: Listing, subscription: TelegramSubscription
    ) -> str:
        """
        Форматирует сообщение для Telegram из данных объявления.

        Args:
            listing: Объект объявления
            subscription: Объект подписки (для определения валюты и фильтров)

        Returns:
            Отформатированное сообщение для Telegram
        """
        # Определяем deal_percent и price_drop_percent если доступны
        deal_percent = getattr(listing, "deal_percent", None)
        price_drop_percent = getattr(listing, "drop_percent", None)

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
            total_floors=listing.total_floors or 0,
            price_byn=listing.price or 0,
            price_usd=listing.price_usd or 0,
            price_per_m2_usd=price_per_m2_usd,
            listing_url=listing.url,
            deal_percent=deal_percent,
            price_drop_percent=price_drop_percent,
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
