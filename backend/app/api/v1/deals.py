"""
Deal Finder API - поиск выгодных предложений недвижимости.

Endpoints для поиска квартир с ценой ниже рыночной.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from loguru import logger

from app.db.database import get_db
from app.services.deal_finder_service import get_deal_finder_service, DealFinderService
from app.schemas.deals import (
    DealFilters,
    DealListingResponse,
    DealsResponse,
)
from app.decorators.cache import cache_response
from app.config import settings

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=DealsResponse)
@cache_response(
    prefix="cache:deals",
    ttl=settings.CACHE_TTL_STATS_OTHER,  # 300 сек
    key_params=["city", "rooms", "discount_percent", "currency", "limit", "offset"],
)
async def get_deals(
    request: Request,
    city: str = Query(
        ...,
        description="Город для поиска (minsk, mogilev, grodno, brest, gomel, vitebsk)",
    ),
    rooms: Optional[int] = Query(
        None,
        ge=1,
        le=10,
        description="Количество комнат (опционально)",
    ),
    discount_percent: float = Query(
        default=10.0,
        ge=0,
        le=50,
        description="Минимальный процент выгоды (0-50%)",
    ),
    currency: str = Query(
        default="usd",
        description="Валюта для расчётов (byn или usd)",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Максимальное количество результатов",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Смещение для пагинации",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить список выгодных предложений недвижимости.

    Находит объявления, цена за м² которых ниже средней на указанный процент.

    - **city**: Город для поиска (обязательно)
    - **rooms**: Количество комнат (опционально)
    - **discount_percent**: Минимальная выгода в процентах (0-50%, по умолчанию 10%)
    - **currency**: Валюта для расчётов (byn или usd, по умолчанию usd)
    - **limit**: Максимум результатов (1-100, по умолчанию 20)
    - **offset**: Смещение для пагинации (по умолчанию 0)

    Response включает:
    - items: Список объявлений с метриками выгоды
    - total: Общее количество найденных объявлений
    - avg_price_per_m2: Средняя цена за м² для выбранных фильтров
    - currency: Валюта расчётов

    **Пример:**
    ```
    GET /api/v1/deals?city=minsk&rooms=2&discount_percent=15&currency=usd
    ```

    **Логирование:**
    Все запросы логируются с параметрами фильтрации.
    """
    # Логирование запроса
    logger.info(
        f"Deal Finder request: city={city}, rooms={rooms}, "
        f"discount_percent={discount_percent}%, currency={currency}, "
        f"limit={limit}, offset={offset}"
    )

    # Валидация города (дополнительная проверка на уровне сервиса)
    valid_cities = ["minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"]
    if city.lower() not in valid_cities:
        raise HTTPException(
            status_code=422,
            detail=f"Некорректный город. Допустимые значения: {', '.join(valid_cities)}",
        )

    # Валидация валюты
    if currency.lower() not in ["byn", "usd"]:
        raise HTTPException(
            status_code=422,
            detail="Валюта должна быть byn или usd",
        )

    try:
        # Получаем сервис
        service = get_deal_finder_service(db)

        # Получаем выгодные предложения
        listings, avg_price_per_m2, total = await service.get_deal_listings(
            city=city,
            rooms=rooms,
            discount_percent=discount_percent,
            currency=currency,
            limit=limit,
            offset=offset,
        )

        # Формируем ответ
        deal_items: List[DealListingResponse] = []

        for listing in listings:
            # Вычисляем deal_percent для каждого объявления
            price_per_m2 = (
                float(listing.price_per_m2_byn)
                if currency.lower() == "byn"
                else (
                    float(listing.price_per_m2_usd)
                    if listing.price_per_m2_usd
                    else avg_price_per_m2
                )
            )

            # Вычисляем процент выгоды
            if avg_price_per_m2 and price_per_m2:
                deal_percent = service.calculate_deal_percent(
                    price_per_m2, avg_price_per_m2
                )
            else:
                deal_percent = 0.0

            deal_items.append(
                DealListingResponse(
                    id=listing.id,
                    kufar_id=listing.kufar_id,
                    url=listing.url,
                    title=listing.title,
                    price=listing.price,
                    price_usd=listing.price_usd,
                    currency=listing.currency,
                    city=listing.city,
                    address=listing.address,
                    rooms=listing.rooms,
                    area=listing.area,
                    floor=listing.floor,
                    total_floors=listing.total_floors,
                    images=listing.images or [],
                    price_per_m2_byn=(
                        float(listing.price_per_m2_byn)
                        if listing.price_per_m2_byn
                        else None
                    ),
                    price_per_m2_usd=(
                        float(listing.price_per_m2_usd)
                        if listing.price_per_m2_usd
                        else None
                    ),
                    deal_percent=deal_percent,
                    avg_price_per_m2=avg_price_per_m2,
                    status=(
                        listing.status.value
                        if hasattr(listing.status, "value")
                        else str(listing.status)
                    ),
                    first_seen_at=listing.first_seen_at,
                    last_seen_at=listing.last_seen_at,
                )
            )

        logger.info(
            f"Deal Finder response: {len(deal_items)} items, "
            f"total={total}, avg_price_per_m2={avg_price_per_m2}"
        )

        return DealsResponse(
            items=deal_items,
            total=total,
            limit=limit,
            offset=offset,
            avg_price_per_m2=avg_price_per_m2 or 0.0,
            currency=currency.lower(),
        )

    except ValueError as e:
        logger.error(f"Deal Finder validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Deal Finder error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/stats")
