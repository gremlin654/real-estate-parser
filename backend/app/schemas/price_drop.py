"""
Pydantic схемы для Price Drop Tracker.

Схемы для API endpoints:
- GET /api/v1/price-drops — список объявлений с падением цены
- GET /api/v1/listings/{id}/price-history — история цен объявления
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PriceDropListing(BaseModel):
    """
    Объявление с информацией о падении цены.

    Attributes:
        id: UUID объявления
        kufar_id: ID объявления на Kufar
        url: Ссылка на объявление
        title: Заголовок
        price: Цена в BYN
        price_usd: Цена в USD
        current_price: Текущая цена (в зависимости от валюты)
        max_price: Максимальная цена за историю наблюдений
        min_price: Минимальная цена за историю наблюдений
        drop_percent: Процент падения цены
        city: Город
        rooms: Количество комнат
        area: Площадь
        floor: Этаж
        images: Список изображений
        status: Статус объявления
        first_seen_at: Дата первого обнаружения
        last_seen_at: Дата последнего обнаружения
    """

    id: UUID
    kufar_id: str
    url: str
    title: str
    price: int  # Цена в BYN для совместимости с Listing
    price_usd: int  # Цена в USD для совместимости с Listing
    current_price: int  # Текущая цена (alias для price или price_usd)
    max_price: int
    min_price: int
    drop_percent: float = Field(..., ge=0, le=100, description="Процент падения цены")
    city: Optional[str] = None
    rooms: Optional[int] = None
    area: Optional[float] = None
    floor: Optional[int] = None
    images: List[str] = Field(default_factory=list)
    status: str
    first_seen_at: datetime
    last_seen_at: datetime

    class Config:
        from_attributes = True


class PriceDropHistoryItem(BaseModel):
    """
    Элемент истории изменения цены.

    Attributes:
        id: UUID записи истории
        event_type: Тип события (price_changed, price_changed_byn)
        price_before: Цена до изменения
        price_after: Цена после изменения
        created_at: Дата изменения
    """

    id: UUID
    event_type: str
    price_before: Optional[int] = None
    price_after: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PriceDropResponse(BaseModel):
    """
    Ответ API для списка объявлений с падением цены.

    Attributes:
        items: Список объявлений с падением цены
        total: Общее количество объявлений
        avg_drop_percent: Средний процент падения
        max_drop_percent: Максимальный процент падения
        min_drop_percent: Минимальный процент падения
        currency: Валюта (BYN/USD)
        page: Текущая страница
        size: Размер страницы
    """

    items: List[PriceDropListing]
    total: int
    avg_drop_percent: Optional[float] = None
    max_drop_percent: Optional[float] = None
    min_drop_percent: Optional[float] = None
    currency: str = "USD"
    page: int
    size: int


class PriceDropHistoryResponse(BaseModel):
    """
    Ответ API для истории цен объявления.

    Attributes:
        items: Список изменений цены
        first_price: Первая зафиксированная цена
        last_price: Последняя зафиксированная цена
        total_drop_percent: Общий процент падения цены
        currency: Валюта (BYN/USD)
    """

    items: List[PriceDropHistoryItem]
    first_price: Optional[int] = None
    last_price: Optional[int] = None
    total_drop_percent: Optional[float] = None
    currency: str = "USD"


class PriceDropStats(BaseModel):
    """
    Статистика падения цен по городу.

    Attributes:
        total_drops: Общее количество объявлений с падением цены
        avg_drop_percent: Средний процент падения
        max_drop_percent: Максимальный процент падения
        min_drop_percent: Минимальный процент падения
        currency: Валюта (BYN/USD)
    """

    total_drops: int
    avg_drop_percent: Optional[float] = None
    max_drop_percent: Optional[float] = None
    min_drop_percent: Optional[float] = None
    currency: str = "USD"


class PriceDropListingWithMetrics(PriceDropListing):
    """
    Расширенное объявление с метриками выгоды (для совместимости с Deal Finder).

    Attributes:
        deal_percent: Процент выгоды относительно средней цены
        avg_price_per_m2: Средняя цена за м² по городу/комнатам
    """

    deal_percent: Optional[float] = None
    avg_price_per_m2: Optional[float] = None


# Схемы для валидации query параметров
class PriceDropQueryParams(BaseModel):
    """
    Параметры запроса для Price Drop API.

    Attributes:
        city: Город для фильтрации
        drop_percent: Минимальный процент падения (0-100)
        currency: Валюта (byn/usd)
        limit: Количество результатов (1-100)
        offset: Смещение для пагинации
    """

    city: str
    drop_percent: float = Field(default=10.0, ge=0, le=100)
    currency: str = Field(default="usd")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.lower() not in ("byn", "usd"):
            raise ValueError("currency must be 'byn' or 'usd'")
        return v.lower()

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        valid_cities = {
            "minsk",
            "mogilev",
            "grodno",
            "brest",
            "gomel",
            "vitebsk",
        }
        if v.lower() not in valid_cities:
            raise ValueError(f"city must be one of: {', '.join(valid_cities)}")
        return v.lower()
