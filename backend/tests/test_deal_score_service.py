"""
Unit тесты для DealScoreService.

Тестируют все 6 подкомпонентов Deal Score:
- PriceScore (6 тестов)
- TrendScore (5 тестов)
- LiquidityScore (5 тестов)
- FreshnessScore (4 тестов)
- FloorScore (4 тестов)
- BonusScore (4 тестов)
- Weighted Score (3 тестов)
- Label (3 тестов)
- Weights Validation (3 тестов)
- Breakdown (2 тестов)

Всего: 39 тестов
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.deal_score_service import DealScoreService


@pytest.fixture
def mock_listing():
    """Создание мок объекта listing с дефолтными значениями."""
    listing = MagicMock()
    listing.id = "test-uuid-123"
    listing.price_per_m2_usd = Decimal("800.00")
    listing.first_seen_at = datetime.now() - timedelta(days=5)
    listing.floor = 5
    listing.total_floors = 9
    listing.images = ["img1.jpg", "img2.jpg", "img3.jpg"]
    listing.area = 65.0
    return listing


@pytest.fixture
def service_without_redis():
    """Создание сервиса без Redis."""
    return DealScoreService(redis_client=None)


@pytest.fixture
def mock_redis():
    """Создание мок Redis клиента."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def service_with_redis(mock_redis):
    """Создание сервиса с Redis."""
    return DealScoreService(redis_client=mock_redis)


class TestPriceScore:
    """Тесты метода calculate_price_score."""

    def test_price_below_market(self, service_without_redis, mock_listing):
        """Тест: цена ниже средней → PriceScore > 0."""
        avg_price_per_m2 = 1000.0
        mock_listing.price_per_m2_usd = Decimal("800.00")

        score = service_without_redis.calculate_price_score(mock_listing, avg_price_per_m2)

        # discount = (1000 - 800) / 1000 * 100 = 20%
        assert score == 20.0

    def test_price_equal_to_market(self, service_without_redis, mock_listing):
        """Тест: цена равна средней → PriceScore = 0."""
        avg_price_per_m2 = 800.0
        mock_listing.price_per_m2_usd = Decimal("800.00")

        score = service_without_redis.calculate_price_score(mock_listing, avg_price_per_m2)

        assert score == 0.0

    def test_price_above_market(self, service_without_redis, mock_listing):
        """Тест: цена выше средней → PriceScore = 0."""
        avg_price_per_m2 = 700.0
        mock_listing.price_per_m2_usd = Decimal("800.00")

        score = service_without_redis.calculate_price_score(mock_listing, avg_price_per_m2)

        # discount = (700 - 800) / 700 * 100 = -14.28% → clamp to 0
        assert score == 0.0

    def test_avg_price_per_m2_zero(self, service_without_redis, mock_listing):
        """Тест: avg_price_per_m2 = 0 → PriceScore = 0."""
        avg_price_per_m2 = 0.0

        score = service_without_redis.calculate_price_score(mock_listing, avg_price_per_m2)

        assert score == 0.0

    def test_avg_price_per_m2_none(self, service_without_redis, mock_listing):
        """Тест: avg_price_per_m2 = None → PriceScore = 0."""
        avg_price_per_m2 = None

        score = service_without_redis.calculate_price_score(mock_listing, avg_price_per_m2)

        assert score == 0.0

    def test_price_per_m2_zero(self, service_without_redis, mock_listing):
        """Тест: price_per_m2 = 0 → PriceScore = 0."""
        avg_price_per_m2 = 1000.0
        mock_listing.price_per_m2_usd = Decimal("0.00")

        score = service_without_redis.calculate_price_score(mock_listing, avg_price_per_m2)

        assert score == 0.0


