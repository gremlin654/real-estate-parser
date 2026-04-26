"""
Service layer для управления подписками Telegram бота.

Предоставляет CRUD операции для пользователей и подписок,
а также логику matching объявлений с подписками.

Пример использования:
    from app.services.telegram_subscription_service import TelegramSubscriptionService

    async with AsyncSession() as session:
        service = TelegramSubscriptionService(session)
        user = await service.create_user(telegram_id=12345, username="test_user")
        subscription = await service.create_subscription(
            user_id=user.id,
            city="minsk",
            rooms=[1, 2],
            price_min=30000,
            price_max=60000,
        )
"""

from typing import List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select, and_, or_, func, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.listing import Listing
from app.models.telegram_user import TelegramUser, TelegramSubscription
from app.services.telegram_validators import (
    TelegramSubscriptionValidator,
    MAX_SUBSCRIPTIONS_PER_USER,
)
from app.services.telegram_exceptions import (
    SubscriptionNotFoundError,
    UserNotFoundError,
)


class TelegramSubscriptionService:
    """
    Сервис для управления подписками Telegram.

    Предоставляет операции CRUD для пользователей и подписок,
    а также логику matching объявлений с активными подписками.

    Attributes:
        db: Асинхронная сессия базы данных
        validator: Экземпляр валидатора параметров
    """

    def __init__(self, db: AsyncSession):
        """
        Инициализирует сервис.

        Args:
            db: Асинхронная сессия базы данных
        """
        self.db = db
        self.validator = TelegramSubscriptionValidator()

    # === User Management ===

    async def create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: str = "ru",
    ) -> TelegramUser:
        """
        Создать или получить пользователя Telegram (идемпотентный).

        Если пользователь с таким telegram_id уже существует, возвращает его.
        Иначе создаёт нового.

        Args:
            telegram_id: Идентификатор пользователя в Telegram
            username: Username пользователя в Telegram
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            language_code: Код языка (ru, en, etc.)

        Returns:
            Объект TelegramUser (новый или существующий)

        Raises:
            SQLAlchemyError: При ошибке базы данных
        """
        # Проверяем существует ли пользователь
        existing = await self.get_user_by_telegram_id(telegram_id)
        if existing:
            logger.debug(f"User with telegram_id {telegram_id} already exists")
            return existing

        # Создаём нового пользователя
        user = TelegramUser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )
        self.db.add(user)

        try:
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(
                f"Created new Telegram user: telegram_id={telegram_id}, "
                f"username='{username}', user_id={user.id}"
            )
            return user
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating Telegram user: {e}")
            raise

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[TelegramUser]:
        """
        Получить пользователя по telegram_id.

        Args:
            telegram_id: Идентификатор пользователя в Telegram

        Returns:
            Объект TelegramUser или None если не найден
        """
        result = await self.db.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            logger.debug(f"Found user by telegram_id {telegram_id}: user_id={user.id}")
        else:
            logger.debug(f"User with telegram_id {telegram_id} not found")

        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[TelegramUser]:
        """
        Получить пользователя по UUID.

        Args:
            user_id: UUID пользователя

        Returns:
            Объект TelegramUser или None если не найден
        """
        result = await self.db.execute(
            select(TelegramUser).where(TelegramUser.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            logger.debug(f"Found user by id {user_id}: telegram_id={user.telegram_id}")
        else:
            logger.debug(f"User with id {user_id} not found")

        return user

    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Деактивировать пользователя (is_active=False).

        Args:
            user_id: UUID пользователя

        Returns:
            True если пользователь деактивирован, False если не найден
        """
        stmt = (
            update(TelegramUser)
            .where(TelegramUser.id == user_id)
            .values(is_active=False)
        )
        result = await self.db.execute(stmt)

        try:
            await self.db.commit()
            rows_updated = result.rowcount
            if rows_updated > 0:
                logger.info(f"Deactivated user: {user_id}")
                return True
            else:
                logger.warning(f"User {user_id} not found for deactivation")
                return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deactivating user {user_id}: {e}")
            raise

    async def activate_user(self, user_id: UUID) -> bool:
        """
        Активировать пользователя (is_active=True).

        Args:
            user_id: UUID пользователя

        Returns:
            True если пользователь активирован, False если не найден
        """
        stmt = (
            update(TelegramUser)
            .where(TelegramUser.id == user_id)
            .values(is_active=True)
        )
        result = await self.db.execute(stmt)

        try:
            await self.db.commit()
            rows_updated = result.rowcount
            if rows_updated > 0:
                logger.info(f"Activated user: {user_id}")
                return True
            else:
                logger.warning(f"User {user_id} not found for activation")
                return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error activating user {user_id}: {e}")
            raise

    # === Subscription Management ===

    async def create_subscription(
        self,
        user_id: UUID,
        city: str,
        rooms: Optional[List[int]] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        price_per_m2_max: Optional[float] = None,
        floor_min: Optional[int] = None,
        floor_max: Optional[int] = None,
        currency: str = "usd",
        notify_only_price_drop: bool = False,
        exclude_deal_below_percent: Optional[int] = None,
    ) -> TelegramSubscription:
        """
        Создать подписку с валидацией всех параметров.

        Проверяет:
        - Город из CITY_CHOICES
        - Комнаты: 1-4 или [5] для 5+ или None
        - Диапазон цен: 0 < price_min < price_max
        - Диапазон этажей: 0 < floor_min < floor_max
        - Валюта: byn/usd
        - Лимит: максимум 5 активных подписок на пользователя

        Args:
            user_id: UUID пользователя
            city: Город для мониторинга
            rooms: Список комнат (None = любые)
            price_min: Минимальная цена
            price_max: Максимальная цена
            price_per_m2_max: Максимальная цена за м²
            floor_min: Минимальный этаж
            floor_max: Максимальный этаж
            currency: Валюта расчётов
            notify_only_price_drop: Уведомлять только о падении цены
            exclude_deal_below_percent: Исключить deal ниже X%

        Returns:
            Объект TelegramSubscription

        Raises:
            InvalidCityError: Если город недопустим
            InvalidRoomsError: Если комнаты недопустимы
            InvalidPriceRangeError: Если диапазон цен недопустим
            InvalidFloorRangeError: Если диапазон этажей недопустим
            InvalidCurrencyError: Если валюта недопустима
            SubscriptionLimitExceeded: Если превышен лимит подписок
            UserNotFoundError: Если пользователь не найден
            SQLAlchemyError: При ошибке базы данных
        """
        # Валидация параметров
        self.validator.validate_city(city)
        self.validator.validate_rooms(rooms)
        self.validator.validate_price_range(price_min, price_max)
        self.validator.validate_floor_range(floor_min, floor_max)
        self.validator.validate_currency(currency)
        self.validator.validate_price_per_m2_max(price_per_m2_max)

        # Проверяем что пользователь существует
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # Проверяем лимит подписок
        current_count = await self.get_user_subscription_count(user_id)
        self.validator.validate_subscription_limit(
            current_count, MAX_SUBSCRIPTIONS_PER_USER
        )

        # Создаём подписку
        subscription = TelegramSubscription(
            user_id=user_id,
            city=city,
            rooms=rooms,
            price_min=price_min,
            price_max=price_max,
            price_per_m2_max=price_per_m2_max,
            floor_min=floor_min,
            floor_max=floor_max,
            currency=currency,
            notify_only_price_drop=notify_only_price_drop,
            exclude_deal_below_percent=exclude_deal_below_percent,
        )
        self.db.add(subscription)

        try:
            await self.db.commit()
            await self.db.refresh(subscription)
            logger.info(
                f"Created subscription {subscription.id} for user {user_id}: "
                f"city={city}, rooms={rooms}, price={price_min}-{price_max} {currency}"
            )
            return subscription
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating subscription for user {user_id}: {e}")
            raise

    async def get_subscription_by_id(
        self, subscription_id: UUID
    ) -> Optional[TelegramSubscription]:
        """
        Получить подписку по ID.

        Args:
            subscription_id: UUID подписки

        Returns:
            Объект TelegramSubscription или None если не найдена
        """
        result = await self.db.execute(
            select(TelegramSubscription).where(
                TelegramSubscription.id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            logger.debug(f"Found subscription: {subscription_id}")
        else:
            logger.debug(f"Subscription {subscription_id} not found")

        return subscription

    async def get_active_subscriptions(
        self, user_id: UUID
    ) -> List[TelegramSubscription]:
        """
        Получить все активные подписки пользователя.

        Args:
            user_id: UUID пользователя

        Returns:
            Список активных подписок
        """
        result = await self.db.execute(
            select(TelegramSubscription)
            .where(
                and_(
                    TelegramSubscription.user_id == user_id,
                    TelegramSubscription.is_active == True,
                )
            )
            .order_by(TelegramSubscription.created_at.desc())
        )
        subscriptions = result.scalars().all()

        logger.debug(
            f"Found {len(subscriptions)} active subscriptions for user {user_id}"
        )
        return list(subscriptions)

    async def update_subscription(
        self,
        subscription_id: UUID,
        **kwargs,
    ) -> Optional[TelegramSubscription]:
        """
        Обновить параметры подписки.

        Args:
            subscription_id: UUID подписки
            **kwargs: Параметры для обновления
                (city, rooms, price_min, price_max, price_per_m2_max,
                 floor_min, floor_max, currency, notify_only_price_drop,
                 exclude_deal_below_percent, is_active)

        Returns:
            Обновлённый объект TelegramSubscription или None если не найдена

        Raises:
            InvalidCityError: Если город недопустим
            InvalidRoomsError: Если комнаты недопустимы
            InvalidPriceRangeError: Если диапазон цен недопустим
            InvalidFloorRangeError: Если диапазон этажей недопустим
            InvalidCurrencyError: Если валюта недопустима
            SubscriptionNotFoundError: Если подписка не найдена
            SQLAlchemyError: При ошибке базы данных
        """
        # Валидация параметров если они переданы
        if "city" in kwargs:
            self.validator.validate_city(kwargs["city"])
        if "rooms" in kwargs:
            self.validator.validate_rooms(kwargs["rooms"])

        price_min = kwargs.get(
            "price_min",
            (
                (await self.get_subscription_by_id(subscription_id)).price_min
                if await self.get_subscription_by_id(subscription_id)
                else None
            ),
        )
        price_max = kwargs.get(
            "price_max",
            (
                (await self.get_subscription_by_id(subscription_id)).price_max
                if await self.get_subscription_by_id(subscription_id)
                else None
            ),
        )
        if "price_min" in kwargs or "price_max" in kwargs:
            self.validator.validate_price_range(
                kwargs.get("price_min", price_min),
                kwargs.get("price_max", price_max),
            )

        if "floor_min" in kwargs or "floor_max" in kwargs:
            sub = await self.get_subscription_by_id(subscription_id)
            floor_min = kwargs.get("floor_min", sub.floor_min if sub else None)
            floor_max = kwargs.get("floor_max", sub.floor_max if sub else None)
            self.validator.validate_floor_range(floor_min, floor_max)

        if "currency" in kwargs:
            self.validator.validate_currency(kwargs["currency"])
        if "price_per_m2_max" in kwargs:
            self.validator.validate_price_per_m2_max(kwargs["price_per_m2_max"])

        # Находим подписку
        subscription = await self.get_subscription_by_id(subscription_id)
        if not subscription:
            raise SubscriptionNotFoundError(subscription_id)

        # Обновляем поля
        for key, value in kwargs.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(subscription)
            logger.info(
                f"Updated subscription {subscription_id}: {', '.join(kwargs.keys())}"
            )
            return subscription
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating subscription {subscription_id}: {e}")
            raise

    async def delete_subscription(self, subscription_id: UUID) -> bool:
        """
        Удалить подписку (soft delete: is_active=False).

        Args:
            subscription_id: UUID подписки

        Returns:
            True если подписка деактивирована, False если не найдена
        """
        stmt = (
            update(TelegramSubscription)
            .where(TelegramSubscription.id == subscription_id)
            .values(is_active=False)
        )
        result = await self.db.execute(stmt)

        try:
            await self.db.commit()
            rows_updated = result.rowcount
            if rows_updated > 0:
                logger.info(f"Soft deleted subscription: {subscription_id}")
                return True
            else:
                logger.warning(f"Subscription {subscription_id} not found for deletion")
                return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deleting subscription {subscription_id}: {e}")
            raise

    async def hard_delete_subscription(self, subscription_id: UUID) -> bool:
        """
        Удалить подписку полностью из БД.

        Args:
            subscription_id: UUID подписки

        Returns:
            True если подписка удалена, False если не найдена
        """
        stmt = sa_delete(TelegramSubscription).where(
            TelegramSubscription.id == subscription_id
        )
        result = await self.db.execute(stmt)

        try:
            await self.db.commit()
            rows_deleted = result.rowcount
            if rows_deleted > 0:
                logger.info(f"Hard deleted subscription: {subscription_id}")
                return True
            else:
                logger.warning(
                    f"Subscription {subscription_id} not found for hard deletion"
                )
                return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error hard deleting subscription {subscription_id}: {e}")
            raise

    # === Matching Logic ===

    async def get_matching_subscriptions(
        self,
        listing: Listing,
        event_type: str = "new_listing",
    ) -> List[TelegramSubscription]:
        """
        Найти все активные подписки которые соответствуют объявлению.

        Критерии matching:
        - city совпадает
        - rooms совпадает (если rooms=None или [] в подписке — любые комнаты)
        - price_min <= listing.price <= price_max (если указаны)
        - floor_min <= listing.floor <= floor_max (если указаны)
        - price_per_m2_max >= listing.price_per_m2 (если указан)
        - notify_only_price_drop (если включен — только событие price_drop)
        - exclude_deal_below_percent (если указан — нужен deal_score >= порога)

        Args:
            listing: Объект Listing для проверки соответствия
            event_type: Тип события уведомления: new_listing | price_drop

        Returns:
            Список подписок которые соответствуют объявлению
        """
        # Базовый запрос: активные подписки с совпадающим городом
        query = select(TelegramSubscription).where(
            and_(
                TelegramSubscription.is_active == True,
                TelegramSubscription.city == listing.city,
            )
        )

        result = await self.db.execute(query)
        all_subscriptions = result.scalars().all()

        matching = []

        for sub in all_subscriptions:
            # Проверяем тип события
            if not self._matches_event_type(sub, event_type):
                continue

            # Проверяем комнаты
            if not self._matches_rooms(sub.rooms, listing.rooms):
                continue

            # Проверяем цену
            if not self._matches_price(sub, listing):
                continue

            # Проверяем этаж
            if not self._matches_floor(sub, listing):
                continue

            # Проверяем цену за м²
            if not self._matches_price_per_m2(sub, listing):
                continue

            # Проверяем минимальный deal score
            if not self._matches_deal_score(sub, listing):
                continue

            matching.append(sub)

        logger.debug(
            f"Found {len(matching)} matching subscriptions for listing "
            f"{listing.kufar_id} (city={listing.city}, rooms={listing.rooms})"
        )
        return matching

    def _matches_rooms(self, sub_rooms: Optional[list], listing_rooms: int) -> bool:
        """
        Проверяет соответствие комнат.

        Правила:
        - sub_rooms = None или [] — любые комнаты подходят
        - sub_rooms = [5] — подходит если listing_rooms >= 5
        - sub_rooms = [1, 2, ...] — listing_rooms должен быть в списке

        Args:
            sub_rooms: Список комнат из подписки
            listing_rooms: Количество комнат в объявлении

        Returns:
            True если комнаты соответствуют
        """
        # None или пустой список — любые комнаты
        if sub_rooms is None or len(sub_rooms) == 0:
            return True

        # [5] — 5+ комнат
        if sub_rooms == [5]:
            return listing_rooms >= 5

        # Конкретные комнаты — проверяем вхождение
        return listing_rooms in sub_rooms

    def _matches_price(
        self, subscription: TelegramSubscription, listing: Listing
    ) -> bool:
        """
        Проверяет соответствие цены.

        Args:
            subscription: Объект подписки
            listing: Объект объявления

        Returns:
            True если цена соответствует
        """
        # Определяем какую цену использовать (зависит от валюты подписки)
        if subscription.currency == "usd":
            listing_price = listing.price_usd
        else:
            listing_price = listing.price

        # Если цена в объявлении None — не можем сравнить, пропускаем
        if listing_price is None:
            return False

        # Проверяем минимальную цену
        if subscription.price_min is not None:
            if listing_price < subscription.price_min:
                return False

        # Проверяем максимальную цену
        if subscription.price_max is not None:
            if listing_price > subscription.price_max:
                return False

        return True

    def _matches_floor(
        self, subscription: TelegramSubscription, listing: Listing
    ) -> bool:
        """
        Проверяет соответствие этажа.

        Args:
            subscription: Объект подписки
            listing: Объект объявления

        Returns:
            True если этаж соответствует
        """
        # Если в подписке нет фильтра по этажу — этаж объявления не важен
        if subscription.floor_min is None and subscription.floor_max is None:
            return True

        # Если фильтр по этажу задан, но в объявлении этаж неизвестен — не подходит
        if listing.floor is None:
            return False

        # Проверяем минимальный этаж
        if subscription.floor_min is not None:
            if listing.floor < subscription.floor_min:
                return False

        # Проверяем максимальный этаж
        if subscription.floor_max is not None:
            if listing.floor > subscription.floor_max:
                return False

        return True

    def _matches_price_per_m2(
        self, subscription: TelegramSubscription, listing: Listing
    ) -> bool:
        """
        Проверяет соответствие цены за м².

        Args:
            subscription: Объект подписки
            listing: Объект объявления

        Returns:
            True если цена за м² соответствует
        """
        # Если в подписке не указан лимит — любые подходят
        if subscription.price_per_m2_max is None:
            return True

        # Определяем цену за м² по валюте подписки
        if subscription.currency == "usd":
            listing_price_per_m2 = listing.price_per_m2_usd
        else:
            listing_price_per_m2 = listing.price_per_m2_byn

        # Если цена за м² в объявлении None — не можем сравнить
        if listing_price_per_m2 is None:
            return False

        # Преобразуем Decimal в float для сравнения
        if hasattr(listing_price_per_m2, "__float__"):
            listing_price_per_m2 = float(listing_price_per_m2)

        # Преобразуем Decimal подписки в float
        sub_max = subscription.price_per_m2_max
        if hasattr(sub_max, "__float__"):
            sub_max = float(sub_max)

        return listing_price_per_m2 <= sub_max

    def _matches_event_type(
        self,
        subscription: TelegramSubscription,
        event_type: str,
    ) -> bool:
        """Проверяет соответствие типа события настройкам подписки."""
        notify_only_price_drop = (
            getattr(subscription, "notify_only_price_drop", False) is True
        )
        if notify_only_price_drop and event_type != "price_drop":
            return False
        return True

    def _matches_deal_score(
        self,
        subscription: TelegramSubscription,
        listing: Listing,
    ) -> bool:
        """Проверяет минимальный порог выгодности (deal score) из подписки."""
        threshold = getattr(subscription, "exclude_deal_below_percent", None)
        if not isinstance(threshold, (int, float)):
            return True

        deal_score = listing.deal_score
        if deal_score is None:
            return False

        return float(deal_score) >= float(threshold)

    # === Stats ===

    async def get_user_subscription_count(self, user_id: UUID) -> int:
        """
        Получить количество активных подписок пользователя.

        Args:
            user_id: UUID пользователя

        Returns:
            Количество активных подписок
        """
        result = await self.db.execute(
            select(func.count(TelegramSubscription.id)).where(
                and_(
                    TelegramSubscription.user_id == user_id,
                    TelegramSubscription.is_active == True,
                )
            )
        )
        count = result.scalar() or 0
        logger.debug(f"User {user_id} has {count} active subscriptions")
        return count

    async def get_total_active_subscriptions(self) -> int:
        """
        Получить общее количество активных подписок.

        Returns:
            Общее количество активных подписок в системе
        """
        result = await self.db.execute(
            select(func.count(TelegramSubscription.id)).where(
                TelegramSubscription.is_active == True
            )
        )
        count = result.scalar() or 0
        logger.info(f"Total active subscriptions: {count}")
        return count
