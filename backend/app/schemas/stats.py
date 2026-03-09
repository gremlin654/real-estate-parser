from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PricePerM2Stats(BaseModel):
    """Статистика цены за м²."""

    average: float = Field(..., description="Средняя цена за м²")
    median: float = Field(..., description="Медианная цена за м²")
    min: float = Field(..., description="Минимальная цена за м²")
    max: float = Field(..., description="Максимальная цена за м²")
    count: int = Field(..., description="Количество объявлений")
    currency: str = Field(..., description="Валюта (byn/usd)")


class PricePerM2Trend(BaseModel):
    """Тренд цены за м² по времени."""

    date: str = Field(..., description="Дата (YYYY-MM-DD)")
    average: float = Field(..., description="Средняя цена за м²")
    median: float = Field(..., description="Медианная цена за м²")
    count: int = Field(..., description="Количество объявлений")


class PricePerM2Distribution(BaseModel):
    """Распределение цены за м² (гистограмма)."""

    range_min: float = Field(..., description="Минимальная граница диапазона")
    range_max: float = Field(..., description="Максимальная граница диапазона")
    count: int = Field(..., description="Количество объявлений в диапазоне")
    percentage: float = Field(..., description="Процент от общего количества")


class PricePerM2StatsRequest(BaseModel):
    """Запрос статистики цены за м²."""

    city: str = Field(..., description="Город")
    rooms: Optional[int] = Field(None, ge=1, le=10, description="Количество комнат")
    date_from: Optional[datetime] = Field(None, description="Дата от")
    date_to: Optional[datetime] = Field(None, description="Дата до")
    currency: str = Field("usd", description="Валюта (byn/usd)")


class PricePerM2TrendsRequest(BaseModel):
    """Запрос трендов цены за м²."""

    city: str = Field(..., description="Город")
    rooms: Optional[int] = Field(None, ge=1, le=10, description="Количество комнат")
    period_days: int = Field(30, ge=1, le=365, description="Период в днях")
    interval: str = Field("day", description="Интервал группировки (day/week/month)")
    currency: str = Field("usd", description="Валюта (byn/usd)")


class PricePerM2DistributionRequest(BaseModel):
    """Запрос распределения цены за м²."""

    city: str = Field(..., description="Город")
    rooms: Optional[int] = Field(None, ge=1, le=10, description="Количество комнат")
    bins: int = Field(10, ge=5, le=50, description="Количество бинов")
    currency: str = Field("usd", description="Валюта (byn/usd)")