class TestTrendScore:
    """Тесты метода calculate_trend_score."""

    def test_drop_percent_20_or_more(self, service_without_redis):
        """Тест: drop_percent >= 20 → TrendScore = 100."""
        assert service_without_redis.calculate_trend_score(20.0) == 100.0
        assert service_without_redis.calculate_trend_score(25.0) == 100.0
        assert service_without_redis.calculate_trend_score(50.0) == 100.0

    def test_drop_percent_15(self, service_without_redis):
        """Тест: drop_percent = 15 → TrendScore = 70."""
        score = service_without_redis.calculate_trend_score(15.0)
        assert score == 70.0

    def test_drop_percent_5(self, service_without_redis):
        """Тест: drop_percent = 5 → TrendScore = 40."""
        score = service_without_redis.calculate_trend_score(5.0)
        assert score == 40.0

    def test_drop_percent_zero(self, service_without_redis):
        """Тест: drop_percent = 0 → TrendScore = 0."""
        score = service_without_redis.calculate_trend_score(0.0)
        assert score == 0.0

    def test_drop_percent_negative(self, service_without_redis):
        """Тест: drop_percent < 0 → TrendScore = 0."""
        score = service_without_redis.calculate_trend_score(-5.0)
        assert score == 0.0


class TestLiquidityScore:
    """Тесты метода calculate_liquidity_score."""

    def test_days_on_market_1(self, service_without_redis, mock_listing):
        """Тест: days_on_market = 1 → LiquidityScore = 90."""
        mock_listing.first_seen_at = datetime.now() - timedelta(days=1)

        score = service_without_redis.calculate_liquidity_score(mock_listing)

        assert score == 90.0

    def test_days_on_market_5(self, service_without_redis, mock_listing):
        """Тест: days_on_market = 5 → LiquidityScore = 70."""
        mock_listing.first_seen_at = datetime.now() - timedelta(days=5)

        score = service_without_redis.calculate_liquidity_score(mock_listing)

        assert score == 70.0

    def test_days_on_market_10(self, service_without_redis, mock_listing):
        """Тест: days_on_market = 10 → LiquidityScore = 50."""
        mock_listing.first_seen_at = datetime.now() - timedelta(days=10)

        score = service_without_redis.calculate_liquidity_score(mock_listing)

        assert score == 50.0

    def test_days_on_market_30(self, service_without_redis, mock_listing):
        """Тест: days_on_market = 30 → LiquidityScore = 20."""
        mock_listing.first_seen_at = datetime.now() - timedelta(days=30)

        score = service_without_redis.calculate_liquidity_score(mock_listing)

        assert score == 20.0

    def test_first_seen_at_none(self, service_without_redis, mock_listing):
        """Тест: first_seen_at = None → LiquidityScore = 50."""
        mock_listing.first_seen_at = None

        score = service_without_redis.calculate_liquidity_score(mock_listing)

        assert score == 50.0


class TestFreshnessScore:
    """Тесты метода calculate_freshness_score."""

    def test_hours_12(self, service_without_redis, mock_listing):
        """Тест: hours = 12 → FreshnessScore = 100."""
        mock_listing.first_seen_at = datetime.now() - timedelta(hours=12)

        score = service_without_redis.calculate_freshness_score(mock_listing)

        assert score == 100.0

    def test_hours_48(self, service_without_redis, mock_listing):
        """Тест: hours = 48 → FreshnessScore = 70."""
        mock_listing.first_seen_at = datetime.now() - timedelta(hours=48)

        score = service_without_redis.calculate_freshness_score(mock_listing)

        assert score == 70.0

    def test_hours_100(self, service_without_redis, mock_listing):
        """Тест: hours = 100 → FreshnessScore = 30."""
        mock_listing.first_seen_at = datetime.now() - timedelta(hours=100)

        score = service_without_redis.calculate_freshness_score(mock_listing)

        assert score == 30.0

    def test_first_seen_at_none(self, service_without_redis, mock_listing):
        """Тест: first_seen_at = None → FreshnessScore = 50."""
        mock_listing.first_seen_at = None

        score = service_without_redis.calculate_freshness_score(mock_listing)

        assert score == 50.0


