"""
Price Drop Tracker API — endpoints для отслеживания падения цен.

Endpoints:
    GET /api/v1/price-drops — Список объявлений с падением цены
    GET /api/v1/price-drops/stats — Статистика падения цен по городу
    GET /api/v1/listings/{id}/price-history — История цен объявления
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from loguru import logger

from app.db.database import get_db
from app.services.price_drop_service import get_price_drop_service, PriceDropService
from app.schemas.price_drop import (
    PriceDropResponse,
    PriceDropHistoryResponse,
    PriceDropStats,
    PriceDropQueryParams,
)
from app.config import CITY_NAMES

router = APIRouter(prefix="/price-drops", tags=["price-drops"])


@router.get("", response_model=PriceDropResponse)
async def get_price_drops(
    request: Request,
    city: str = Query(
        ...,
        description="Город для фильтрации (minsk, mogilev, grodno, brest, gomel, vitebsk)",
    ),
    drop_percent: float = Query(
        10.0, ge=0, le=100, description="Минимальный процент падения (0-100)"
    ),
    currency: str = Query("usd", description="Валюта: byn или usd"),
    limit: int = Query(20, ge=1, le=100, description="Количество результатов (1-100)"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить список объявлений с падением цены.

    Возвращает объявления у которых зафиксировано падение цены на указанный процент.
    Расчёт drop_percent производится по формуле:
        ((MAX(price_before) - MIN(price_after)) / MAX(price_before)) * 100

    **Параметры:**
    - `city`: Город для фильтрации (обязательный)
    - `drop_percent`: Минимальный процент падения (по умолчанию 10%)
    - `currency`: Валюта для расчёта (USD или BYN, по умолчанию USD)
    - `limit`: Количество результатов (1-100, по умолчанию 20)
    - `offset`: Смещение для пагинации (по умолчанию 0)

    **Возвращает:**
    - `items`: Список объявлений с полями max_price, min_price, drop_percent
    - `total`: Общее количество объявлений
    - `avg_drop_percent`: Средний процент падения
    - `max_drop_percent`: Максимальный процент падения
    - `min_drop_percent`: Минимальный процент падения
    - `currency`: Использованная валюта
    - `page`: Текущая страница
    - `size`: Размер страницы

    **Пример:**
    ```bash
    curl "http://localhost:8000/api/v1/price-drops?city=minsk&drop_percent=10&currency=usd"
    ```
    """
    # Валидация города
    city_lower = city.lower()
    valid_cities = {"minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"}
    if city_lower not in valid_cities:
        raise HTTPException(
            status_code=422,
            detail=f"Неверный город. Допустимые значения: {', '.join(valid_cities)}",
        )

    # Валидация валюты
    currency_lower = currency.lower()
    if currency_lower not in ("byn", "usd"):
        raise HTTPException(
            status_code=422,
            detail="Неверная валюта. Допустимые значения: byn, usd",
        )

    logger.info(
        f"Price drops request: city={city_lower}, drop_percent={drop_percent}, "
        f"currency={currency_lower}, limit={limit}, offset={offset}"
    )

    try:
        service = get_price_drop_service(db)

        listings, avg_drop, max_drop, min_drop, total = (
            await service.get_price_drop_listings(
                city=city_lower,
                drop_percent=drop_percent,
                limit=limit,
                offset=offset,
                currency=currency_lower,
            )
        )

        logger.info(
            f"Price drops response: total={total}, returned={len(listings)}, "
            f"avg_drop={avg_drop}%, max_drop={max_drop}%"
        )

        return {
            "items": listings,
            "total": total,
            "avg_drop_percent": round(avg_drop, 2),
            "max_drop_percent": round(max_drop, 2),
            "min_drop_percent": round(min_drop, 2),
            "currency": currency_lower.upper(),
            "page": (offset // limit) + 1 if limit > 0 else 1,
            "size": limit,
        }

    except Exception as e:
        logger.error(f"Error getting price drops: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения данных: {str(e)}"
        )


@router.get("/stats", response_model=PriceDropStats)
async def get_price_drop_statistics(
    request: Request,
    city: str = Query(..., description="Город для фильтрации"),
    drop_percent: float = Query(
        10.0, ge=0, le=100, description="Минимальный процент падения"
    ),
    currency: str = Query("usd", description="Валюта: byn или usd"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить статистику падения цен по городу.

    **Параметры:**
    - `city`: Город для фильтрации (обязательный)
    - `drop_percent`: Минимальный процент падения (по умолчанию 10%)
    - `currency`: Валюта для расчёта (USD или BYN, по умолчанию USD)

    **Возвращает:**
    - `total_drops`: Общее количество объявлений с падением цены
    - `avg_drop_percent`: Средний процент падения
    - `max_drop_percent`: Максимальный процент падения
    - `min_drop_percent`: Минимальный процент падения
    - `currency`: Использованная валюта

    **Пример:**
    ```bash
    curl "http://localhost:8000/api/v1/price-drops/stats?city=minsk&drop_percent=10"
    ```
    """
    # Валидация города
    city_lower = city.lower()
    valid_cities = {"minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"}
    if city_lower not in valid_cities:
        raise HTTPException(
            status_code=422,
            detail=f"Неверный город. Допустимые значения: {', '.join(valid_cities)}",
        )

    # Валидация валюты
    currency_lower = currency.lower()
    if currency_lower not in ("byn", "usd"):
        raise HTTPException(
            status_code=422,
            detail="Неверная валюта. Допустимые значения: byn, usd",
        )

    logger.info(
        f"Price drop stats request: city={city_lower}, drop_percent={drop_percent}, "
        f"currency={currency_lower}"
    )

    try:
        service = get_price_drop_service(db)
        stats = await service.get_price_drop_stats(
            city=city_lower,
            drop_percent=drop_percent,
            currency=currency_lower,
        )

        logger.info(
            f"Price drop stats response: total={stats['total_drops']}, "
            f"avg={stats['avg_drop_percent']}%"
        )

        return stats

    except Exception as e:
        logger.error(f"Error getting price drop stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения статистики: {str(e)}"
        )


@router.get(
    "/listings/{listing_id}/price-history", response_model=PriceDropHistoryResponse
)
async def get_listing_price_history(
    listing_id: UUID,
    currency: str = Query("usd", description="Валюта: byn или usd"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить историю изменений цены для объявления.

    **Параметры:**
    - `listing_id`: UUID объявления (обязательный)
    - `currency`: Валюта для отображения (USD или BYN, по умолчанию USD)

    **Возвращает:**
    - `items`: Список изменений цены (event_type, price_before, price_after, created_at)
    - `first_price`: Первая зафиксированная цена
    - `last_price`: Последняя зафиксированная цена
    - `total_drop_percent`: Общий процент падения цены
    - `currency`: Использованная валюта

    **Пример:**
    ```bash
    curl "http://localhost:8000/api/v1/price-drops/listings/123e4567-e89b-12d3-a456-426614174000/price-history?currency=usd"
    ```
    """
    # Валидация валюты
    currency_lower = currency.lower()
    if currency_lower not in ("byn", "usd"):
        raise HTTPException(
            status_code=422,
            detail="Неверная валюта. Допустимые значения: byn, usd",
        )

    logger.info(
        f"Price history request: listing_id={listing_id}, currency={currency_lower}"
    )

    try:
        service = get_price_drop_service(db)

        items, first_price, last_price, total_drop_percent = (
            await service.get_listing_price_history(
                listing_id=listing_id,
                currency=currency_lower,
            )
        )

        logger.info(
            f"Price history response: listing_id={listing_id}, events={len(items)}, "
            f"drop={total_drop_percent}%"
        )

        return {
            "items": items,
            "first_price": first_price,
            "last_price": last_price,
            "total_drop_percent": (
                round(total_drop_percent, 2) if total_drop_percent else None
            ),
            "currency": currency_lower.upper(),
        }

    except Exception as e:
        logger.error(f"Error getting price history for listing {listing_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка получения истории: {str(e)}"
        )
