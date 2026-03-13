"""
Favorites API - управление избранными объявлениями.

Endpoints для добавления, удаления и получения списка избранных объявлений.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from loguru import logger

from app.db.database import get_db
from app.services.favorites_service import FavoritesService
from app.schemas.favorites import (
    FavoriteResponse,
    FavoritesListResponse,
    FavoriteCheckResponse,
)
from app.models.listing import Listing

router = APIRouter(prefix="/favorites", tags=["favorites"])


# Заглушка для user_id (session-based, пока без реальной аутентификации)
# В будущем заменить на реальную систему аутентификации
DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


def get_user_id() -> UUID:
    """
    Получает ID текущего пользователя.

    Пока возвращает заглушку для session-based пользователей.
    В будущем будет извлекать из JWT токена или сессии.

    Returns:
        UUID пользователя
    """
    return DEFAULT_USER_ID


def get_favorites_service(db: AsyncSession = Depends(get_db)) -> FavoritesService:
    """
    Создаёт экземпляр FavoritesService.

    Args:
        db: Асинхронная сессия базы данных

    Returns:
        Экземпляр FavoritesService
    """
    return FavoritesService(db)


async def validate_listing_exists(listing_id: UUID, db: AsyncSession) -> Listing:
    """
    Проверяет существование объявления.

    Args:
        listing_id: UUID объявления
        db: Асинхронная сессия базы данных

    Raises:
        HTTPException: Если объявление не найдено (404)

    Returns:
        Объект Listing
    """
    listing = await db.get(Listing, listing_id)
    if not listing:
        logger.warning(f"Listing {listing_id} not found for favorites operation")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with id {listing_id} not found",
        )
    return listing


@router.get("", response_model=FavoritesListResponse)
async def get_favorites(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    city: Optional[str] = Query(None, description="Город для фильтрации"),
    price_from: Optional[int] = Query(None, ge=0, description="Минимальная цена"),
    price_to: Optional[int] = Query(None, ge=0, description="Максимальная цена"),
    rooms: Optional[List[int]] = Query(None, description="Количество комнат"),
    rooms_other: Optional[bool] = Query(False, description="Включить 5+ комнат"),
    sort: Optional[str] = Query(
        None,
        description="Сортировка: created_at_desc, created_at_asc, price_asc, price_desc, newest, oldest",
    ),
    user_id: UUID = Depends(get_user_id),
    service: FavoritesService = Depends(get_favorites_service),
):
    """
    Получить список избранных объявлений пользователя.

    Возвращает пагинированный список избранных объявлений с данными объявлений.

    Параметры фильтрации:
    - **city**: Город для фильтрации (minsk, mogilev, grodno, brest, gomel, vitebsk)
    - **price_from**: Минимальная цена
    - **price_to**: Максимальная цена
    - **rooms**: Количество комнат (можно указать несколько)
    - **rooms_other**: Включить объявления с 5+ комнатами
    - **sort**: Сортировка (created_at_desc, created_at_asc, price_asc, price_desc, newest, oldest)

    - **page**: Номер страницы (1-based, по умолчанию 1)
    - **size**: Размер страницы (1-100, по умолчанию 20)

    Response включает:
    - items: Список избранных объявлений
    - total: Общее количество избранных объявлений
    - page: Текущая страница
    - size: Размер страницы
    """
    logger.info(
        f"Getting favorites for user {user_id} (page={page}, size={size}, "
        f"city={city}, price_from={price_from}, price_to={price_to}, rooms={rooms}, sort={sort})"
    )

    try:
        favorites, total = await service.get_favorites(
            user_id=user_id,
            page=page,
            size=size,
            city=city,
            price_from=price_from,
            price_to=price_to,
            rooms=rooms,
            rooms_other=rooms_other,
            sort=sort,
        )

        # Конвертируем в response schema
        items = [
            FavoriteResponse(
                id=fav.id,
                user_id=fav.user_id,
                listing_id=fav.listing_id,
                created_at=fav.created_at,
                listing=fav.listing,
            )
            for fav in favorites
        ]

        logger.info(f"Retrieved {len(items)} favorites (total={total})")

        return FavoritesListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
        )
    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving favorites: {str(e)}",
        )


@router.post("/{listing_id}", response_model=FavoriteResponse)
async def add_to_favorites(
    listing_id: UUID,
    user_id: UUID = Depends(get_user_id),
    service: FavoritesService = Depends(get_favorites_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Добавить объявление в избранное.

    Idempotent операция: если объявление уже в избранном, возвращает 200 OK
    с существующей записью (не создаёт дубликат).

    - **listing_id**: UUID объявления для добавления в избранное
    """
    logger.info(f"Adding listing {listing_id} to favorites for user {user_id}")

    # Проверяем существование объявления
    await validate_listing_exists(listing_id, db)

    try:
        favorite = await service.add_to_favorites(
            user_id=user_id, listing_id=listing_id
        )

        logger.info(f"Added listing {listing_id} to favorites")

        return FavoriteResponse(
            id=favorite.id,
            user_id=favorite.user_id,
            listing_id=favorite.listing_id,
            created_at=favorite.created_at,
            listing=favorite.listing,
        )
    except ValueError as e:
        logger.warning(f"ValueError adding to favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error adding to favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding to favorites: {str(e)}",
        )


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    listing_id: UUID,
    user_id: UUID = Depends(get_user_id),
    service: FavoritesService = Depends(get_favorites_service),
):
    """
    Удалить объявление из избранного.

    Idempotent операция: если объявления нет в избранном, возвращает 204 No Content
    (не считается ошибкой).
    """
    logger.info(f"Removing listing {listing_id} from favorites for user {user_id}")

    try:
        removed = await service.remove_from_favorites(
            user_id=user_id, listing_id=listing_id
        )

        if removed:
            logger.info(f"Removed listing {listing_id} from favorites")
        else:
            logger.debug(f"Listing {listing_id} was not in favorites")

        # Всегда возвращаем 204 (idempotent)
        return None
    except Exception as e:
        logger.error(f"Error removing from favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing from favorites: {str(e)}",
        )


@router.get("/check/{listing_id}", response_model=FavoriteCheckResponse)
async def check_favorite(
    listing_id: UUID,
    user_id: UUID = Depends(get_user_id),
    service: FavoritesService = Depends(get_favorites_service),
):
    """
    Проверить, находится ли объявление в избранном.

    - **listing_id**: UUID объявления для проверки

    Response включает:
    - is_favorite: True если объявление в избранном, иначе False
    """
    logger.info(f"Checking if listing {listing_id} is favorite for user {user_id}")

    try:
        is_favorite = await service.is_favorite(user_id=user_id, listing_id=listing_id)

        logger.debug(f"Favorite check result: {is_favorite}")

        return FavoriteCheckResponse(is_favorite=is_favorite)
    except Exception as e:
        logger.error(f"Error checking favorite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking favorite status: {str(e)}",
        )