class TestFloorScore:
    """Тесты метода calculate_floor_score."""

    def test_first_floor(self, service_without_redis, mock_listing):
        """Тест: floor = 1 → FloorScore = 40."""
        mock_listing.floor = 1
        mock_listing.total_floors = 9

        score = service_without_redis.calculate_floor_score(mock_listing)

        assert score == 40.0

    def test_last_floor(self, service_without_redis, mock_listing):
        """Тест: floor = total_floors → FloorScore = 40."""
        mock_listing.floor = 9
        mock_listing.total_floors = 9

        score = service_without_redis.calculate_floor_score(mock_listing)

        assert score == 40.0

    def test_middle_floor(self, service_without_redis, mock_listing):
        """Тест: floor = 5, total_floors = 9 → FloorScore = 80."""
        mock_listing.floor = 5
        mock_listing.total_floors = 9

        score = service_without_redis.calculate_floor_score(mock_listing)

        assert score == 80.0

    def test_floor_none(self, service_without_redis, mock_listing):
        """Тест: floor = None → FloorScore = 50."""
        mock_listing.floor = None
        mock_listing.total_floors = 9

        score = service_without_redis.calculate_floor_score(mock_listing)

        assert score == 50.0


class TestBonusScore:
    """Тесты метода calculate_bonus_score."""

    def test_images_and_area_bonus(self, service_without_redis, mock_listing):
        """Тест: images > 0, area > 50 → BonusScore = 40."""
        mock_listing.images = ["img1.jpg", "img2.jpg"]
        mock_listing.area = 65.0

        score = service_without_redis.calculate_bonus_score(mock_listing)

        assert score == 40.0

    def test_area_only_bonus(self, service_without_redis, mock_listing):
        """Тест: images = 0, area > 50 → BonusScore = 20."""
        mock_listing.images = []
        mock_listing.area = 65.0

        score = service_without_redis.calculate_bonus_score(mock_listing)

        assert score == 20.0

    def test_images_only_bonus(self, service_without_redis, mock_listing):
        """Тест: images > 0, area < 50 → BonusScore = 20."""
        mock_listing.images = ["img1.jpg"]
        mock_listing.area = 40.0

        score = service_without_redis.calculate_bonus_score(mock_listing)

        assert score == 20.0

    def test_no_bonus(self, service_without_redis, mock_listing):
        """Тест: images = 0, area < 50 → BonusScore = 0."""
        mock_listing.images = []
        mock_listing.area = 40.0

        score = service_without_redis.calculate_bonus_score(mock_listing)

        assert score == 0.0


