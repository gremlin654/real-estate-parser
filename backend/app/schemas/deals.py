"""
Pydantic схемы для Deal Finder API.

Схемы для поиска выгодных предложений (квартир с ценой ниже рыночной).
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from app.schemas.listing import ListingBase


class DealFilters(BaseModel):
    """
    Фильтры для поиска выгодных предложений.

    Attributes:
        city: Город для поиска (minsk, mogilev, grodno, brest, gomel, vitebsk)
        rooms: Количество комнат (опционально)
        discount_percent: Минимальный процент выгоды (0-50%)
        currency: Валюта для расчётов (byn или usd)
        limit: Максимальное количество результатов (1-100)
        offset: Смещение для пагинации
    """

    city: str = Field(..., description="Город для поиска")
    rooms: Optional[int] = Field(None, ge=1, le=10, description="Количество комнат")
    discount_percent: float = Field(
        default=10.0, ge=0, le=50, description="Минимальный процент выгоды (0-50%)"
    )
    currency: str = Field(default="usd", description="Валюта (byn/usd)")
    limit: int = Field(default=20, ge=1, le=100, description="Максимум результатов")
    offset: int = Field(default=0, ge=0, description="Смещение")

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        """Валидация города."""
        valid_cities = ["minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"]
        if v.lower() not in valid_cities:
            raise ValueError(
                f"Некорректный город. Допустимые значения: {', '.join(valid_cities)}"
            )
        return v.lower()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Валидация валюты."""
        if v.lower() not in ["byn", "usd"]:
            raise ValueError("Валюта должна быть byn или usd")
        return v.lower()


class DealListing(ListingBase):
    """
    Объявление с информацией о выгоде.

    Наследуется от ListingBase, добавляет поля deal_percent и avg_price_per_m2.
    """

    id: UUID
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    deleted_at: Optional[datetime] = None

    # Поля Deal Finder
    deal_percent: Optional[float] = Field(
        None,
        description="Процент выгоды (отрицательное значение, например -15.5 означает 15.5% ниже рынка)",
    )
    avg_price_per_m2: Optional[float] = Field(
        None, description="Средняя цена за м² для аналогичных квартир"
    )

    class Config:
        from_attributes = True


class DealListingResponse(BaseModel):
    """
    Объявление в ответе Deal Finder.

    Включает основную информацию о квартире и метрики выгоды.
    """

    id: UUID
    kufar_id: str
    url: str
    title: str
    price: int
    price_usd: Optional[int] = None
    currency: str = "BYN"
    city: Optional[str] = None
    address: Optional[str] = None
    rooms: Optional[int] = None
    area: Optional[float] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    images: List[str] = Field(default_factory=list)

    # Price per m²
    price_per_m2_byn: Optional[float] = None
    price_per_m2_usd: Optional[float] = None

    # Deal metrics
    deal_percent: float = Field(
        ..., description="Процент выгоды (отрицательное значение, например -15.5)"
    )
    avg_price_per_m2: float = Field(
        ..., description="Средняя цена за м² для аналогичных квартир"
    )
    status: str
    first_seen_at: datetime
    last_seen_at: datetime

    class Config:
        from_attributes = True


class DealsResponse(BaseModel):
    """
    Ответ API Deals с пагинацией.

    Attributes:
        items: Список выгодных объявлений
        total: Общее количество найденных объявлений
        limit: Максимальное количество результатов в ответе
        offset: Смещение от начала
        avg_price_per_m2: Средняя цена за м² для выбранных фильтров
        currency: Валюта расчётов
    """

    items: List[DealListingResponse]
    total: int
    limit: int
    offset: int
    avg_price_per_m2: float = Field(..., description="Средняя цена за м²")
    currency: str = Field(..., description="Валюта расчётов (byn/usd)")


class DealMetrics(BaseModel):
    """
    Метрики выгоды для отдельного объявления.

    Используется для добавления deal_percent в обычный список объявлений.
    """

    deal_percent: Optional[float] = Field(
        None, description="Процент выгоды (отрицательное значение)"
    )
    avg_price_per_m2: Optional[float] = Field(
        None, description="Средняя цена за м² для аналогичных квартир"
    )


class StatsSummaryWithDealMetrics(BaseModel):
    """
    Расширенная сводная статистика с метриками Deal Finder.
    """

    new_today: int
    deleted_today: int
    price_changed_usd_today: int
    price_changed_byn_today: int
    active_total: int
    archived_total: int

    # Deal Finder metrics
    avg_price_per_m2_byn: Optional[float] = Field(
        None, description="Средняя цена за м² в BYN"
    )
    avg_price_per_m2_usd: Optional[float] = Field(
        None, description="Средняя цена за м² в USD"
    )
    avg_price_per_m2_by_rooms: Optional[dict] = Field(
        None, description="Средняя цена за м² по комнатам {rooms: price}"
    )
