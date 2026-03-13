"""
Service layer для управления избранными объявлениями (Favorites).

Предоставляет функции для добавления, удаления, получения и проверки статуса избранных объявлений.
Использует Redis для кэширования списков избранных объявлений.

Пример использования:
    from app.services.favorites_service import FavoritesService

    async with AsyncSession() as session:
        service = FavoritesService(session)
        favorite = await service.add_to_favorites(user_id, listing_id)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from loguru import logger
import redis.asyncio as redis
import json

from app.models.favorite import Favorite
from app.models.listing import Listing
from app.core.redis_client import get_redis
from app.config import settings

# TTL для кэша избранных объявлений (5 минут)
FAVORITES_CACHE_TTL = 300


class FavoritesService:
    """
    Сервис для управления избранными объявлениями.

    Предоставляет CRUD операции для избранных объявлений с Redis кэшированием.

    Attributes:
        db: Асинхронная сессия базы данных
        redis_client: Redis клиент для кэширования
    """

    def __init__(self, db: AsyncSession):
        """
        Инициализирует сервис.

        Args:
            db: Асинхронная сессия базы данных
        """
        self.db = db
        self._redis_client: Optional[redis.Redis] = None

    async def _get_redis(self) -> Optional[redis.Redis]:
        """
        Получает Redis клиент (lazy initialization).

        Returns:
            Redis клиент или None если Redis недоступен
        """
        if self._redis_client is None:
            try:
                self._redis_client = await get_redis()
            except Exception as e:
                logger.warning(f"Failed to get Redis connection: {e}")
                self._redis_client = None
        return self._redis_client

    def _get_cache_key(self, user_id: UUID, page: int = 1, size: int = 20) -> str:
        """
        Генерирует ключ кэша для пользователя с учётом пагинации.

        Args:
            user_id: UUID пользователя
            page: Номер страницы
            size: Размер страницы

        Returns:
            Строка ключа кэша
        """
        return f"cache:favorites:{user_id}:{page}:{size}"

    def _serialize_favorite(self, favorite: Favorite) -> Dict[str, Any]:
        """
        Сериализует объект Favorite в JSON-совместимый dict.

        Args:
            favorite: Объект Favorite для сериализации

        Returns:
            Dict с сериализованными данными
        """
        listing = favorite.listing if hasattr(favorite, "listing") else None

        return {
            "id": str(favorite.id),
            "user_id": str(favorite.user_id),
            "listing_id": str(favorite.listing_id),
            "created_at": (
                favorite.created_at.isoformat() if favorite.created_at else None
            ),
            "listing": (
                {
                    "id": str(listing.id),
                    "kufar_id": listing.kufar_id,
                    "url": listing.url,
                    "title": listing.title,
                    "price": float(listing.price) if listing.price else None,
                    "price_usd": (
                        float(listing.price_usd) if listing.price_usd else None
                    ),
                    "currency": listing.currency,
                    "city": listing.city,
                    "address": listing.address,
                    "rooms": listing.rooms,
                    "area": float(listing.area) if listing.area else None,
                    "floor": listing.floor,
                    "images": listing.images,
                    "status": listing.status,
                    "first_seen_at": (
                        listing.first_seen_at.isoformat()
                        if listing.first_seen_at
                        else None
                    ),
                    "last_seen_at": (
                        listing.last_seen_at.isoformat()
                        if listing.last_seen_at
                        else None
                    ),
                }
                if listing
                else None
            ),
        }

    def _deserialize_favorites(self, cached_data: Any) -> List[Favorite]:
        """
        Десериализует JSON данные обратно в список объектов Favorite.

        Args:
            cached_data: JSON данные из кэша

        Returns:
            Список объектов Favorite
        """
        favorites = []
        for item in cached_data:
            listing_data = item.get("listing")
            listing = None

            if listing_data:
                listing = Listing(
                    id=UUID(listing_data["id"]),
                    kufar_id=listing_data["kufar_id"],
                    url=listing_data["url"],
                    title=listing_data["title"],
                    price=listing_data["price"],
                    price_usd=listing_data["price_usd"],
                    currency=listing_data["currency"],
                    city=listing_data["city"],
                    address=listing_data["address"],
                    rooms=listing_data["rooms"],
                    area=listing_data["area"],
                    floor=listing_data["floor"],
                    images=listing_data.get("images"),
                    status=listing_data["status"],
                    first_seen_at=(
                        datetime.fromisoformat(listing_data["first_seen_at"])
                        if listing_data.get("first_seen_at")
                        else None
                    ),
                    last_seen_at=(
                        datetime.fromisoformat(listing_data["last_seen_at"])
                        if listing_data.get("last_seen_at")
                        else None
                    ),
                )

            favorite = Favorite(
                id=UUID(item["id"]),
                user_id=UUID(item["user_id"]),
                listing_id=UUID(item["listing_id"]),
                created_at=(
                    datetime.fromisoformat(item["created_at"])
                    if item.get("created_at")
                    else None
                ),
                listing=listing,
            )
            favorites.append(favorite)

        return favorites

    async def _invalidate_cache(self, user_id: UUID) -> None:
        """
        Инвалидирует кэш избранных объявлений пользователя.

        Args:
            user_id: UUID пользователя
        """
        try:
            redis_client = await self._get_redis()
            if redis_client:
                cache_key = self._get_cache_key(user_id)
                await redis_client.delete(cache_key)
                logger.debug(f"Invalidated favorites cache for user {user_id}")
        except Exception as e:
            logger.error(f"Error invalidating favorites cache: {e}")

    async def add_to_favorites(self, user_id: UUID, listing_id: UUID) -> Favorite:
        """
        Добавляет объявление в избранное.

        Если объявление уже в избранном, возвращает существующую запись (idempotent).

        Args:
            user_id: UUID пользователя
            listing_id: UUID объявления

        Returns:
            Объект Favorite (новый или существующий)

        Raises:
            SQLAlchemyError: При ошибке базы данных
            ValueError: Если объявление не найдено
        """
        # Проверяем существование объявления
        listing = await self.db.get(Listing, listing_id)
        if not listing:
            logger.warning(f"Listing {listing_id} not found for adding to favorites")
            raise ValueError(f"Listing with id {listing_id} not found")

        # Проверяем существует ли уже запись
        existing = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.listing_id == listing_id
            )
        )
        favorite = existing.scalar_one_or_none()

        if favorite:
            logger.debug(
                f"Favorite already exists for user {user_id}, listing {listing_id}"
            )
            return favorite

        # Создаём новую запись
        favorite = Favorite(user_id=user_id, listing_id=listing_id)
        self.db.add(favorite)

        try:
            await self.db.commit()
            await self.db.refresh(favorite)
            logger.info(f"Added listing {listing_id} to favorites for user {user_id}")

            # Инвалидируем кэш
            await self._invalidate_cache(user_id)

            return favorite
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error adding to favorites: {e}")
            raise

    async def remove_from_favorites(self, user_id: UUID, listing_id: UUID) -> bool:
        """
        Удаляет объявление из избранного.

        Если записи нет, возвращает False (idempotent).

        Args:
            user_id: UUID пользователя
            listing_id: UUID объявления

        Returns:
            True если запись была удалена, False если записи не было
        """
        # Проверяем существует ли запись
        existing = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.listing_id == listing_id
            )
        )
        favorite = existing.scalar_one_or_none()

        if not favorite:
            logger.debug(f"Favorite not found for user {user_id}, listing {listing_id}")
            return False

        # Удаляем запись через execute с delete() construct
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(Favorite).where(
            Favorite.user_id == user_id, Favorite.listing_id == listing_id
        )
        await self.db.execute(stmt)

        try:
            await self.db.commit()
            logger.info(
                f"Removed listing {listing_id} from favorites for user {user_id}"
            )

            # Инвалидируем кэш
            await self._invalidate_cache(user_id)

            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error removing from favorites: {e}")
            raise

    async def get_favorites(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        city: Optional[str] = None,
        price_from: Optional[int] = None,
        price_to: Optional[int] = None,
        rooms: Optional[List[int]] = None,
        rooms_other: Optional[bool] = None,
        sort: Optional[str] = None,
    ) -> Tuple[List[Favorite], int]:
        """
        Получает список избранных объявлений пользователя с пагинацией и фильтрами.

        Использует Redis кэш для ускорения повторных запросов.
        Кэш записывается с TTL = FAVORITES_CACHE_TTL (300 секунд).

        Args:
            user_id: UUID пользователя
            page: Номер страницы (1-based)
            size: Размер страницы (максимум 100)
            city: Город для фильтрации
            price_from: Минимальная цена
            price_to: Максимальная цена
            rooms: Список количества комнат
            rooms_other: Включить 5+ комнат
            sort: Сортировка ('created_at_desc', 'created_at_asc', 'price_asc', 'price_desc', 'newest', 'oldest')

        Returns:
            Кортеж (список объектов Favorite, общее количество)
        """
        # Ограничиваем размер страницы
        size = min(size, 100)
        offset = (page - 1) * size

        # Базовый запрос с join listing
        base_query = (
            select(Favorite)
            .options(selectinload(Favorite.listing))
            .join(Listing, Favorite.listing_id == Listing.id)
            .where(Favorite.user_id == user_id)
        )

        # Применяем фильтры
        if city:
            base_query = base_query.where(Listing.city == city)

        if price_from is not None:
            base_query = base_query.where(Listing.price_usd >= price_from)

        if price_to is not None:
            base_query = base_query.where(Listing.price_usd <= price_to)

        if rooms:
            base_query = base_query.where(Listing.rooms.in_(rooms))

        if rooms_other:
            base_query = base_query.where(Listing.rooms >= 5)

        # Применяем сортировку
        if sort == "created_at_asc":
            base_query = base_query.order_by(Favorite.created_at.asc())
        elif sort == "price_asc":
            base_query = base_query.order_by(Listing.price_usd.asc())
        elif sort == "price_desc":
            base_query = base_query.order_by(Listing.price_usd.desc())
        elif sort == "newest":
            base_query = base_query.order_by(Listing.first_seen_at.desc())
        elif sort == "oldest":
            base_query = base_query.order_by(Listing.first_seen_at.asc())
        else:  # created_at_desc (default)
            base_query = base_query.order_by(Favorite.created_at.desc())

        # Получаем общее количество с фильтрами
        count_query = (
            select(func.count(Favorite.id))
            .join(Listing, Favorite.listing_id == Listing.id)
            .where(Favorite.user_id == user_id)
        )

        if city:
            count_query = count_query.where(Listing.city == city)
        if price_from is not None:
            count_query = count_query.where(Listing.price_usd >= price_from)
        if price_to is not None:
            count_query = count_query.where(Listing.price_usd <= price_to)
        if rooms:
            count_query = count_query.where(Listing.rooms.in_(rooms))
        if rooms_other:
            count_query = count_query.where(Listing.rooms >= 5)

        # Получаем Redis клиент для кэширования
        redis_client = await self._get_redis()

        # Проверяем кэш (если Redis доступен)
        if redis_client:
            cache_key = self._get_cache_key(user_id, page, size)
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    logger.debug(
                        f"Cache hit for user {user_id}, page {page}, size {size}"
                    )
                    # Десериализуем данные из кэша
                    data = json.loads(cached_data)
                    favorites = [self._deserialize_favorite(item) for item in data]

                    # Получаем total из кэша или БД
                    total_cached = await redis_client.get(f"{cache_key}:total")
                    if total_cached:
                        total = int(total_cached)
                    else:
                        total_result = await self.db.execute(count_query)
                        total = total_result.scalar() or 0

                    return favorites, total
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

        # Получаем общее количество с фильтрами (cache miss)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Применяем пагинацию
        query = base_query.offset(offset).limit(size)
        result = await self.db.execute(query)
        favorites = result.scalars().all()

        # Записываем в кэш (если Redis доступен и есть данные)
        if redis_client and favorites:
            cache_key = self._get_cache_key(user_id, page, size)
            try:
                serialized = [self._serialize_favorite(fav) for fav in favorites]
                await redis_client.setex(
                    cache_key, FAVORITES_CACHE_TTL, json.dumps(serialized)
                )
                # Кэшируем total отдельно
                await redis_client.setex(
                    f"{cache_key}:total", FAVORITES_CACHE_TTL, str(total)
                )
                logger.debug(f"Cached {len(favorites)} favorites for user {user_id}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")

        logger.debug(
            f"Retrieved {len(favorites)} favorites for user {user_id} "
            f"(page {page}, size {size}, city={city}, rooms={rooms})"
        )

        return list(favorites), total

    async def is_favorite(self, user_id: UUID, listing_id: UUID) -> bool:
        """
        Проверяет, находится ли объявление в избранном.

        Args:
            user_id: UUID пользователя
            listing_id: UUID объявления

        Returns:
            True если объявление в избранном, иначе False
        """
        result = await self.db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.listing_id == listing_id
            )
        )
        favorite = result.scalar_one_or_none()

        is_fav = favorite is not None
        logger.debug(
            f"Favorite check for user {user_id}, listing {listing_id}: {is_fav}"
        )
        return is_fav

    async def clear_user_favorites_cache(self, user_id: UUID) -> None:
        """
        Принудительно очищает кэш избранных объявлений пользователя.

        Вызывается при добавлении/удалении объявлений из избранного.

        Args:
            user_id: UUID пользователя
        """
        await self._invalidate_cache(user_id)

    async def get_favorite_by_listing(
        self, user_id: UUID, listing_id: UUID
    ) -> Optional[Favorite]:
        """
        Получает запись об избранном объявлении.

        Args:
            user_id: UUID пользователя
            listing_id: UUID объявления

        Returns:
            Объект Favorite или None если не найдено
        """
        result = await self.db.execute(
            select(Favorite)
            .options(selectinload(Favorite.listing))
            .where(Favorite.user_id == user_id, Favorite.listing_id == listing_id)
        )
        return result.scalar_one_or_none()
