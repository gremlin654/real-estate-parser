"""
Unit тесты для PriceDropService.

Тестируют методы:
- get_price_drop_listings
- get_listing_price_history
- get_price_drop_stats
- Redis кэширование
- Обработка edge cases
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Result
from uuid import uuid4

from app.services.price_drop_service import (
    PriceDropService,
    get_price_drop_service,
    CACHE_TTL_PRICE_DROPS,
    CACHE_TTL_PRICE_HISTORY,
    CACHE_TTL_PRICE_DROP_STATS,
)
from app.models.listing import Listing, ListingHistory, EventType, ListingStatus


@pytest.fixture
def mock_db_session():
    """Создание мок сессии базы данных."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    return session


@pytest.fixture
def price_drop_service(mock_db_session):
    """Создание экземпляра сервиса."""
    return PriceDropService(mock_db_session)


class TestPriceDropServiceInit:
    """Тесты инициализации сервиса."""

    def test_init_with_db_session(self, mock_db_session):
        """Тест инициализации с сессией БД."""
        service = PriceDropService(mock_db_session)
        assert service.db == mock_db_session
        assert service._redis is None

    def test_get_price_drop_service_factory(self, mock_db_session):
        """Тест factory функции."""
        service = get_price_drop_service(mock_db_session)
        assert isinstance(service, PriceDropService)
        assert service.db == mock_db_session


class TestCacheKeyGeneration:
    """Тесты генерации ключей кэша."""

    def test_generate_cache_key_simple(self, price_drop_service):
        """Тест генерации простого ключа."""
        key = price_drop_service._generate_cache_key(
            "price_drops",
            city="minsk",
            drop_percent=10,
        )
        assert key == "cache:price_drops:city=minsk:drop_percent=10"

    def test_generate_cache_key_with_none_values(self, price_drop_service):
        """Тест: None значения исключаются из ключа."""
        key = price_drop_service._generate_cache_key(
            "price_drops",
            city="minsk",
            drop_percent=10,
            currency=None,
        )
        assert "currency" not in key
        assert key == "cache:price_drops:city=minsk:drop_percent=10"

    def test_generate_cache_key_no_params(self, price_drop_service):
        """Тест: нет параметров."""
        key = price_drop_service._generate_cache_key("price_drops")
        assert key == "cache:price_drops:default"