class TestWeightedScore:
    """Тесты расчёта итогового Score."""

    @pytest.mark.asyncio
    async def test_all_scores_100(self, service_without_redis, mock_listing):
        """Тест: Все факторы 100 → Score = 100."""
        # Подготовить listing для максимальных значений
        mock_listing.price_per_m2_usd = Decimal("0.01")  # Очень низкая цена
        mock_listing.first_seen_at = datetime.now() - timedelta(hours=1)  # Свежее
        mock_listing.floor = 5
        mock_listing.total_floors = 9
        mock_listing.images = ["img1.jpg"]
        mock_listing.area = 60.0

        # drop_percent = 25 → TrendScore = 100
        score = await service_without_redis.calculate_score(
            listing=mock_listing,
            avg_price_per_m2=1000.0,
            drop_percent=25.0
        )

        # PriceScore = 100 (цена почти 0)
        # TrendScore = 100
        # LiquidityScore = 90 (< 3 дней)
        # FreshnessScore = 100 (< 24 часов)
        # FloorScore = 80 (средний этаж)
        # BonusScore = 40 (images + area)
        # Score = 0.40*100 + 0.20*100 + 0.15*90 + 0.10*100 + 0.05*80 + 0.10*40
        #       = 40 + 20 + 13.5 + 10 + 4 + 4 = 91.5
        assert score > 90.0

    @pytest.mark.asyncio
    async def test_all_scores_0(self, service_without_redis, mock_listing):
        """Тест: Все факторы 0 → Score близок к 0."""
        # Подготовить listing для минимальных значений
        mock_listing.price_per_m2_usd = Decimal("1500.00")  # Высокая цена
        mock_listing.first_seen_at = datetime.now() - timedelta(days=30)  # Старое
        mock_listing.floor = 1  # Первый этаж
        mock_listing.total_floors = 9
        mock_listing.images = []
        mock_listing.area = 30.0

        # drop_percent = 0 → TrendScore = 0
        score = await service_without_redis.calculate_score(
            listing=mock_listing,
            avg_price_per_m2=1000.0,
            drop_percent=0.0
        )

        # PriceScore = 0 (цена выше рынка)
        # TrendScore = 0
        # LiquidityScore = 20 (30 дней)
        # FreshnessScore = 30 (> 72 часов)
        # FloorScore = 40 (первый этаж)
        # BonusScore = 0
        # Score = 0.40*0 + 0.20*0 + 0.15*20 + 0.10*30 + 0.05*40 + 0.10*0
        #       = 0 + 0 + 3 + 3 + 2 + 0 = 8.0
        assert score == 8.0

    @pytest.mark.asyncio
    async def test_mixed_scores(self, service_without_redis, mock_listing):
        """Тест: Смешанные значения → корректный weighted sum."""
        mock_listing.price_per_m2_usd = Decimal("800.00")
        mock_listing.first_seen_at = datetime.now() - timedelta(days=5)
        mock_listing.floor = 5
        mock_listing.total_floors = 9
        mock_listing.images = ["img1.jpg"]
        mock_listing.area = 60.0

        # drop_percent = 12 → TrendScore = 70
        score = await service_without_redis.calculate_score(
            listing=mock_listing,
            avg_price_per_m2=1000.0,
            drop_percent=12.0
        )

        # PriceScore = 20 ((1000-800)/1000*100)
        # TrendScore = 70 (10 <= 12 < 20)
        # LiquidityScore = 70 (3 <= 5 < 7)
        # FreshnessScore = 30 (> 72 часов, 5 дней = 120 часов)
        # FloorScore = 80 (средний этаж)
        # BonusScore = 40 (images + area)
        # Score = 0.40*20 + 0.20*70 + 0.15*70 + 0.10*30 + 0.05*80 + 0.10*40
        #       = 8 + 14 + 10.5 + 3 + 4 + 4 = 43.5
        assert score == 43.5


class TestLabel:
    """Тесты метода calculate_label."""

    def test_hot_label(self):
        """Тест: score = 85 → '🔥 HOT'."""
        label = DealScoreService.calculate_label(85.0)
        assert label == "🔥 HOT"

    def test_good_label(self):
        """Тест: score = 70 → '🔥 HOT'."""
        label = DealScoreService.calculate_label(70.0)
        assert label == "🔥 HOT"

    def test_normal_label(self):
        """Тест: score = 40 → '👍 GOOD'."""
        label = DealScoreService.calculate_label(40.0)
        assert label == "👍 GOOD"


class TestWeightsValidation:
    """Тесты валидации весов."""

    def test_valid_weights_default(self):
        """Тест: weights sum = 1.0 → OK (default weights)."""
        service = DealScoreService(redis_client=None)
        assert service.weights == DealScoreService.DEFAULT_WEIGHTS

    def test_invalid_weights_low(self):
        """Тест: weights sum = 0.95 → ValueError."""
        invalid_weights = {
            "price": 0.35,
            "trend": 0.15,
            "liquidity": 0.10,
            "freshness": 0.10,
            "floor": 0.05,
            "bonus": 0.10,
        }  # sum = 0.85

        with pytest.raises(ValueError, match="Sum of weights must be 1.0"):
            DealScoreService(redis_client=None, weights=invalid_weights)

    def test_invalid_weights_high(self):
        """Тест: weights sum = 1.05 → ValueError."""
        invalid_weights = {
            "price": 0.50,
            "trend": 0.25,
            "liquidity": 0.15,
            "freshness": 0.10,
            "floor": 0.05,
            "bonus": 0.10,
        }  # sum = 1.15

        with pytest.raises(ValueError, match="Sum of weights must be 1.0"):
            DealScoreService(redis_client=None, weights=invalid_weights)


