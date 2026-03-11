"""
Deal Finder Service - сервис для поиска выгодных предложений.

Предоставляет методы для:
- Расчёта средней цены за м² по городу и комнатам
- Вычисления процента выгоды объявления
- Поиска объявлений с ценой ниже рыночной

Использует Redis кэширование для агрегированных данных.
"""
import redis.asyncio as redis
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple
from loguru import logger

from app.models.listing import Listing, ListingStatus
from app.core.redis_client import get_redis
from app.decorators.cache import _generate_cache_key, _get_from_cache, _set_to_cache
from app.config import settings


# Константы для валидации
VALID_CITIES = ["minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"]
VALID_STATUSES = [
    ListingStatus.active,
    ListingStatus.new,
    ListingStatus.updated,
    ListingStatus.price_changed_byn,
]
MAX_DISCOUNT_PERCENT = 50.0


class DealFinderService:
    """
    Сервис для поиска выгодных предложений недвижимости.
    
    Вычисляет среднюю цену за м² для аналогичных квартир и определяет
    процент отклонения текущей цены от средней.
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
        """Получить Redis клиент с кэшированием."""
        if self._redis is None:
            try:
                self._redis = await get_redis()
            except Exception as e:
                logger.warning(f"Failed to get Redis connection: {e}")
                return None
        return self._redis
    
    async def get_avg_price_per_m2(
        self,
        city: str,
        rooms: Optional[int] = None,
        currency: str = "usd"
    ) -> Optional[float]:
        """
        Получить среднюю цену за м² для указанных параметров.
        
        Использует Redis кэширование (TTL 300 сек) для ускорения повторных запросов.
        
        Args:
            city: Город (minsk, mogilev, grodno, brest, gomel, vitebsk)
            rooms: Количество комнат (опционально)
            currency: Валюта для расчёта (byn или usd)
        
        Returns:
            Средняя цена за м² или None если нет данных
        
        Raises:
            ValueError: Если город некорректный
        """
        # Валидация города
        city = city.lower()
        if city not in VALID_CITIES:
            raise ValueError(f"Некорректный город: {city}. Допустимые: {VALID_CITIES}")
        
        # Валидация валюты
        currency = currency.lower()
        if currency not in ["byn", "usd"]:
            raise ValueError(f"Некорректная валюта: {currency}. Допустимые: byn, usd")
        
        # Валидация комнат
        if rooms is not None and (rooms < 1 or rooms > 10):
            raise ValueError(f"Количество комнат должно быть от 1 до 10, получено: {rooms}")
        
        # Формируем ключ кэша
        cache_key = _generate_cache_key(
            prefix="cache:avg_price_m2",
            endpoint="get",
            params={"city": city, "rooms": rooms, "currency": currency},
            key_params=["city", "rooms", "currency"]
        )
        
        # Попытка получить из кэша
        redis_client = await self._get_redis()
        if redis_client:
            cached = await _get_from_cache(redis_client, cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for avg_price_per_m2: {cache_key}")
                return float(cached)
        
        logger.debug(f"Cache miss for avg_price_per_m2: {cache_key}, querying database")
        
        # Выбираем колонку цены в зависимости от валюты
        price_col = (
            Listing.price_per_m2_byn if currency == "byn" else Listing.price_per_m2_usd
        )
        
        # Базовые фильтры
        filters = [
            price_col.isnot(None),
            Listing.city == city,
            Listing.status.in_(VALID_STATUSES),
        ]
        
        if rooms is not None:
            filters.append(Listing.rooms == rooms)
        
        # SQL агрегация: AVG(price_per_m2)
        query = select(func.avg(price_col)).where(*filters)
        
        result = await self.db.execute(query)
        avg_price = result.scalar()
        
        if avg_price is None:
            logger.warning(f"No data for avg_price_per_m2: city={city}, rooms={rooms}, currency={currency}")
            return None
        
        avg_price_float = float(avg_price)
        
        # Сохраняем в кэш
        if redis_client:
            await _set_to_cache(redis_client, cache_key, avg_price_float, ttl=300)
            logger.debug(f"Cached avg_price_per_m2: {cache_key} = {avg_price_float}")
        
        return avg_price_float
    
    def calculate_deal_percent(
        self,
        current_price_per_m2: float,
        avg_price_per_m2: float
    ) -> float:
        """
        Вычислить процент выгоды объявления.
        
        Формула: ((current_price - avg_price) / avg_price) * 100
        
        Отрицательное значение означает, что цена ниже средней (выгодное предложение).
        Положительное значение означает, что цена выше средней.
        
        Args:
            current_price_per_m2: Цена за м² данного объявления
            avg_price_per_m2: Средняя цена за м² по рынку
        
        Returns:
            Процент выгоды (округлённый до 2 знаков)
        
        Example:
            >>> calculate_deal_percent(800, 1000)
            -20.0  # На 20% ниже рынка
            >>> calculate_deal_percent(1200, 1000)
            20.0  # На 20% выше рынка
        """
        if avg_price_per_m2 == 0:
            return 0.0
        
        deal_percent = ((current_price_per_m2 - avg_price_per_m2) / avg_price_per_m2) * 100
        return round(deal_percent, 2)
    
    async def get_deal_listings(
        self,
        city: str,
        rooms: Optional[int] = None,
        discount_percent: float = 10.0,
        currency: str = "usd",
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Listing], float, int]:
        """
        Получить список выгодных предложений.
        
        Находит объявления, цена за м² которых ниже средней на discount_percent процентов.
        
        Args:
            city: Город для поиска
            rooms: Количество комнат (опционально)
            discount_percent: Минимальный процент выгоды (0-50%)
            currency: Валюта для расчётов (byn или usd)
            limit: Максимальное количество результатов (1-100)
            offset: Смещение для пагинации
        
        Returns:
            Кортеж (список объявлений, средняя цена за м², общее количество)
        
        Raises:
            ValueError: Если параметры некорректны
        """
        # Валидация параметров
        city = city.lower()
        if city not in VALID_CITIES:
            raise ValueError(f"Некорректный город: {city}. Допустимые: {VALID_CITIES}")
        
        if discount_percent < 0 or discount_percent > MAX_DISCOUNT_PERCENT:
            raise ValueError(
                f"discount_percent должен быть от 0 до {MAX_DISCOUNT_PERCENT}, "
                f"получено: {discount_percent}"
            )
        
        currency = currency.lower()
        if currency not in ["byn", "usd"]:
            raise ValueError(f"Некорректная валюта: {currency}. Допустимые: byn, usd")
        
        if rooms is not None and (rooms < 1 or rooms > 10):
            raise ValueError(f"Количество комнат должно быть от 1 до 10, получено: {rooms}")
        
        if limit < 1 or limit > 100:
            raise ValueError(f"limit должен быть от 1 до 100, получено: {limit}")
        
        if offset < 0:
            raise ValueError(f"offset должен быть >= 0, получено: {offset}")
        
        # Получаем среднюю цену за м²
        avg_price_per_m2 = await self.get_avg_price_per_m2(
            city=city,
            rooms=rooms,
            currency=currency
        )
        
        if avg_price_per_m2 is None:
            logger.warning(f"No data for deals: city={city}, rooms={rooms}")
            return [], 0.0, 0
        
        # Выбираем колонку цены в зависимости от валюты
        price_col = (
            Listing.price_per_m2_byn if currency == "byn" else Listing.price_per_m2_usd
        )
        
        # Вычисляем максимальную цену за м² для выгодных предложений
        # Например, если avg=1000 и discount=10%, то max_price = 1000 * (1 - 0.10) = 900
        max_price_per_m2 = avg_price_per_m2 * (1 - discount_percent / 100)
        
        logger.info(
            f"Searching for deals: city={city}, rooms={rooms}, "
            f"avg_price={avg_price_per_m2}, max_price={max_price_per_m2}, "
            f"discount={discount_percent}%"
        )
        
        # Базовые фильтры
        filters = [
            price_col.isnot(None),
            price_col <= max_price_per_m2,  # Цена ниже порога
            Listing.city == city,
            Listing.status.in_(VALID_STATUSES),
        ]
        
        if rooms is not None:
            filters.append(Listing.rooms == rooms)
        
        # Считаем общее количество
        count_query = select(func.count(Listing.id)).where(*filters)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Получаем объявления, отсортированные по выгоде (сначала самые выгодные)
        query = (
            select(Listing)
            .where(*filters)
            .order_by(price_col.asc())  # Сначала самые дешёвые (самые выгодные)
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        listings = result.scalars().all()
        
        logger.info(f"Found {len(listings)} deals out of {total} total")
        
        return listings, avg_price_per_m2, total
    
    async def get_listing_deal_metrics(
        self,
        listing: Listing,
        currency: str = "usd"
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Получить метрики выгоды для отдельного объявления.
        
        Args:
            listing: Объект объявления
            currency: Валюта для расчёта (byn или usd)
        
        Returns:
            Кортеж (deal_percent, avg_price_per_m2) или (None, None) если нет данных
        """
        if not listing.city:
            return None, None
        
        # Получаем цену за м² объявления
        price_per_m2 = (
            float(listing.price_per_m2_byn) if currency == "byn" 
            else float(listing.price_per_m2_usd) if listing.price_per_m2_usd 
            else None
        )
        
        if price_per_m2 is None:
            return None, None
        
        # Получаем среднюю цену за м²
        avg_price_per_m2 = await self.get_avg_price_per_m2(
            city=listing.city,
            rooms=listing.rooms,
            currency=currency
        )
        
        if avg_price_per_m2 is None:
            return None, None
        
        # Вычисляем процент выгоды
        deal_percent = self.calculate_deal_percent(price_per_m2, avg_price_per_m2)
        
        return deal_percent, avg_price_per_m2


# Singleton instance для использования вне контекста запроса
_service_instance: Optional[DealFinderService] = None


def get_deal_finder_service(db: AsyncSession) -> DealFinderService:
    """
    Получить экземпляр DealFinderService.
    
    Args:
        db: Асинхронная сессия базы данных
    
    Returns:
        Экземпляр сервиса
    """
    return DealFinderService(db)
