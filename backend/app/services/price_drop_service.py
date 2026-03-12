"""
Price Drop Service — сервис для отслеживания падения цен.

Предоставляет методы для:
- Поиска объявлений с падением цены
- Получения истории изменений цены
- Расчёта статистики падения цен

Использует Redis кэширование для ускорения ответов API.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
import json
import redis.asyncio as redis

from app.models.listing import Listing, ListingHistory, EventType, ListingStatus
from app.schemas.price_drop import (
    PriceDropListing,
    PriceDropHistoryItem,
    PriceDropStats,
)
from app.core.redis_client import get_redis
from app.config import settings, CITY_NAMES


# TTL для кэширования (в секундах)
CACHE_TTL_PRICE_DROPS = 300  # 5 минут
CACHE_TTL_PRICE_HISTORY = 180  # 3 минуты
CACHE_TTL_PRICE_DROP_STATS = 600  # 10 минут


class PriceDropService:
    """
    Сервис для работы с падением цен.

    Методы:
        get_price_drop_listings: Получить список объявлений с падением цены
        get_listing_price_history: Получить историю цен объявления
        get_price_drop_stats: Получить статистику падения цен
    """

    def __init__(self, db: AsyncSession):
        """
        Инициализация сервиса.

        Args:
            db: Асинхронная сессия базы данных
        """
        self.db = db
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> Optional[redis.Redis]:
        """Получить Redis подключение."""
        if self._redis is None:
            try:
                self._redis = await get_redis()
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                return None
        return self._redis

    def _generate_cache_key(
        self, prefix: str, **params: Any
    ) -> str:
        """
        Генерирует ключ кэша из параметров.

        Args:
            prefix: Префикс ключа
            **params: Параметры для ключа

        Returns:
            Строка ключа в формате: cache:{prefix}:{param1}={value1}:{param2}={value2}
        """
        sorted_params = sorted(params.items())
        param_str = ":".join(f"{k}={v}" for k, v in sorted_params if v is not None)
        if not param_str:
            param_str = "default"
        return f"cache:{prefix}:{param_str}"

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Получить данные из Redis кэша.

        Args:
            key: Ключ кэша

        Returns:
            Десериализованные данные или None
        """
        redis_client = await self._get_redis()
        if not redis_client:
            return None

        try:
            cached_data = await redis_client.get(key)
            if cached_data is None:
                return None

            deserialized = json.loads(cached_data)
            logger.debug(f"Cache hit for key {key}")
            return deserialized
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize cache data for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Redis error getting cache for key {key}: {e}")
            return None

    async def _set_to_cache(self, key: str, data: Any, ttl: int) -> bool:
        """
        Сохранить данные в Redis кэш.

        Args:
            key: Ключ кэша
            data: Данные для сохранения
            ttl: Время жизни кэша в секундах

        Returns:
            True если успешно
        """
        redis_client = await self._get_redis()
        if not redis_client:
            return False

        try:
            # Сериализация с поддержкой Decimal и datetime
            def default_serializer(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                elif hasattr(obj, "model_dump"):
                    return obj.model_dump()
                return str(obj)

            serialized_data = json.dumps(data, default=default_serializer, ensure_ascii=False)
            await redis_client.setex(key, ttl, serialized_data)
            logger.debug(f"Cached data for key {key} with TTL {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False

    async def get_price_drop_listings(
        self,
        city: str,
        drop_percent: float = 10.0,
        limit: int = 20,
        offset: int = 0,
        currency: str = "usd",
    ) -> Tuple[List[Dict[str, Any]], float, float, float, int]:
        """
        Получить список объявлений с падением цены.

        Использует SQL агрегацию для расчёта drop_percent:
            drop_percent = ((MAX(price_before) - MIN(price_after)) / MAX(price_before)) * 100

        Args:
            city: Город для фильтрации
            drop_percent: Минимальный процент падения (0-100)
            limit: Количество результатов (1-100)
            offset: Смещение для пагинации
            currency: Валюта ('byn' или 'usd')

        Returns:
            Кортеж (listings, avg_drop, max_drop, min_drop, total)
            - listings: Список словарей с данными объявлений
            - avg_drop: Средний процент падения
            - max_drop: Максимальный процент падения
            - min_drop: Минимальный процент падения
            - total: Общее количество объявлений
        """
        # Проверка кэша
        cache_key = self._generate_cache_key(
            "price_drops",
            city=city,
            drop_percent=drop_percent,
            currency=currency,
            limit=limit,
            offset=offset,
        )
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return (
                cached_result.get("items", []),
                cached_result.get("avg_drop_percent", 0),
                cached_result.get("max_drop_percent", 0),
                cached_result.get("min_drop_percent", 0),
                cached_result.get("total", 0),
            )

        # Определяем поле цены в зависимости от валюты
        price_before_field = (
            ListingHistory.price_before_usd
            if currency == "usd"
            else ListingHistory.price_before
        )
        price_after_field = (
            ListingHistory.price_after_usd
            if currency == "usd"
            else ListingHistory.price_after
        )

        # Базовый запрос для агрегации
        subquery = (
            select(
                ListingHistory.listing_id,
                func.max(price_before_field).label("max_price"),
                func.min(price_after_field).label("min_price"),
            )
            .where(
                and_(
                    ListingHistory.event_type == EventType.price_changed,
                    price_before_field.isnot(None),
                    price_after_field.isnot(None),
                )
            )
            .group_by(ListingHistory.listing_id)
            .cte("price_drops_subquery")
        )

        # Запрос с расчётом drop_percent
        drop_query = (
            select(
                subquery.c.listing_id,
                subquery.c.max_price,
                subquery.c.min_price,
                (
                    (subquery.c.max_price - subquery.c.min_price)
                    / func.nullif(subquery.c.max_price, 0)
                    * 100
                ).label("drop_percent"),
            )
            .where(
                and_(
                    subquery.c.max_price > 0,
                    ((subquery.c.max_price - subquery.c.min_price) / func.nullif(subquery.c.max_price, 0) * 100)
                    >= drop_percent,
                )
            )
        )

        # Получаем total через подзапрос
        total_cte = drop_query.cte("drop_query_total")
        total_result = await self.db.execute(
            select(func.count()).select_from(total_cte)
        )
        total = total_result.scalar() or 0

        # Основной запрос с JOIN к listings
        drop_query_limited = drop_query.order_by(
            func.nullif(
                (subquery.c.max_price - subquery.c.min_price)
                / func.nullif(subquery.c.max_price, 0)
                * 100,
                0,
            ).desc()
        ).offset(offset).limit(limit)

        # CTE для ограниченного запроса
        limited_cte = drop_query_limited.cte("drop_query_limited")

        # Финальный запрос с данными объявлений
        final_query = (
            select(
                Listing,
                limited_cte.c.max_price,
                limited_cte.c.min_price,
                limited_cte.c.drop_percent,
            )
            .join(limited_cte, Listing.id == limited_cte.c.listing_id)
            .where(
                and_(
                    Listing.city == city,
                    Listing.status != ListingStatus.deleted,
                    Listing.status != ListingStatus.archived,
                )
            )
        )

        result = await self.db.execute(final_query)
        rows = result.all()

        # Формируем ответ
        listings = []
        drop_percents = []

        for row in rows:
            listing = row[0]
            max_price = row[1]
            min_price = row[2]
            drop_pct = float(row[3]) if row[3] else 0.0

            drop_percents.append(drop_pct)

            # Текущая цена в зависимости от валюты
            current_price = (
                listing.price_usd if currency == "usd" else listing.price
            )

            listings.append(
                {
                    "id": str(listing.id),
                    "kufar_id": listing.kufar_id,
                    "url": listing.url,
                    "title": listing.title,
                    "current_price": current_price or 0,
                    "max_price": max_price or 0,
                    "min_price": min_price or 0,
                    "drop_percent": round(drop_pct, 2),
                    "city": listing.city,
                    "rooms": listing.rooms,
                    "area": listing.area,
                    "floor": listing.floor,
                    "images": listing.images or [],
                    "status": listing.status.value if hasattr(listing.status, "value") else str(listing.status),
                    "first_seen_at": listing.first_seen_at,
                    "last_seen_at": listing.last_seen_at,
                }
            )

        # Статистика
        avg_drop = sum(drop_percents) / len(drop_percents) if drop_percents else 0.0
        max_drop = max(drop_percents) if drop_percents else 0.0
        min_drop = min(drop_percents) if drop_percents else 0.0

        # Кэширование результата
        cache_data = {
            "items": listings,
            "avg_drop_percent": round(avg_drop, 2),
            "max_drop_percent": round(max_drop, 2),
            "min_drop_percent": round(min_drop, 2),
            "total": total,
        }
        await self._set_to_cache(cache_key, cache_data, CACHE_TTL_PRICE_DROPS)

        logger.info(
            f"Price drops: city={city}, currency={currency}, drop_percent>={drop_percent}, "
            f"total={total}, returned={len(listings)}"
        )

        return listings, avg_drop, max_drop, min_drop, total

    async def get_listing_price_history(
        self,
        listing_id: UUID,
        currency: str = "usd",
    ) -> Tuple[List[Dict[str, Any]], Optional[int], Optional[int], Optional[float]]:
        """
        Получить историю изменений цены для объявления.

        Args:
            listing_id: UUID объявления
            currency: Валюта ('byn' или 'usd')

        Returns:
            Кортеж (history_items, first_price, last_price, total_drop_percent)
        """
        # Проверка кэша
        cache_key = self._generate_cache_key(
            "price_history",
            listing_id=str(listing_id),
            currency=currency,
        )
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return (
                cached_result.get("items", []),
                cached_result.get("first_price"),
                cached_result.get("last_price"),
                cached_result.get("total_drop_percent"),
            )

        # Определяем поле цены в зависимости от валюты
        price_before_field = (
            ListingHistory.price_before_usd
            if currency == "usd"
            else ListingHistory.price_before
        )
        price_after_field = (
            ListingHistory.price_after_usd
            if currency == "usd"
            else ListingHistory.price_after
        )

        # Запрос истории изменений цены
        query = (
            select(ListingHistory)
            .where(
                and_(
                    ListingHistory.listing_id == listing_id,
                    ListingHistory.event_type.in_(
                        [EventType.price_changed, EventType.price_changed_byn]
                    ),
                    price_before_field.isnot(None),
                    price_after_field.isnot(None),
                )
            )
            .order_by(ListingHistory.created_at.asc())
        )

        result = await self.db.execute(query)
        history_records = result.scalars().all()

        # Формируем ответ
        items = []
        prices = []

        for record in history_records:
            price_before = (
                record.price_before_usd if currency == "usd" else record.price_before
            )
            price_after = (
                record.price_after_usd if currency == "usd" else record.price_after
            )

            if price_before:
                prices.append(price_before)
            if price_after:
                prices.append(price_after)

            items.append(
                {
                    "id": str(record.id),
                    "event_type": record.event_type.value if hasattr(record.event_type, "value") else str(record.event_type),
                    "price_before": price_before,
                    "price_after": price_after,
                    "created_at": record.created_at,
                }
            )

        # Первая и последняя цена
        first_price = prices[0] if prices else None
        last_price = prices[-1] if prices else None

        # Общий процент падения
        total_drop_percent = None
        if first_price and last_price and first_price > 0:
            total_drop_percent = ((first_price - last_price) / first_price) * 100

        # Кэширование результата
        cache_data = {
            "items": items,
            "first_price": first_price,
            "last_price": last_price,
            "total_drop_percent": round(total_drop_percent, 2) if total_drop_percent else None,
        }
        await self._set_to_cache(cache_key, cache_data, CACHE_TTL_PRICE_HISTORY)

        logger.info(
            f"Price history: listing_id={listing_id}, currency={currency}, "
            f"events={len(items)}, drop={total_drop_percent}"
        )

        return items, first_price, last_price, total_drop_percent

    async def get_price_drop_stats(
        self,
        city: str,
        drop_percent: float = 10.0,
        currency: str = "usd",
    ) -> Dict[str, Any]:
        """
        Получить статистику падения цен по городу.

        Args:
            city: Город для фильтрации
            drop_percent: Минимальный процент падения (0-100)
            currency: Валюта ('byn' или 'usd')

        Returns:
            Словарь со статистикой (total_drops, avg_drop_percent, max_drop_percent, min_drop_percent)
        """
        # Проверка кэша
        cache_key = self._generate_cache_key(
            "price_drop_stats",
            city=city,
            drop_percent=drop_percent,
            currency=currency,
        )
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        # Определяем поле цены в зависимости от валюты
        price_before_field = (
            ListingHistory.price_before_usd
            if currency == "usd"
            else ListingHistory.price_before
        )
        price_after_field = (
            ListingHistory.price_after_usd
            if currency == "usd"
            else ListingHistory.price_after
        )

        # Подзапрос для агрегации
        subquery = (
            select(
                ListingHistory.listing_id,
                func.max(price_before_field).label("max_price"),
                func.min(price_after_field).label("min_price"),
            )
            .where(
                and_(
                    ListingHistory.event_type == EventType.price_changed,
                    price_before_field.isnot(None),
                    price_after_field.isnot(None),
                )
            )
            .group_by(ListingHistory.listing_id)
            .cte("price_drops_stats_subquery")
        )

        # Запрос с расчётом drop_percent
        drop_query = (
            select(
                subquery.c.listing_id,
                (
                    (subquery.c.max_price - subquery.c.min_price)
                    / func.nullif(subquery.c.max_price, 0)
                    * 100
                ).label("drop_percent"),
            )
            .where(
                and_(
                    subquery.c.max_price > 0,
                    ((subquery.c.max_price - subquery.c.min_price) / func.nullif(subquery.c.max_price, 0) * 100)
                    >= drop_percent,
                )
            )
        )

        # CTE для расчёта статистики
        drop_cte = drop_query.cte("drop_query_stats")

        # Запрос статистики
        stats_query = select(
            func.count().label("total_drops"),
            func.avg(drop_cte.c.drop_percent).label("avg_drop"),
            func.max(drop_cte.c.drop_percent).label("max_drop"),
            func.min(drop_cte.c.drop_percent).label("min_drop"),
        )

        stats_result = await self.db.execute(stats_query)
        stats_row = stats_result.first()

        total_drops = stats_row[0] if stats_row else 0
        avg_drop = float(stats_row[1]) if stats_row and stats_row[1] else 0.0
        max_drop = float(stats_row[2]) if stats_row and stats_row[2] else 0.0
        min_drop = float(stats_row[3]) if stats_row and stats_row[3] else 0.0

        result = {
            "total_drops": total_drops,
            "avg_drop_percent": round(avg_drop, 2),
            "max_drop_percent": round(max_drop, 2),
            "min_drop_percent": round(min_drop, 2),
            "currency": currency.upper(),
        }

        # Кэширование результата
        await self._set_to_cache(cache_key, result, CACHE_TTL_PRICE_DROP_STATS)

        logger.info(
            f"Price drop stats: city={city}, currency={currency}, "
            f"total={total_drops}, avg={avg_drop}%"
        )

        return result


def get_price_drop_service(db: AsyncSession) -> PriceDropService:
    """
    Factory функция для создания PriceDropService.

    Args:
        db: Асинхронная сессия базы данных

    Returns:
        Экземпляр PriceDropService
    """
    return PriceDropService(db)