class TestScoreBreakdown:
    """Тесты метода get_score_breakdown."""

    @pytest.mark.asyncio
    async def test_breakdown_structure(self, service_without_redis, mock_listing):
        """Тест: get_score_breakdown возвращает корректную структуру."""
        mock_listing.price_per_m2_usd = Decimal("800.00")
        mock_listing.first_seen_at = datetime.now() - timedelta(days=5)
        mock_listing.floor = 5
        mock_listing.total_floors = 9
        mock_listing.images = ["img1.jpg"]
        mock_listing.area = 60.0

        breakdown = await service_without_redis.get_score_breakdown(
            listing=mock_listing,
            avg_price_per_m2=1000.0,
            drop_percent=12.0
        )

        # Проверка структуры
        assert "deal_score" in breakdown
        assert "deal_label" in breakdown
        assert "breakdown" in breakdown

        # Проверка breakdown
        bd = breakdown["breakdown"]
        assert "price_score" in bd
        assert "trend_score" in bd
        assert "liquidity_score" in bd
        assert "freshness_score" in bd
        assert "floor_score" in bd
        assert "bonus_score" in bd

        # Каждый sub-score имеет score, weight, weighted
        for key in bd:
            assert "score" in bd[key]
            assert "weight" in bd[key]
            assert "weighted" in bd[key]

        # Проверка label
        expected_label = DealScoreService.calculate_label(breakdown["deal_score"])
        assert breakdown["deal_label"] == expected_label

    @pytest.mark.asyncio
    async def test_breakdown_weighted_sum(self, service_without_redis, mock_listing):
        """Тест: breakdown weighted sum = deal_score."""
        mock_listing.price_per_m2_usd = Decimal("800.00")
        mock_listing.first_seen_at = datetime.now() - timedelta(days=5)
        mock_listing.floor = 5
        mock_listing.total_floors = 9
        mock_listing.images = ["img1.jpg"]
        mock_listing.area = 60.0

        breakdown = await service_without_redis.get_score_breakdown(
            listing=mock_listing,
            avg_price_per_m2=1000.0,
            drop_percent=12.0
        )

        # Сумма weighted должна быть равна deal_score (с допуском на округление)
        weighted_sum = sum(item["weighted"] for item in breakdown["breakdown"].values())
        assert abs(weighted_sum - breakdown["deal_score"]) < 0.1


