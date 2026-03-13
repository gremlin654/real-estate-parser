"""
Pydantic schemas для избранных объявлений (Favorites).

Модуль содержит схемы для валидации запросов и ответов API связанных с избранными объявлениями.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.listing import ListingResponse


class FavoriteBase(BaseModel):
    """
    Базовая схема избранного объявления.

    Содержит основные поля записи об избранном объявлении.
    """

    user_id: UUID = Field(..., description="UUID пользователя (session-based)")
    listing_id: UUID = Field(..., description="UUID избранного объявления")


class FavoriteCreate(FavoriteBase):
    """
    Схема для создания записи об избранном объявлении.

    Используется для валидации запросов на добавление в избранное.
    """

    pass


class FavoriteResponse(BaseModel):
    """
    Схема ответа с данными об избранном объявлении.

    Содержит информацию о записи в избранном и данные объявления.
    """

    id: UUID = Field(..., description="UUID записи об избранном")
    user_id: UUID = Field(..., description="UUID пользователя")
    listing_id: UUID = Field(..., description="UUID избранного объявления")
    created_at: datetime = Field(..., description="Дата и время добавления в избранное")
    listing: ListingResponse = Field(..., description="Данные избранного объявления")

    class Config:
        from_attributes = True


class FavoritesListResponse(BaseModel):
    """
    Схема ответа для списка избранных объявлений с пагинацией.

    Используется для endpoint GET /api/v1/favorites.

    Attributes:
        items: Список записей об избранных объявлениях
        total: Общее количество избранных объявлений
        page: Текущая страница (1-based)
        size: Размер страницы
    """

    items: List[FavoriteResponse] = Field(
        ..., description="Список избранных объявлений"
    )
    total: int = Field(..., description="Общее количество избранных объявлений")
    page: int = Field(..., description="Текущая страница", ge=1)
    size: int = Field(..., description="Размер страницы", ge=1, le=100)


class FavoriteCheckResponse(BaseModel):
    """
    Схема ответа для проверки статуса избранного.

    Используется для endpoint GET /api/v1/favorites/check/{listing_id}.

    Attributes:
        is_favorite: True если объявление в избранном, иначе False
    """

    is_favorite: bool = Field(..., description="Статус избранного объявления")
