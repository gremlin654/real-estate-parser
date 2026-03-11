"""
Unit тесты для DealFinderService.

Тестируют методы:
- get_avg_price_per_m2
- calculate_deal_percent
- get_deal_listings
- get_listing_deal_metrics
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Result

from app.services.deal_finder_service import DealFinderService, VALID_CITIES
from app.models.listing import Listing, ListingStatus


@pytest.fixture
def mock_db_session():
    """Создание мок сессии базы данных."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    return session


@pytest.fixture
def deal_finder_service(mock_db_session):
    """Создание экземпляра сервиса."""
    return DealFinderService(mock_db_session)


class TestDealFinderServiceInit:
    """Тесты инициализации сервиса."""
    
    def test_init_with_db_session(self, mock_db_session):
        """Тест инициализации с сессией БД."""
        service = DealFinderService(mock_db_session)
        assert service.db == mock_db_session
        assert service._redis is None


class TestCalculateDealPercent:
    """Тесты метода calculate_deal_percent."""
    
    def test_calculate_deal_percent_below_market(self, deal_finder_service):
        """Тест: цена ниже средней (выгодное предложение)."""
        current_price = 800
        avg_price = 1000
        
        result = deal_finder_service.calculate_deal_percent(current_price, avg_price)
        
        assert result == -20.0  # На 20% ниже рынка
    
    def test_calculate_deal_percent_above_market(self, deal_finder_service):
        """Тест: цена выше средней."""
        current_price = 1200
        avg_price = 1000
        
        result = deal_finder_service.calculate_deal_percent(current_price, avg_price)
        
        assert result == 20.0  # На 20% выше рынка
    
    def test_calculate_deal_percent_equal_to_market(self, deal_finder_service):
        """Тест: цена равна средней."""
        current_price = 1000
        avg_price = 1000
        
        result = deal_finder_service.calculate_deal_percent(current_price, avg_price)
        
        assert result == 0.0
    
    def test_calculate_deal_percent_zero_avg_price(self, deal_finder_service):
        """Тест: средняя цена равна нулю (защита от деления на ноль)."""
        current_price = 800
        avg_price = 0
        
        result = deal_finder_service.calculate_deal_percent(current_price, avg_price)
        
        assert result == 0.0
    
    def test_calculate_deal_percent_rounding(self, deal_finder_service):
        """Тест: округление до 2 знаков."""
        current_price = 987.654
        avg_price = 1000
        
        result = deal_finder_service.calculate_deal_percent(current_price, avg_price)
        
        assert result == -1.23  # Округлено до 2 знаков
    
    def test_calculate_deal_percent_negative_prices(self, deal_finder_service):
        """Тест: отрицательные цены (корректная обработка)."""
        current_price = -800
        avg_price = -1000
        
        result = deal_finder_service.calculate_deal_percent(current_price, avg_price)
        
        assert result == -20.0


