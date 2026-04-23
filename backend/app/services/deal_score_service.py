"""
Deal Score Service — сервис расчёта скоринга выгодности объявлений.

Оценивает объявление по шкале от 0 до 100 на основе 6 факторов:
- PriceScore (0.40) — цена ниже рынка
- TrendScore (0.20) — динамика цены (падение)
- LiquidityScore (0.15) — ликвидность (дней на рынке)
- FreshnessScore (0.10) — свежесть объявления
- FloorScore (0.05) — предпочтительность этажа
- BonusScore (0.10) — бонусы (фото, площадь)

Использует Redis для кэширования результатов (TTL 300 сек).
"""

from datetime import datetime
from typing import Dict, Optional
from loguru import logger
import redis.asyncio as redis


class DealScoreService:
    """
    Сервис расчёта Deal Score (0-100) для оценки выгодности объявлений.

    Атрибуты:
        DEFAULT_WEIGHTS: Веса по умолчанию (сумма = 1.0)
        redis_client: Redis клиент для кэширования
        weights: Активные веса
    """

    # Default weights (сумма = 1.0)
    DEFAULT_WEIGHTS = {
        "price": 0.40,
        "trend": 0.20,
        "liquidity": 0.15,
        "freshness": 0.10,
        "floor": 0.05,
        "bonus": 0.10,
    }

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Инициализация сервиса.

        Args:
            redis_client: Redis клиент для кэширования (опционально)
            weights: Кастомные веса (по умолчанию DEFAULT_WEIGHTS)

        Raises:
            ValueError: Если сумма весов не равна 1.0 (допуск 0.01)
        """
        self.redis_client = redis_client
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._validate_weights()

    def _validate_weights(self) -> None:
        """
        Валидация: сумма весов должна быть ~1.0 (допуск 0.01).

        Raises:
            ValueError: Если сумма весов выходит за пределы [0.99, 1.01]
        """
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Sum of weights must be 1.0, got {total:.4f}")

    async def calculate_score(
        self,
        listing,
        avg_price_per_m2: float,
        drop_percent: float = 0.0,
    ) -> float:
        """
        Расчёт Deal Score для объявления.

        Args:
            listing: SQLAlchemy Listing модель
            avg_price_per_m2: Средняя цена за м² по городу/комнатам
            drop_percent: Процент падения цены (из Price Drop Tracker)

        Returns:
            float: Deal Score (0-100), округлённый до 2 знаков
        """
        # Check Redis cache
        cache_key = f"deal_score:{listing.id}"
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for deal_score: {cache_key}")
                    return float(cached)
            except Exception as e:
                logger.warning(f"Redis cache error for {cache_key}: {e}")

        # Calculate sub-scores
        price_score = self.calculate_price_score(listing, avg_price_per_m2)
        trend_score = self.calculate_trend_score(drop_percent)
        liquidity_score = self.calculate_liquidity_score(listing)
        freshness_score = self.calculate_freshness_score(listing)
        floor_score = self.calculate_floor_score(listing)
        bonus_score = self.calculate_bonus_score(listing)

        logger.info(
            f"Deal scores calculated: listing_id={listing.id}, "
            f"price_score={price_score}, trend_score={trend_score}, "
            f"liquidity_score={liquidity_score}, freshness_score={freshness_score}, "
            f"floor_score={floor_score}, bonus_score={bonus_score}"
        )

        # Weighted sum
        score = (
            self.weights["price"] * price_score
            + self.weights["trend"] * trend_score
            + self.weights["liquidity"] * liquidity_score
            + self.weights["freshness"] * freshness_score
            + self.weights["floor"] * floor_score
            + self.weights["bonus"] * bonus_score
        )

        # Clamp to 0-100
        score = max(0.0, min(100.0, score))
        score = round(score, 2)

        # Cache in Redis (TTL 300 сек)
        if self.redis_client:
            try:
                await self.redis_client.setex(cache_key, 300, str(score))
                logger.debug(f"Cached deal_score: {cache_key} = {score}")
            except Exception as e:
                logger.warning(f"Redis cache set error for {cache_key}: {e}")

        return score

    def calculate_price_score(self, listing, avg_price_per_m2: float) -> float:
        """
        PriceScore: насколько цена ниже средней.

        Формула: discount_percent = (avg - current) / avg * 100
        Если цена выше средней → 0.

        Args:
            listing: SQLAlchemy Listing модель
            avg_price_per_m2: Средняя цена за м²

        Returns:
            float: PriceScore (0-100)
        """
        if not avg_price_per_m2 or avg_price_per_m2 <= 0:
            logger.debug(f"PriceScore: invalid avg_price_per_m2={avg_price_per_m2}")
            return 0.0

        price_per_m2 = float(listing.price_per_m2_usd or 0)
        if price_per_m2 <= 0:
            logger.debug(
                f"PriceScore: invalid price_per_m2={price_per_m2} for listing {listing.id}"
            )
            return 0.0

        discount_percent = (avg_price_per_m2 - price_per_m2) / avg_price_per_m2 * 100
        score = max(0.0, min(100.0, discount_percent))

        logger.debug(
            f"PriceScore: avg={avg_price_per_m2}, current={price_per_m2}, discount={discount_percent:.2f}%, score={score}"
        )
        return score

    def calculate_trend_score(self, drop_percent: float) -> float:
        """
        TrendScore: динамика цены.

        Логика:
        - drop_percent >= 20 → 100
        - drop_percent >= 10 → 70
        - drop_percent > 0 → 40
        - иначе → 0

        Args:
            drop_percent: Процент падения цены

        Returns:
            float: TrendScore (0, 40, 70 или 100)
        """
        if drop_percent >= 20:
            score = 100.0
        elif drop_percent >= 10:
            score = 70.0
        elif drop_percent > 0:
            score = 40.0
        else:
            score = 0.0

        logger.debug(f"TrendScore: drop_percent={drop_percent}, score={score}")
        return score

    def calculate_liquidity_score(self, listing) -> float:
        """
        LiquidityScore: ликвидность (дней на рынке).

        Логика:
        - < 3 дней → 90
        - < 7 дней → 70
        - < 14 дней → 50
        - >= 14 дней → 20

        Args:
            listing: SQLAlchemy Listing модель

        Returns:
            float: LiquidityScore (20, 50, 70 или 90)
        """
        if not listing.first_seen_at:
            logger.debug(
                f"LiquidityScore: no first_seen_at for listing {listing.id}, using default 50"
            )
            return 50.0

        days_on_market = (datetime.now() - listing.first_seen_at).days

        if days_on_market < 3:
            score = 90.0
        elif days_on_market < 7:
            score = 70.0
        elif days_on_market < 14:
            score = 50.0
        else:
            score = 20.0

        logger.debug(f"LiquidityScore: days_on_market={days_on_market}, score={score}")
        return score

    def calculate_freshness_score(self, listing) -> float:
        """
        FreshnessScore: свежесть объявления.

        Логика:
        - < 24 часов → 100
        - < 72 часов → 70
        - >= 72 часов → 30

        Args:
            listing: SQLAlchemy Listing модель

        Returns:
            float: FreshnessScore (30, 70 или 100)
        """
        if not listing.first_seen_at:
            logger.debug(
                f"FreshnessScore: no first_seen_at for listing {listing.id}, using default 50"
            )
            return 50.0

        hours_since_first_seen = (
            datetime.now() - listing.first_seen_at
        ).total_seconds() / 3600

        if hours_since_first_seen < 24:
            score = 100.0
        elif hours_since_first_seen < 72:
            score = 70.0
        else:
            score = 30.0

        logger.debug(
            f"FreshnessScore: hours={hours_since_first_seen:.1f}, score={score}"
        )
        return score

    def calculate_floor_score(self, listing) -> float:
        """
        FloorScore: предпочтительность этажа.

        Логика:
        - Первый или последний этаж → 40
        - Средние этажи → 80

        Args:
            listing: SQLAlchemy Listing модель

        Returns:
            float: FloorScore (40 или 80)
        """
        if not listing.floor or not listing.total_floors:
            logger.debug(
                f"FloorScore: no floor/total_floors for listing {listing.id}, using default 50"
            )
            return 50.0

        if listing.floor == 1 or listing.floor == listing.total_floors:
            score = 40.0
        else:
            score = 80.0

        logger.debug(
            f"FloorScore: floor={listing.floor}/{listing.total_floors}, score={score}"
        )
        return score

    def calculate_bonus_score(self, listing) -> float:
        """
        BonusScore: бонусы (фото, площадь).

        Логика:
        - Есть фото → +20
        - Площадь > 50 м² → +20
        - Бонус за локацию — зарезервировано

        Args:
            listing: SQLAlchemy Listing модель

        Returns:
            float: BonusScore (0-100)
        """
        score = 0.0

        # Images bonus
        if listing.images and len(listing.images) > 0:
            score += 20.0

        # Area bonus
        if listing.area and listing.area > 50:
            score += 20.0

        # Location bonus — зарезервировано (пока не используем)
        # if listing.good_location:
        #     score += 60.0

        score = min(score, 100.0)
        logger.debug(
            f"BonusScore: has_images={bool(listing.images)}, area={listing.area}, score={score}"
        )
        return score

    @staticmethod
    def calculate_label(score: float) -> str:
        """
        Получить текстовую метку по Score.

        Пороги (оптимизированы для реальных данных):
        - 50+ → 🔥 HOT (отличная сделка)
        - 35+ → 👍 GOOD (хорошая сделка)
        - <35 → 😐 NORMAL (обычное объявление)

        Args:
            score: Deal Score (0-100)

        Returns:
            str: Текстовая метка ("🔥 HOT", "👍 GOOD" или "😐 NORMAL")
        """
        if score >= 50:
            return "🔥 HOT"
        elif score >= 35:
            return "👍 GOOD"
        else:
            return "😐 NORMAL"

    async def get_score_breakdown(
        self,
        listing,
        avg_price_per_m2: float,
        drop_percent: float = 0.0,
    ) -> dict:
        """
        Получить детализацию по всем факторам.

        Args:
            listing: SQLAlchemy Listing модель
            avg_price_per_m2: Средняя цена за м²
            drop_percent: Процент падения цены

        Returns:
            dict: Структура с deal_score, deal_label и breakdown по факторам
        """
        price_score = self.calculate_price_score(listing, avg_price_per_m2)
        trend_score = self.calculate_trend_score(drop_percent)
        liquidity_score = self.calculate_liquidity_score(listing)
        freshness_score = self.calculate_freshness_score(listing)
        floor_score = self.calculate_floor_score(listing)
        bonus_score = self.calculate_bonus_score(listing)

        # Weighted sum
        score = (
            self.weights["price"] * price_score
            + self.weights["trend"] * trend_score
            + self.weights["liquidity"] * liquidity_score
            + self.weights["freshness"] * freshness_score
            + self.weights["floor"] * floor_score
            + self.weights["bonus"] * bonus_score
        )
        score = max(0.0, min(100.0, score))
        score = round(score, 2)

        breakdown = {
            "price_score": {
                "score": round(price_score, 2),
                "weight": self.weights["price"],
                "weighted": round(self.weights["price"] * price_score, 2),
            },
            "trend_score": {
                "score": round(trend_score, 2),
                "weight": self.weights["trend"],
                "weighted": round(self.weights["trend"] * trend_score, 2),
            },
            "liquidity_score": {
                "score": round(liquidity_score, 2),
                "weight": self.weights["liquidity"],
                "weighted": round(self.weights["liquidity"] * liquidity_score, 2),
            },
            "freshness_score": {
                "score": round(freshness_score, 2),
                "weight": self.weights["freshness"],
                "weighted": round(self.weights["freshness"] * freshness_score, 2),
            },
            "floor_score": {
                "score": round(floor_score, 2),
                "weight": self.weights["floor"],
                "weighted": round(self.weights["floor"] * floor_score, 2),
            },
            "bonus_score": {
                "score": round(bonus_score, 2),
                "weight": self.weights["bonus"],
                "weighted": round(self.weights["bonus"] * bonus_score, 2),
            },
        }

        # Verify: sum of weighted scores = deal_score (с допуском на округление)
        weighted_sum = sum(item["weighted"] for item in breakdown.values())
        logger.info(
            f"Deal score breakdown: listing_id={listing.id}, "
            f"score={score}, weighted_sum={weighted_sum:.2f}, "
            f"label={self.calculate_label(score)}"
        )

        return {
            "deal_score": score,
            "deal_label": self.calculate_label(score),
            "breakdown": breakdown,
        }


def get_deal_score_service(redis_client=None) -> DealScoreService:
    """
    Factory функция для создания DealScoreService.

    Args:
        redis_client: Redis клиент (опционально)

    Returns:
        Экземпляр DealScoreService
    """
    return DealScoreService(redis_client=redis_client)
