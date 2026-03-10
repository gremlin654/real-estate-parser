"""
Тесты для функциональности price_per_m2
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from app.services.listing_service import ListingService
from app.models.listing import Listing, ListingStatus


@pytest.mark.asyncio
class TestPricePerM2Calculation:
    """Тесты для расчёта цены за м²."""

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
    def listing_service(self, db_mock):
        """Создание сервиса listings."""
        return ListingService(db_mock)

    async def test_price_per_m2_calculation_new_listing(self, listing_service, db_mock):
        """Проверка расчёта цены за м² для нового объявления."""
        # Мокаем отсутствие существующего объявления
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        listing_data = {
            "kufar_id": "123456",
            "url": "https://re.kufar.by/vi/minsk/kupit/kvartiru/123456",
            "title": "Test listing",
            "price": 150000,  # 150,000 BYN
            "price_usd": 45000,  # $45,000
            "area": 50.0,  # 50 м²
            "city": "minsk",
            "rooms": 2,
        }

        listing, action = await listing_service.upsert(listing_data)

        # Проверяем что цена за м² рассчитана
        assert listing_data["price_per_m2_byn"] == 3000.0  # 150000 / 50
        assert listing_data["price_per_m2_usd"] == 900.0  # 45000 / 50
        assert action == "created"

    async def test_price_per_m2_area_zero(self, listing_service, db_mock):
        """Проверка что при area=0 цена за м² не рассчитывается."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        listing_data = {
            "kufar_id": "123457",
            "url": "https://re.kufar.by/vi/minsk/kupit/kvartiru/123457",
            "title": "Test listing no area",
            "price": 100000,
            "price_usd": 30000,
            "area": 0,  # Площадь не указана
            "city": "minsk",
        }

        listing, action = await listing_service.upsert(listing_data)

        # Проверяем что цена за м² None
        assert listing_data["price_per_m2_byn"] is None
        assert listing_data["price_per_m2_usd"] is None

    async def test_price_per_m2_area_none(self, listing_service, db_mock):
        """Проверка что при area=None цена за м² не рассчитывается."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        listing_data = {
            "kufar_id": "123458",
            "url": "https://re.kufar.by/vi/minsk/kupit/kvartiru/123458",
            "title": "Test listing no area",
            "price": 100000,
            "price_usd": 30000,
            "area": None,  # Площадь не указана
            "city": "minsk",
        }

        listing, action = await listing_service.upsert(listing_data)

        assert listing_data["price_per_m2_byn"] is None
        assert listing_data["price_per_m2_usd"] is None

    async def test_price_per_m2_update_existing(self, listing_service, db_mock):
        """Проверка пересчёта цены за м² при обновлении объявления."""
        # Создаём мок существующего объявления
        existing_listing = MagicMock(spec=Listing)
        existing_listing.id = "uuid-123"
        existing_listing.kufar_id = "123456"
        existing_listing.price_usd = 45000
        existing_listing.price = 150000
        existing_listing.status = ListingStatus.active
        existing_listing.price_per_m2_byn = Decimal("3000.00")
        existing_listing.price_per_m2_usd = Decimal("900.00")

        # Мокаем получение существующего объявления
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [existing_listing, None]
        db_mock.execute.return_value = mock_result

        listing_data = {
            "kufar_id": "123456",
            "url": "https://re.kufar.by/vi/minsk/kupit/kvartiru/123456",
            "title": "Updated listing",
            "price": 160000,  # Новая цена 160,000 BYN
            "price_usd": 48000,  # Новая цена $48,000
            "area": 50.0,
            "city": "minsk",
        }

        listing, action = await listing_service.upsert(listing_data)

        # Проверяем что цена за м² пересчитана
        assert listing_data["price_per_m2_byn"] == 3200.0  # 160000 / 50
        assert listing_data["price_per_m2_usd"] == 960.0  # 48000 / 50

    async def test_price_per_m2_rounding(self, listing_service, db_mock):
        """Проверка округления цены за м² до 2 знаков."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        listing_data = {
            "kufar_id": "123459",
            "url": "https://re.kufar.by/vi/minsk/kupit/kvartiru/123459",
            "title": "Test rounding",
            "price": 100000,
            "price_usd": 30000,
            "area": 33.33,  # Некруглая площадь
            "city": "minsk",
        }

        listing, action = await listing_service.upsert(listing_data)

        # Проверяем округление
        assert listing_data["price_per_m2_byn"] == 3000.3  # 100000 / 33.33 ≈ 3000.30
        assert listing_data["price_per_m2_usd"] == 900.09  # 30000 / 33.33 ≈ 900.09


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires test database")
class TestPricePerM2Endpoints:
    """Интеграционные тесты для API endpoints price_per_m2."""

    async def test_price_per_m2_stats_endpoint(self, client, test_db):
        """Тест endpoint статистики цены за м²."""
        # Создаём тестовые данные
        from app.models.listing import Listing
        from uuid import uuid4
        
        test_listing = Listing(
            id=uuid4(),
            kufar_id="test_123",
            url="https://re.kufar.by/test",
            title="Test",
            price=150000,
            price_usd=45000,
            area=50.0,
            price_per_m2_byn=3000.0,
            price_per_m2_usd=900.0,
            city="minsk",
            status=ListingStatus.active,
        )
        test_db.add(test_listing)
        await test_db.commit()

        response = await client.get(
            "/api/v1/stats/price-per-m2?city=minsk&currency=usd"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "average" in data
        assert "median" in data
        assert "min" in data
        assert "max" in data
        assert "count" in data
        assert data["currency"] == "usd"

    async def test_price_per_m2_trends_endpoint(self, client, test_db):
        """Тест endpoint трендов цены за м²."""
        response = await client.get(
            "/api/v1/stats/price-per-m2-trends?city=minsk&period_days=30&interval=day"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "date" in data[0]
            assert "average" in data[0]
            assert "median" in data[0]
            assert "count" in data[0]

    async def test_price_per_m2_distribution_endpoint(self, client, test_db):
        """Тест endpoint распределения цены за м²."""
        response = await client.get(
            "/api/v1/stats/price-per-m2-distribution?city=minsk&bins=10"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "range_min" in data[0]
            assert "range_max" in data[0]
            assert "count" in data[0]
            assert "percentage" in data[0]

    async def test_listings_price_per_m2_filter(self, client, test_db):
        """Тест фильтрации listings по цене за м²."""
        # Создаём тестовые данные
        from app.models.listing import Listing
        from uuid import uuid4
        
        listings = [
            Listing(
                id=uuid4(),
                kufar_id=f"test_{i}",
                url="https://re.kufar.by/test",
                title="Test",
                price=150000,
                price_usd=45000,
                area=50.0,
                price_per_m2_usd=900.0,
                city="minsk",
                status=ListingStatus.active,
            )
            for i in range(5)
        ]
        
        test_db.add_all(listings)
        await test_db.commit()

        # Тест фильтрации по минимальной цене за м²
        response = await client.get(
            "/api/v1/listings?city=minsk&price_per_m2_min=800&price_per_m2_max=1000"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Все объявления должны попасть в фильтр