@cache_response(
    prefix="cache:deals:stats",
    ttl=settings.CACHE_TTL_STATS_OTHER,  # 300 сек
    key_params=["city", "rooms", "currency"],
)
async def get_deals_stats(
    request: Request,
    city: str = Query(
        ...,
        description="Город для статистики",
    ),
    rooms: Optional[int] = Query(
        None,
        ge=1,
        le=10,
        description="Количество комнат (опционально)",
    ),
    currency: str = Query(
        default="usd",
        description="Валюта для расчётов (byn или usd)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить статистику для Deal Finder.

    Возвращает среднюю цену за м² и количество потенциально выгодных объявлений.

    - **city**: Город для статистики
    - **rooms**: Количество комнат (опционально)
    - **currency**: Валюта (byn или usd)
    """
    logger.info(
        f"Deal Finder stats request: city={city}, rooms={rooms}, currency={currency}"
    )

    # Валидация
    valid_cities = ["minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"]
    if city.lower() not in valid_cities:
        raise HTTPException(
            status_code=422,
            detail=f"Некорректный город. Допустимые значения: {', '.join(valid_cities)}",
        )

    try:
        service = get_deal_finder_service(db)

        # Получаем среднюю цену за м²
        avg_price_per_m2 = await service.get_avg_price_per_m2(
            city=city,
            rooms=rooms,
            currency=currency,
        )

        if avg_price_per_m2 is None:
            return {
                "city": city,
                "rooms": rooms,
                "currency": currency,
                "avg_price_per_m2": None,
                "total_listings": 0,
                "potential_deals": 0,
            }

        # Считаем количество объявлений с ценой ниже средней
        from sqlalchemy import select, func
        from app.models.listing import Listing, ListingStatus

        price_col = (
            Listing.price_per_m2_byn
            if currency.lower() == "byn"
            else Listing.price_per_m2_usd
        )

        filters = [
            price_col.isnot(None),
            Listing.city == city,
            Listing.status.in_(
                [
                    ListingStatus.active,
                    ListingStatus.new,
                    ListingStatus.updated,
                    ListingStatus.price_changed_byn,
                ]
            ),
        ]

        if rooms is not None:
            filters.append(Listing.rooms == rooms)

        # Общее количество
        total_query = select(func.count(Listing.id)).where(*filters)
        total_result = await db.execute(total_query)
        total_listings = total_result.scalar() or 0

        # Количество потенциально выгодных (ниже средней на 10%+)
        deal_threshold = avg_price_per_m2 * 0.9  # 10% ниже средней
        deals_query = select(func.count(Listing.id)).where(
            *filters, price_col <= deal_threshold
        )
        deals_result = await db.execute(deals_query)
        potential_deals = deals_result.scalar() or 0

        logger.info(
            f"Deal Finder stats: city={city}, rooms={rooms}, "
            f"avg_price={avg_price_per_m2}, total={total_listings}, "
            f"potential_deals={potential_deals}"
        )

        return {
            "city": city,
            "rooms": rooms,
            "currency": currency,
            "avg_price_per_m2": round(avg_price_per_m2, 2),
            "total_listings": total_listings,
            "potential_deals": potential_deals,
            "deal_threshold": round(deal_threshold, 2),
        }

    except ValueError as e:
        logger.error(f"Deal Finder stats validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Deal Finder stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