class TestGetAvgPricePerM2:
    """Тесты метода get_avg_price_per_m2."""
    
    @pytest.mark.asyncio
    async def test_get_avg_price_usd_no_rooms(self, deal_finder_service, mock_db_session):
        """Тест: средняя цена в USD без фильтра по комнатам."""
        # Мокаем результат SQL запроса
        mock_result = MagicMock(spec=Result)
        mock_result.scalar.return_value = Decimal("1250.50")
        mock_db_session.execute.return_value = mock_result
        
        result = await deal_finder_service.get_avg_price_per_m2(
            city="minsk",
            rooms=None,
            currency="usd"
        )
        
        assert result == 1250.50
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_avg_price_byn_with_rooms(self, deal_finder_service, mock_db_session):
        """Тест: средняя цена в BYN с фильтром по комнатам."""
        mock_result = MagicMock(spec=Result)
        mock_result.scalar.return_value = Decimal("3500.75")
        mock_db_session.execute.return_value = mock_result
        
        result = await deal_finder_service.get_avg_price_per_m2(
            city="minsk",
            rooms=2,
            currency="byn"
        )
        
        assert result == 3500.75
    
    @pytest.mark.asyncio
    async def test_get_avg_price_no_data(self, deal_finder_service, mock_db_session):
        """Тест: нет данных для расчёта."""
        mock_result = MagicMock(spec=Result)
        mock_result.scalar.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await deal_finder_service.get_avg_price_per_m2(
            city="minsk",
            rooms=5,
            currency="usd"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_avg_price_invalid_city(self, deal_finder_service):
        """Тест: некорректный город."""
        with pytest.raises(ValueError, match="Некорректный город"):
            await deal_finder_service.get_avg_price_per_m2(
                city="invalid_city",
                rooms=None,
                currency="usd"
            )
    
    @pytest.mark.asyncio
    async def test_get_avg_price_invalid_rooms(self, deal_finder_service):
        """Тест: некорректное количество комнат."""
        with pytest.raises(ValueError, match="Количество комнат должно быть от 1 до 10"):
            await deal_finder_service.get_avg_price_per_m2(
                city="minsk",
                rooms=15,
                currency="usd"
            )
    
    @pytest.mark.asyncio
    async def test_get_avg_price_invalid_currency(self, deal_finder_service):
        """Тест: некорректная валюта."""
        with pytest.raises(ValueError, match="Некорректная валюта"):
            await deal_finder_service.get_avg_price_per_m2(
                city="minsk",
                rooms=None,
                currency="eur"
            )
    
    @pytest.mark.asyncio
    async def test_get_avg_price_city_lowercase(self, deal_finder_service, mock_db_session):
        """Тест: город приводится к нижнему регистру."""
        mock_result = MagicMock(spec=Result)
        mock_result.scalar.return_value = Decimal("1000")
        mock_db_session.execute.return_value = mock_result
        
        result = await deal_finder_service.get_avg_price_per_m2(
            city="MINSK",
            rooms=None,
            currency="usd"
        )
        
        assert result == 1000.0
    
    @pytest.mark.asyncio
    async def test_get_avg_price_all_valid_cities(self, deal_finder_service, mock_db_session):
        """Тест: все валидные города."""
        mock_result = MagicMock(spec=Result)
        mock_result.scalar.return_value = Decimal("1000")
        mock_db_session.execute.return_value = mock_result
        
        for city in VALID_CITIES:
            result = await deal_finder_service.get_avg_price_per_m2(
                city=city,
                rooms=None,
                currency="usd"
            )
            assert result == 1000.0


class TestGetDealListings:
    """Тесты метода get_deal_listings."""
    
    @pytest.mark.asyncio
    async def test_get_deal_listings_basic(self, deal_finder_service, mock_db_session):
        """Тест: базовый поиск выгодных предложений."""
        # Мокаем среднюю цену
        mock_result_avg = MagicMock(spec=Result)
        mock_result_avg.scalar.return_value = Decimal("1000")
        
        # Мокаем количество
        mock_result_count = MagicMock(spec=Result)
        mock_result_count.scalar.return_value = 5
        
        # Мокаем список объявлений
        mock_listing = MagicMock(spec=Listing)
        mock_listing.price_per_m2_usd = Decimal("850")
        mock_listing.city = "minsk"
        mock_listing.rooms = 2
        
        mock_result_listings = MagicMock(spec=Result)
        mock_result_listings.scalars.return_value.all.return_value = [mock_listing]
        
        # Настраиваем последовательные вызовы
        mock_db_session.execute.side_effect = [
            mock_result_avg,      # get_avg_price_per_m2
            mock_result_count,    # count query
            mock_result_listings  # listings query
        ]
        
        listings, avg_price, total = await deal_finder_service.get_deal_listings(
            city="minsk",
            rooms=2,
            discount_percent=10,
            currency="usd",
            limit=20,
            offset=0
        )
        
        assert avg_price == 1000.0
        assert total == 5
        assert len(listings) == 1
    
    @pytest.mark.asyncio
    async def test_get_deal_listings_no_data(self, deal_finder_service, mock_db_session):
        """Тест: нет данных для расчёта средней цены."""
        # Мокаем метод get_avg_price_per_m2 для возврата None
        with patch.object(deal_finder_service, 'get_avg_price_per_m2', new_callable=AsyncMock) as mock_get_avg:
            mock_get_avg.return_value = None
            
            listings, avg_price, total = await deal_finder_service.get_deal_listings(
                city="minsk",
                rooms=2,
                discount_percent=10,
                currency="usd"
            )
            
            assert listings == []
            assert avg_price == 0.0
            assert total == 0
            mock_get_avg.assert_called_once_with(city="minsk", rooms=2, currency="usd")
    
    @pytest.mark.asyncio
    async def test_get_deal_listings_invalid_discount(self, deal_finder_service):
        """Тест: некорректный discount_percent."""
        with pytest.raises(ValueError, match="discount_percent должен быть от 0 до 50"):
            await deal_finder_service.get_deal_listings(
                city="minsk",
                discount_percent=60
            )
    
    @pytest.mark.asyncio
    async def test_get_deal_listings_invalid_limit(self, deal_finder_service):
        """Тест: некорректный limit."""
        with pytest.raises(ValueError, match="limit должен быть от 1 до 100"):
            await deal_finder_service.get_deal_listings(
                city="minsk",
                limit=150
            )
    
    @pytest.mark.asyncio
    async def test_get_deal_listings_invalid_offset(self, deal_finder_service):
        """Тест: некорректный offset."""
        with pytest.raises(ValueError, match="offset должен быть >= 0"):
            await deal_finder_service.get_deal_listings(
                city="minsk",
                offset=-5
            )


class TestGetListingDealMetrics:
    """Тесты метода get_listing_deal_metrics."""
    
    @pytest.mark.asyncio
    async def test_get_listing_deal_metrics_basic(self, deal_finder_service, mock_db_session):
        """Тест: базовый расчёт метрик."""
        # Создаём тестовое объявление
        listing = MagicMock(spec=Listing)
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_per_m2_usd = Decimal("850")
        
        # Мокаем среднюю цену
        mock_result = MagicMock(spec=Result)
        mock_result.scalar.return_value = Decimal("1000")
        mock_db_session.execute.return_value = mock_result
        
        deal_percent, avg_price = await deal_finder_service.get_listing_deal_metrics(
            listing=listing,
            currency="usd"
        )
        
        assert avg_price == 1000.0
        assert deal_percent == -15.0  # (850-1000)/1000 * 100
    
    @pytest.mark.asyncio
    async def test_get_listing_deal_metrics_no_city(self, deal_finder_service):
        """Тест: нет города у объявления."""
        listing = MagicMock(spec=Listing)
        listing.city = None
        
        deal_percent, avg_price = await deal_finder_service.get_listing_deal_metrics(
            listing=listing
        )
        
        assert deal_percent is None
        assert avg_price is None
    
    @pytest.mark.asyncio
    async def test_get_listing_deal_metrics_no_price_per_m2(self, deal_finder_service):
        """Тест: нет цены за м² у объявления."""
        listing = MagicMock(spec=Listing)
        listing.city = "minsk"
        listing.rooms = 2
        listing.price_per_m2_usd = None
        
        deal_percent, avg_price = await deal_finder_service.get_listing_deal_metrics(
            listing=listing
        )
        
        assert deal_percent is None
        assert avg_price is None


class TestRedisCaching:
    """Тесты Redis кэширования."""
    
    @pytest.mark.asyncio
    async def test_get_avg_price_cache_hit(self, deal_finder_service, mock_db_session):
        """Тест: попадание в кэш."""
        with patch.object(deal_finder_service, '_get_redis', return_value=AsyncMock()) as mock_redis_get:
            mock_redis = await mock_redis_get()
            
            # Мокаем функции кэша
            with patch('app.services.deal_finder_service._get_from_cache', return_value=1200.50) as mock_get:
                result = await deal_finder_service.get_avg_price_per_m2(
                    city="minsk",
                    rooms=2,
                    currency="usd"
                )
                
                assert result == 1200.50
                mock_get.assert_called_once()
                # SQL запрос не должен был выполниться
                mock_db_session.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_avg_price_cache_miss(self, deal_finder_service, mock_db_session):
        """Тест: промах кэша."""
        with patch.object(deal_finder_service, '_get_redis', return_value=AsyncMock()) as mock_redis_get:
            mock_redis = await mock_redis_get()
            
            # Мокаем функции кэша
            with patch('app.services.deal_finder_service._get_from_cache', return_value=None) as mock_get:
                with patch('app.services.deal_finder_service._set_to_cache', return_value=True) as mock_set:
                    # Мокаем результат БД
                    mock_result = MagicMock(spec=Result)
                    mock_result.scalar.return_value = Decimal("1100")
                    mock_db_session.execute.return_value = mock_result
                    
                    result = await deal_finder_service.get_avg_price_per_m2(
                        city="minsk",
                        rooms=2,
                        currency="usd"
                    )
                    
                    assert result == 1100.0
                    mock_get.assert_called_once()
                    mock_set.assert_called_once()


class TestEdgeCases:
    """Тесты граничных случаев."""
    
    def test_calculate_deal_percent_very_large_discount(self, deal_finder_service):
        """Тест: очень большой дисконт."""
        current_price = 100
        avg_price = 1000
        
        result = deal_finder_service.calculate_deal_percent(current_price, avg_price)
        
        assert result == -90.0
    
    def test_calculate_deal_percent_very_small_discount(self, deal_finder_service):
        """Тест: очень маленький дисконт."""
        current_price = 999
        avg_price = 1000
        
        result = deal_finder_service.calculate_deal_percent(current_price, avg_price)
        
        assert result == -0.1
    
    @pytest.mark.asyncio
    async def test_get_avg_price_zero_result(self, deal_finder_service, mock_db_session):
        """Тест: результат 0 от БД."""
        mock_result = MagicMock(spec=Result)
        mock_result.scalar.return_value = Decimal("0")
        mock_db_session.execute.return_value = mock_result
        
        result = await deal_finder_service.get_avg_price_per_m2(
            city="minsk",
            rooms=None,
            currency="usd"
        )
        
        assert result == 0.0