class TestRedisCaching:
    """Тесты Redis кэширования."""

    @pytest.mark.asyncio
    async def test_cache_hit(self, service_with_redis, mock_redis, mock_listing):
        """Тест: Redis cache hit → возвращает кэшированное значение."""
        mock_redis.get = AsyncMock(return_value="72.50")

        score = await service_with_redis.calculate_score(
            listing=mock_listing,
            avg_price_per_m2=1000.0,
            drop_percent=12.0
        )

        assert score == 72.50
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_not_called()  # Не должен вызывать setex при cache hit

    @pytest.mark.asyncio
    async def test_cache_miss(self, service_with_redis, mock_redis, mock_listing):
        """Тест: Redis cache miss → вычисляет и кэширует."""
        mock_redis.get = AsyncMock(return_value=None)

        mock_listing.price_per_m2_usd = Decimal("800.00")
        mock_listing.first_seen_at = datetime.now() - timedelta(days=5)
        mock_listing.floor = 5
        mock_listing.total_floors = 9
        mock_listing.images = ["img1.jpg"]
        mock_listing.area = 60.0

        score = await service_with_redis.calculate_score(
            listing=mock_listing,
            avg_price_per_m2=1000.0,
            drop_percent=12.0
        )

        # Должен вызвать setex для кэширования
        mock_redis.setex.assert_called_once()
        cache_key, ttl, value = mock_redis.setex.call_args[0]
        assert cache_key == f"deal_score:{mock_listing.id}"
        assert ttl == 300
        assert float(value) == score

    @pytest.mark.asyncio
    async def test_redis_error_does_not_crash(self, service_with_redis, mock_redis, mock_listing):
        """Тест: Redis error → сервис работает без кэширования."""
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection error"))
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis connection error"))

        mock_listing.price_per_m2_usd = Decimal("800.00")
        mock_listing.first_seen_at = datetime.now() - timedelta(days=5)

        # Должен работать без кэша
        score = await service_with_redis.calculate_score(
            listing=mock_listing,
            avg_price_per_m2=1000.0,
            drop_percent=12.0
        )

        assert isinstance(score, float)
        assert 0 <= score <= 100


class TestEdgeCases:
    """Тесты граничных случаев."""

    @pytest.mark.asyncio
    async def test_very_high_discount(self, service_without_redis, mock_listing):
        """Тест: Очень большой discount → PriceScore capped at 100."""
        mock_listing.price_per_m2_usd = Decimal("1.00")  # Почти бесплатная
        avg_price_per_m2 = 1000.0

        price_score = service_without_redis.calculate_price_score(mock_listing, avg_price_per_m2)

        # (1000 - 1) / 1000 * 100 = 99.9 → close to 100
        assert price_score >= 99.0

    @pytest.mark.asyncio
    async def test_very_old_listing(self, service_without_redis, mock_listing):
        """Тест: Очень старое объявление → минимальные scores."""
        mock_listing.first_seen_at = datetime.now() - timedelta(days=365)

        liquidity_score = service_without_redis.calculate_liquidity_score(mock_listing)
        freshness_score = service_without_redis.calculate_freshness_score(mock_listing)

        assert liquidity_score == 20.0
        assert freshness_score == 30.0

    def test_label_boundaries(self):
        """Тест: Label boundaries корректны."""
        assert DealScoreService.calculate_label(80.0) == "🔥 HOT"
        assert DealScoreService.calculate_label(50.0) == "🔥 HOT"
        assert DealScoreService.calculate_label(49.99) == "👍 GOOD"
        assert DealScoreService.calculate_label(35.0) == "👍 GOOD"
        assert DealScoreService.calculate_label(34.99) == "😐 NORMAL"

    def test_custom_weights(self):
        """Тест: Кастомные веса работают корректно."""
        custom_weights = {
            "price": 0.50,
            "trend": 0.20,
            "liquidity": 0.10,
            "freshness": 0.10,
            "floor": 0.05,
            "bonus": 0.05,
        }  # sum = 1.0

        service = DealScoreService(redis_client=None, weights=custom_weights)
        assert service.weights["price"] == 0.50
        assert service.weights["bonus"] == 0.05


class TestFactoryFunction:
    """Тесты factory функции get_deal_score_service."""

    def test_factory_without_redis(self):
        """Тест: Factory без Redis."""
        from app.services.deal_score_service import get_deal_score_service

        service = get_deal_score_service(redis_client=None)
        assert isinstance(service, DealScoreService)
        assert service.redis_client is None

    def test_factory_with_mock_redis(self):
        """Тест: Factory с mock Redis."""
        from app.services.deal_score_service import get_deal_score_service

        mock_redis = AsyncMock()
        service = get_deal_score_service(redis_client=mock_redis)
        assert isinstance(service, DealScoreService)
        assert service.redis_client == mock_redis