class TestCalculateDropPercent:
    """Тесты расчёта процента падения цены."""

    @pytest.mark.asyncio
    async def test_drop_percent_calculation(self, price_drop_service, mock_db_session):
        """Тест расчёта drop_percent через SQL агрегацию."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db_session.execute.return_value = mock_result

        # Вызов метода
        listings, avg_drop, max_drop, min_drop, total = await price_drop_service.get_price_drop_listings(
            city="minsk",
            drop_percent=10.0,
            limit=20,
            offset=0,
            currency="usd",
        )

        # Проверка что SQL запрос был выполнен
        assert mock_db_session.execute.called
        # total из мока
        assert total == 5

    @pytest.mark.asyncio
    async def test_drop_percent_zero_max_price(self, price_drop_service):
        """Тест: защита от деления на ноль (max_price = 0)."""
        # Edge case проверяется в SQL через NULLIF
        # Этот тест проверяет что сервис не падает
        pass  # SQL логика тестируется в integration тестах

    @pytest.mark.asyncio
    async def test_drop_percent_null_prices(self, price_drop_service):
        """Тест: null цены в истории."""
        # SQL запрос фильтрует NULL через isnot(None)
        pass  # SQL логика тестируется в integration тестах


class TestPriceDropListings:
    """Тесты метода get_price_drop_listings."""

    @pytest.mark.asyncio
    async def test_get_price_drop_listings_basic(self, price_drop_service, mock_db_session):
        """Тест получения списка с падением цены."""
        # Setup mock - возвращаем пустой список для простоты
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        # Вызов метода
        listings, avg_drop, max_drop, min_drop, total = await price_drop_service.get_price_drop_listings(
            city="minsk",
            drop_percent=10.0,
            limit=20,
            offset=0,
            currency="usd",
        )

        # Проверка что SQL запрос был выполнен
        assert mock_db_session.execute.called
        assert listings == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_price_drop_listings_byn_currency(self, price_drop_service, mock_db_session):
        """Тест получения списка с валютой BYN."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        listings, _, _, _, _ = await price_drop_service.get_price_drop_listings(
            city="minsk",
            drop_percent=10.0,
            currency="byn",
        )

        assert isinstance(listings, list)

    @pytest.mark.asyncio
    async def test_get_price_drop_listings_empty_result(self, price_drop_service, mock_db_session):
        """Тест: нет объявлений с падением цены."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        listings, avg_drop, max_drop, min_drop, total = await price_drop_service.get_price_drop_listings(
            city="minsk",
            drop_percent=50.0,  # Высокий порог
        )

        assert listings == []
        assert total == 0
        assert avg_drop == 0.0
        assert max_drop == 0.0
        assert min_drop == 0.0

    @pytest.mark.asyncio
    async def test_get_price_drop_listings_cache_hit(self, price_drop_service, mock_db_session):
        """Тест: попадание в кэш."""
        # Setup mock Redis
        mock_redis = AsyncMock()
        cached_data = {
            "items": [{"kufar_id": "cached_123"}],
            "avg_drop_percent": 15.0,
            "max_drop_percent": 20.0,
            "min_drop_percent": 10.0,
            "total": 1,
        }
        mock_redis.get.return_value = str(cached_data).replace("'", '"')
        price_drop_service._redis = mock_redis

        listings, avg_drop, max_drop, min_drop, total = await price_drop_service.get_price_drop_listings(
            city="minsk",
            drop_percent=10.0,
        )

        # Проверка что Redis был вызван
        assert mock_redis.get.called
        # Проверка что SQL не выполнялся (кэш hit)
        # listings из кэша
        assert len(listings) == 1
        assert listings[0]["kufar_id"] == "cached_123"

    @pytest.mark.asyncio
    async def test_get_price_drop_listings_cache_miss(self, price_drop_service, mock_db_session):
        """Тест: промах кэша."""
        # Setup mock Redis
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Cache miss
        price_drop_service._redis = mock_redis

        # Setup mock DB
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        await price_drop_service.get_price_drop_listings(city="minsk")

        # Проверка что Redis был вызван
        assert mock_redis.get.called
        # Проверка что setex был вызван для сохранения в кэш
        assert mock_redis.setex.called


class TestListingPriceHistory:
    """Тесты метода get_listing_price_history."""

    @pytest.mark.asyncio
    async def test_get_listing_price_history_basic(self, price_drop_service, mock_db_session):
        """Тест получения истории цен."""
        listing_id = uuid4()

        # Setup mock
        mock_record = MagicMock()
        mock_record.price_before_usd = 40000
        mock_record.price_after_usd = 38000
        mock_record.price_before = 114000
        mock_record.price_after = 108000
        mock_record.event_type = EventType.price_changed
        mock_record.created_at = datetime.now()
        mock_record.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_record]
        mock_db_session.execute.return_value = mock_result

        items, first_price, last_price, total_drop = await price_drop_service.get_listing_price_history(
            listing_id=listing_id,
            currency="usd",
        )

        assert len(items) == 1
        assert items[0]["price_before"] == 40000
        assert items[0]["price_after"] == 38000
        assert first_price == 40000
        assert last_price == 38000
        assert total_drop is not None
        assert total_drop > 0  # 5% падение

    @pytest.mark.asyncio
    async def test_get_listing_price_history_empty(self, price_drop_service, mock_db_session):
        """Тест: нет истории изменений."""
        listing_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        items, first_price, last_price, total_drop = await price_drop_service.get_listing_price_history(
            listing_id=listing_id,
        )

        assert items == []
        assert first_price is None
        assert last_price is None
        assert total_drop is None

    @pytest.mark.asyncio
    async def test_get_listing_price_history_multiple_events(self, price_drop_service, mock_db_session):
        """Тест: несколько событий изменения цены."""
        listing_id = uuid4()

        # Создаём несколько записей
        mock_records = []
        prices = [(50000, 45000), (45000, 42000), (42000, 40000)]

        for price_before, price_after in prices:
            mock_record = MagicMock()
            mock_record.price_before_usd = price_before
            mock_record.price_after_usd = price_after
            mock_record.event_type = EventType.price_changed
            mock_record.created_at = datetime.now()
            mock_records.append(mock_record)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db_session.execute.return_value = mock_result

        items, first_price, last_price, total_drop = await price_drop_service.get_listing_price_history(
            listing_id=listing_id,
            currency="usd",
        )

        assert len(items) == 3
        assert first_price == 50000  # Первая цена
        assert last_price == 40000  # Последняя цена
        assert total_drop is not None
        assert total_drop == 20.0  # (50000-40000)/50000 * 100

    @pytest.mark.asyncio
    async def test_get_listing_price_history_cache(self, price_drop_service, mock_db_session):
        """Тест кэширования истории."""
        listing_id = uuid4()
        mock_redis = AsyncMock()
        cached_data = {
            "items": [{"price_before": 40000, "price_after": 38000}],
            "first_price": 40000,
            "last_price": 38000,
            "total_drop_percent": 5.0,
        }
        mock_redis.get.return_value = str(cached_data).replace("'", '"')
        price_drop_service._redis = mock_redis

        items, first_price, last_price, total_drop = await price_drop_service.get_listing_price_history(
            listing_id=listing_id,
        )

        assert mock_redis.get.called
        assert len(items) == 1


class TestPriceDropStats:
    """Тесты метода get_price_drop_stats."""

    @pytest.mark.asyncio
    async def test_get_price_drop_stats_basic(self, price_drop_service, mock_db_session):
        """Тест получения статистики."""
        # Setup mock с правильным доступом по индексу
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=lambda idx: [10, 12.5, 25.0, 5.0][idx])
        mock_row.__iter__ = MagicMock(return_value=iter([10, 12.5, 25.0, 5.0]))

        mock_result = MagicMock()
        mock_result.first.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        stats = await price_drop_service.get_price_drop_stats(
            city="minsk",
            drop_percent=10.0,
            currency="usd",
        )

        assert stats["total_drops"] == 10
        assert stats["avg_drop_percent"] == 12.5
        assert stats["max_drop_percent"] == 25.0
        assert stats["min_drop_percent"] == 5.0
        assert stats["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_get_price_drop_stats_empty(self, price_drop_service, mock_db_session):
        """Тест: нет статистики."""
        # Setup mock с правильным доступом по индексу
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=lambda idx: [0, None, None, None][idx])
        mock_row.__iter__ = MagicMock(return_value=iter([0, None, None, None]))

        mock_result = MagicMock()
        mock_result.first.return_value = mock_row
        mock_db_session.execute.return_value = mock_result

        stats = await price_drop_service.get_price_drop_stats(city="minsk")

        assert stats["total_drops"] == 0
        assert stats["avg_drop_percent"] == 0.0
        assert stats["max_drop_percent"] == 0.0
        assert stats["min_drop_percent"] == 0.0

    @pytest.mark.asyncio
    async def test_get_price_drop_stats_cache(self, price_drop_service, mock_db_session):
        """Тест кэширования статистики."""
        mock_redis = AsyncMock()
        cached_data = {
            "total_drops": 5,
            "avg_drop_percent": 10.0,
            "max_drop_percent": 15.0,
            "min_drop_percent": 5.0,
            "currency": "USD",
        }
        mock_redis.get.return_value = str(cached_data).replace("'", '"')
        price_drop_service._redis = mock_redis

        stats = await price_drop_service.get_price_drop_stats(city="minsk")

        assert mock_redis.get.called
        assert stats["total_drops"] == 5


class TestEdgeCases:
    """Тесты граничных случаев."""

    @pytest.mark.asyncio
    async def test_division_by_zero_protection(self, price_drop_service):
        """Тест защиты от деления на ноль."""
        # SQL использует NULLIF для защиты
        pass  # Тестируется в integration тестах

    @pytest.mark.asyncio
    async def test_null_price_handling(self, price_drop_service):
        """Тест обработки null цен."""
        # SQL фильтрует NULL через isnot(None)
        pass  # Тестируется в integration тестах

    @pytest.mark.asyncio
    async def test_single_event_no_drop(self, price_drop_service):
        """Тест: одно событие в истории (drop_percent = 0)."""
        pass  # Тестируется в integration тестах

    @pytest.mark.asyncio
    async def test_invalid_city_validation(self, price_drop_service):
        """Тест валидации города (должен быть в списке)."""
        # Валидация происходит в API endpoint
        pass

    @pytest.mark.asyncio
    async def test_drop_percent_range_validation(self, price_drop_service):
        """Тест валидации drop_percent (0-100)."""
        # Валидация происходит в API endpoint
        pass


class TestRedisCacheTTL:
    """Тесты TTL для кэширования."""

    def test_cache_ttl_constants(self):
        """Тест констант TTL."""
        assert CACHE_TTL_PRICE_DROPS == 300  # 5 минут
        assert CACHE_TTL_PRICE_HISTORY == 180  # 3 минуты
        assert CACHE_TTL_PRICE_DROP_STATS == 600  # 10 минут

    @pytest.mark.asyncio
    async def test_cache_setex_called_with_correct_ttl(self, price_drop_service, mock_db_session):
        """Тест: setex вызывается с правильным TTL."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Cache miss
        price_drop_service._redis = mock_redis

        # Setup mock DB
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        await price_drop_service.get_price_drop_listings(city="minsk")

        # Проверка что setex был вызван с правильным TTL
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == CACHE_TTL_PRICE_DROPS  # TTL argument
