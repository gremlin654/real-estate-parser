"""
Pydantic схемы для Deal Score API.

Схемы для поиска объявлений по Deal Score и получения детализации скоринга.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class DealScoreBreakdown(BaseModel):
    """Детализация одного фактора Deal Score."""

    score: float = Field(..., ge=0, le=100, description="Score фактора (0-100)")
    weight: float = Field(..., ge=0, le=1, description="Вес фактора")
    weighted: float = Field(
        ..., ge=0, le=100, description="Взвешенный вклад (score * weight)"
    )


class DealScoreFullBreakdown(BaseModel):
    """Полная детализация Deal Score по всем факторам."""

    price_score: DealScoreBreakdown
    trend_score: DealScoreBreakdown
    liquidity_score: DealScoreBreakdown
    freshness_score: DealScoreBreakdown
    floor_score: DealScoreBreakdown
    bonus_score: DealScoreBreakdown


class DealScoreResponse(BaseModel):
    """Response для Deal Score."""

    deal_score: float = Field(..., ge=0, le=100, description="Deal Score (0-100)")
    deal_label: str = Field(
        ..., description="Текстовая метка (🔥 HOT, 👍 GOOD, 😐 NORMAL)"
    )
    breakdown: DealScoreFullBreakdown = Field(
        ..., description="Детализация по факторам"
    )


class DealListingWithScore(BaseModel):
    """Listing с Deal Score (для включения в response)."""

    id: UUID
    kufar_id: str
    url: str
    title: str
    price: int
    price_usd: Optional[int] = None
    price_per_m2_usd: Optional[float] = None
    city: Optional[str] = None
    rooms: Optional[int] = None
    area: Optional[float] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    address: Optional[str] = None
    status: str
    first_seen_at: datetime
    last_seen_at: datetime

    # Deal Score поля
    deal_score: Optional[float] = Field(
        None, ge=0, le=100, description="Deal Score (0-100)"
    )
    deal_label: Optional[str] = Field(None, description="Текстовая метка")

    class Config:
        from_attributes = True


class DealsScoreRequest(BaseModel):
    """Request параметры для поиска по Deal Score."""

    city: str = Field(..., description="Город (обязательно)")
    rooms: Optional[int] = Field(None, ge=1, le=5, description="Количество комнат")
    min_score: float = Field(70.0, ge=0, le=100, description="Минимальный Deal Score")
    currency: str = Field("usd", description="Валюта (usd/byn)")
    limit: int = Field(20, ge=1, le=100, description="Максимум результатов")
    offset: int = Field(0, ge=0, description="Смещение")

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
            raise ValueError("Валюта должна быть usd или byn")
        return v.lower()


class DealsScoreResponse(BaseModel):
    """Response для поиска по Deal Score."""

    items: List[DealListingWithScore]
    total: int
    avg_score: float = Field(..., description="Средний Deal Score")
    min_score_filter: float = Field(..., description="Применённый фильтр min_score")
    currency: str = Field(..., description="Валюта расчётов")
    limit: int
    offset: int


class DealScoreStatsResponse(BaseModel):
    """Response для статистики Deal Score."""

    city: str
    rooms: Optional[int] = None
    total_listings: int
    listings_with_score: int
    avg_score: float
    min_score: float
    max_score: float
    currency: str
