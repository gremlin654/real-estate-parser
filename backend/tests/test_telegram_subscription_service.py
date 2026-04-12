"""
Тесты для TelegramSubscriptionService.

Unit тесты с мок базой данных для проверки:
- User Management (CRUD)
- Subscription Management (CRUD)
- Matching Logic
- Stats
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from app.services.telegram_subscription_service import TelegramSubscriptionService
from app.models.telegram_user import TelegramUser, TelegramSubscription
from app.models.listing import Listing
from app.services.telegram_exceptions import (
    SubscriptionLimitExceeded,
    InvalidCityError,
    InvalidPriceRangeError,
    InvalidFloorRangeError,
    InvalidCurrencyError,
    SubscriptionNotFoundError,
    UserNotFoundError,
)


@pytest.mark.asyncio
class TestTelegramSubscriptionService:
    """Тесты для TelegramSubscriptionService."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def service(self, db_mock):
        """Создание сервиса."""
        return TelegramSubscriptionService(db_mock)

    # === User Management ===

    async def test_create_user_new(self, service, db_mock):
        """Тест создания нового пользователя."""
        # Mock get_user_by_telegram_id возвращает None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        # Mock refresh для установки id и is_active
        async def mock_refresh(user):
            user.id = uuid4()
            user.is_active = True  # Устанавливаем вручную т.к. мок не применяет default

        db_mock.refresh.side_effect = mock_refresh

        user = await service.create_user(
            telegram_id=12345,
            username="test_user",
            first_name="Test",
            last_name="User",
            language_code="ru",
        )

        assert user is not None
        assert user.telegram_id == 12345
        assert user.username == "test_user"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.language_code == "ru"
        assert user.is_active == True
        db_mock.add.assert_called_once()
        db_mock.commit.assert_called_once()

    async def test_create_user_existing(self, service, db_mock):
        """Тест получения существующего пользователя (идемпотентность)."""
        existing_user = MagicMock(spec=TelegramUser)
        existing_user.id = uuid4()
        existing_user.telegram_id = 12345
        existing_user.username = "existing_user"

        # Mock get_user_by_telegram_id возвращает существующего
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        db_mock.execute.return_value = mock_result

        user = await service.create_user(telegram_id=12345)

        assert user == existing_user
        db_mock.add.assert_not_called()
        db_mock.commit.assert_not_called()

    async def test_get_user_by_telegram_id_found(self, service, db_mock):
        """Тест получения пользователя по telegram_id (найден)."""
        expected_user = MagicMock(spec=TelegramUser)
        expected_user.id = uuid4()
        expected_user.telegram_id = 12345

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_user
        db_mock.execute.return_value = mock_result

        user = await service.get_user_by_telegram_id(12345)

        assert user == expected_user
        db_mock.execute.assert_called_once()

    async def test_get_user_by_telegram_id_not_found(self, service, db_mock):
        """Тест получения пользователя по telegram_id (не найден)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        user = await service.get_user_by_telegram_id(99999)

        assert user is None

    async def test_get_user_by_id_found(self, service, db_mock):
        """Тест получения пользователя по UUID (найден)."""
        user_id = uuid4()
        expected_user = MagicMock(spec=TelegramUser)
        expected_user.id = user_id
        expected_user.telegram_id = 12345

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_user
        db_mock.execute.return_value = mock_result

        user = await service.get_user_by_id(user_id)

        assert user == expected_user

    async def test_get_user_by_id_not_found(self, service, db_mock):
        """Тест получения пользователя по UUID (не найден)."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        user = await service.get_user_by_id(uuid4())

        assert user is None

    async def test_deactivate_user_success(self, service, db_mock):
        """Тест деактивации пользователя (успех)."""
        user_id = uuid4()

        # Mock execute возвращает результат с rowcount=1
        mock_result = MagicMock()
        mock_result.rowcount = 1
        db_mock.execute.return_value = mock_result

        result = await service.deactivate_user(user_id)

        assert result == True
        db_mock.commit.assert_called_once()

    async def test_deactivate_user_not_found(self, service, db_mock):
        """Тест деактивации несуществующего пользователя."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 0
        db_mock.execute.return_value = mock_result

        result = await service.deactivate_user(user_id)

        assert result == False

    async def test_activate_user_success(self, service, db_mock):
        """Тест активации пользователя (успех)."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        db_mock.execute.return_value = mock_result

        result = await service.activate_user(user_id)

        assert result == True
        db_mock.commit.assert_called_once()

    # === Subscription Management ===

    async def test_create_subscription_valid(self, service, db_mock):
        """Тест создания валидной подписки."""
        user_id = uuid4()

        # Mock для get_user_by_id
        mock_user = MagicMock(spec=TelegramUser)
        mock_user.id = user_id

        # Mock для count — возвращаем 0 (подписок нет)
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0

        # Настраиваем side_effect: get_user_by_id, get_user_subscription_count
        db_mock.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),  # get_user_by_id
            MagicMock(scalar=MagicMock(return_value=0)),  # get_user_subscription_count
        ]

        async def mock_refresh(sub):
            sub.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        subscription = await service.create_subscription(
            user_id=user_id,
            city="minsk",
            rooms=[1, 2],
            price_min=30000,
            price_max=60000,
            currency="usd",
        )

        assert subscription is not None
        assert subscription.city == "minsk"
        assert subscription.rooms == [1, 2]
        assert subscription.price_min == 30000
        assert subscription.price_max == 60000
        assert subscription.currency == "usd"
        db_mock.add.assert_called_once()
        db_mock.commit.assert_called_once()

    async def test_create_subscription_invalid_city(self, service, db_mock):
        """Тест создания подписки с невалидным городом."""
        user_id = uuid4()

        with pytest.raises(InvalidCityError):
            await service.create_subscription(
                user_id=user_id,
                city="invalid_city",
            )

        db_mock.add.assert_not_called()
        db_mock.commit.assert_not_called()

    async def test_create_subscription_invalid_price_range(self, service, db_mock):
        """Тест создания подписки с невалидным диапазоном цен."""
        user_id = uuid4()

        with pytest.raises(InvalidPriceRangeError):
            await service.create_subscription(
                user_id=user_id,
                city="minsk",
                price_min=60000,
                price_max=30000,  # min > max
            )

        db_mock.add.assert_not_called()

    async def test_create_subscription_limit_exceeded(self, service, db_mock):
        """Тест превышения лимита подписок."""
        user_id = uuid4()

        # Mock: пользователь существует, но уже 5 подписок
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = MagicMock(
            spec=TelegramUser, id=user_id
        )

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5

        db_mock.execute.side_effect = [
            mock_user_result,  # get_user_by_id
            mock_count_result,  # count
        ]

        with pytest.raises(SubscriptionLimitExceeded):
            await service.create_subscription(
                user_id=user_id,
                city="minsk",
            )

        db_mock.add.assert_not_called()

    async def test_get_active_subscriptions(self, service, db_mock):
        """Тест получения активных подписок пользователя."""
        user_id = uuid4()

        mock_sub1 = MagicMock(spec=TelegramSubscription)
        mock_sub2 = MagicMock(spec=TelegramSubscription)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub1, mock_sub2]
        db_mock.execute.return_value = mock_result

        subscriptions = await service.get_active_subscriptions(user_id)

        assert len(subscriptions) == 2
        assert subscriptions[0] == mock_sub1
        assert subscriptions[1] == mock_sub2

    async def test_update_subscription_success(self, service, db_mock):
        """Тест обновления подписки."""
        subscription_id = uuid4()

        # Mock get_subscription_by_id
        existing_sub = MagicMock(spec=TelegramSubscription)
        existing_sub.id = subscription_id
        existing_sub.city = "minsk"
        existing_sub.price_min = 30000
        existing_sub.price_max = 60000
        existing_sub.floor_min = None
        existing_sub.floor_max = None
        existing_sub.price_per_m2_max = None

        # Настраиваем side_effect для multiple вызовов get_subscription_by_id
        # (валидация вызывает его несколько раз)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_sub
        db_mock.execute.return_value = mock_result

        async def mock_refresh(sub):
            pass

        db_mock.refresh.side_effect = mock_refresh

        subscription = await service.update_subscription(
            subscription_id=subscription_id,
            city="brest",
            price_min=40000,
        )

        assert subscription is not None
        assert subscription.city == "brest"
        assert subscription.price_min == 40000
        db_mock.commit.assert_called_once()

    async def test_update_subscription_not_found(self, service, db_mock):
        """Тест обновления несуществующей подписки."""
        subscription_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        with pytest.raises(SubscriptionNotFoundError):
            await service.update_subscription(
                subscription_id=subscription_id,
                city="minsk",
            )

    async def test_soft_delete_subscription_success(self, service, db_mock):
        """Тест soft delete подписки."""
        subscription_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        db_mock.execute.return_value = mock_result

        result = await service.delete_subscription(subscription_id)

        assert result == True
        db_mock.commit.assert_called_once()

    async def test_soft_delete_subscription_not_found(self, service, db_mock):
        """Тест soft delete несуществующей подписки."""
        subscription_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 0
        db_mock.execute.return_value = mock_result

        result = await service.delete_subscription(subscription_id)

        assert result == False

    async def test_hard_delete_subscription_success(self, service, db_mock):
        """Тест hard delete подписки."""
        subscription_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 1
        db_mock.execute.return_value = mock_result

        result = await service.hard_delete_subscription(subscription_id)

        assert result == True
        db_mock.commit.assert_called_once()

    async def test_hard_delete_subscription_not_found(self, service, db_mock):
        """Тест hard delete несуществующей подписки."""
        subscription_id = uuid4()

        mock_result = MagicMock()
        mock_result.rowcount = 0
        db_mock.execute.return_value = mock_result

        result = await service.hard_delete_subscription(subscription_id)

        assert result == False

    # === Matching Logic ===

    async def test_get_matching_subscriptions_city_match(self, service, db_mock):
        """Тест matching по городу (совпадает)."""
        # Создаём тестовое объявление
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_usd = 50000
        listing.price = 150000
        listing.floor = 3
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с city=minsk
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.id = uuid4()
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = None  # Любые комнаты
        mock_sub.price_min = None
        mock_sub.price_max = None
        mock_sub.floor_min = None
        mock_sub.floor_max = None
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 1
        assert matching[0] == mock_sub

    async def test_get_matching_subscriptions_city_mismatch(self, service, db_mock):
        """Тест matching по городу (не совпадает)."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_usd = 50000
        listing.price = 150000
        listing.floor = 3
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с другим городом не будет возвращена из БД
        # (query фильтрует по city)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 0

    async def test_get_matching_subscriptions_rooms_null(self, service, db_mock):
        """Тест matching: rooms=None подписки соответствует любым комнатам."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 5  # 5 комнат
        listing.price_usd = 50000
        listing.price = 150000
        listing.floor = 3
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с rooms=None (любые комнаты)
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = None  # Любые комнаты
        mock_sub.price_min = None
        mock_sub.price_max = None
        mock_sub.floor_min = None
        mock_sub.floor_max = None
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 1

    async def test_get_matching_subscriptions_rooms_match(self, service, db_mock):
        """Тест matching: rooms совпадает."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_usd = 50000
        listing.price = 150000
        listing.floor = 3
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с rooms=[1, 2, 3]
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = [1, 2, 3]
        mock_sub.price_min = None
        mock_sub.price_max = None
        mock_sub.floor_min = None
        mock_sub.floor_max = None
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 1

    async def test_get_matching_subscriptions_rooms_mismatch(self, service, db_mock):
        """Тест matching: rooms не совпадает."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 4
        listing.price_usd = 50000
        listing.price = 150000
        listing.floor = 3
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с rooms=[1, 2] (нет 4)
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = [1, 2]
        mock_sub.price_min = None
        mock_sub.price_max = None
        mock_sub.floor_min = None
        mock_sub.floor_max = None
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 0  # 4 не в [1, 2]

    async def test_get_matching_subscriptions_price_range(self, service, db_mock):
        """Тест matching: цена в диапазоне."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_usd = 50000  # Цена в USD
        listing.price = 150000
        listing.floor = 3
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с ценой 40000-60000 USD
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = None
        mock_sub.price_min = 40000
        mock_sub.price_max = 60000
        mock_sub.floor_min = None
        mock_sub.floor_max = None
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 1  # 50000 в диапазоне [40000, 60000]

    async def test_get_matching_subscriptions_price_out_of_range(self, service, db_mock):
        """Тест matching: цена вне диапазона."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_usd = 70000  # Выше максимума
        listing.price = 200000
        listing.floor = 3
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с ценой 40000-60000 USD
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = None
        mock_sub.price_min = 40000
        mock_sub.price_max = 60000
        mock_sub.floor_min = None
        mock_sub.floor_max = None
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 0  # 70000 > 60000

    async def test_get_matching_subscriptions_floor_range(self, service, db_mock):
        """Тест matching: этаж в диапазоне."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_usd = 50000
        listing.price = 150000
        listing.floor = 5
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с floor_min=3, floor_max=7
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = None
        mock_sub.price_min = None
        mock_sub.price_max = None
        mock_sub.floor_min = 3
        mock_sub.floor_max = 7
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 1  # 5 в диапазоне [3, 7]

    async def test_get_matching_subscriptions_floor_out_of_range(self, service, db_mock):
        """Тест matching: этаж вне диапазона."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_usd = 50000
        listing.price = 150000
        listing.floor = 10  # Выше максимума
        listing.price_per_m2_usd = 1000
        listing.price_per_m2_byn = 3000

        # Подписка с floor_min=3, floor_max=7
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = None
        mock_sub.price_min = None
        mock_sub.price_max = None
        mock_sub.floor_min = 3
        mock_sub.floor_max = 7
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 0  # 10 > 7

    async def test_get_matching_subscriptions_price_per_m2(self, service, db_mock):
        """Тест matching: цена за м² в лимите."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_usd = 50000
        listing.price = 150000
        listing.floor = 3
        listing.price_per_m2_usd = 900  # Ниже лимита
        listing.price_per_m2_byn = 2700

        # Подписка с price_per_m2_max=1000
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = None
        mock_sub.price_min = None
        mock_sub.price_max = None
        mock_sub.floor_min = None
        mock_sub.floor_max = None
        mock_sub.price_per_m2_max = 1000
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 1  # 900 <= 1000

    async def test_get_matching_subscriptions_rooms_5_plus(self, service, db_mock):
        """Тест matching: rooms=[5] для 5+ комнат."""
        listing = MagicMock(spec=Listing)
        listing.kufar_id = "123456"
        listing.city = "minsk"
        listing.rooms = 6  # 6 комнат
        listing.price_usd = 80000
        listing.price = 240000
        listing.floor = 5
        listing.price_per_m2_usd = 1200
        listing.price_per_m2_byn = 3600

        # Подписка с rooms=[5] (5+ комнат)
        mock_sub = MagicMock(spec=TelegramSubscription)
        mock_sub.is_active = True
        mock_sub.city = "minsk"
        mock_sub.rooms = [5]
        mock_sub.price_min = None
        mock_sub.price_max = None
        mock_sub.floor_min = None
        mock_sub.floor_max = None
        mock_sub.price_per_m2_max = None
        mock_sub.currency = "usd"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sub]
        db_mock.execute.return_value = mock_result

        matching = await service.get_matching_subscriptions(listing)

        assert len(matching) == 1  # 6 >= 5

    # === Stats ===

    async def test_user_subscription_count(self, service, db_mock):
        """Тест получения количества подписок пользователя."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        db_mock.execute.return_value = mock_result

        count = await service.get_user_subscription_count(user_id)

        assert count == 3

    async def test_user_subscription_count_zero(self, service, db_mock):
        """Тест получения количества подписок (ноль)."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar.return_value = None  # Нет подписок
        db_mock.execute.return_value = mock_result

        count = await service.get_user_subscription_count(user_id)

        assert count == 0

    async def test_total_active_subscriptions(self, service, db_mock):
        """Тест получения общего количества активных подписок."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        db_mock.execute.return_value = mock_result

        count = await service.get_total_active_subscriptions()

        assert count == 42

    async def test_create_subscription_user_not_found(self, service, db_mock):
        """Тест создания подписки для несуществующего пользователя."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        with pytest.raises(UserNotFoundError):
            await service.create_subscription(
                user_id=user_id,
                city="minsk",
            )

    async def test_create_subscription_invalid_floor_range(self, service, db_mock):
        """Тест создания подписки с невалидным диапазоном этажей."""
        user_id = uuid4()

        with pytest.raises(InvalidFloorRangeError):
            await service.create_subscription(
                user_id=user_id,
                city="minsk",
                floor_min=10,
                floor_max=5,  # min > max
            )

    async def test_create_subscription_invalid_currency(self, service, db_mock):
        """Тест создания подписки с невалидной валютой."""
        user_id = uuid4()

        with pytest.raises(InvalidCurrencyError):
            await service.create_subscription(
                user_id=user_id,
                city="minsk",
                currency="eur",  # Недопустимая валюта
            )
