"""
Deal Finder API - поиск выгодных предложений недвижимости.

Endpoints для поиска квартир с ценой ниже рыночной и Deal Score.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from loguru import logger

from app.db.database import get_db
from app.services.deal_finder_service import get_deal_finder_service, DealFinderService
from app.services.price_drop_service import PriceDropService
from app.services.deal_score_service import DealScoreService, get_deal_score_service
from app.models.listing import Listing, ListingStatus, ListingHistory
from app.schemas.deals import (
    DealFilters,
    DealListingResponse,
    DealsResponse,
)
from app.schemas.deal_score import DealListingWithScore, DealsScoreResponse
from app.decorators.cache import cache_response
from app.core.redis_client import get_redis_client, RedisClient
from app.config import settings

router = APIRouter(prefix="/deals", tags=["deals"])

VALID_CITIES = ["minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"]


def get_deal_score_service_depends() -> DealScoreService:
    """Factory функция для FastAPI Depends."""
    try:
        redis_client = get_redis_client().get_client()
        return DealScoreService(redis_client=redis_client)
    except Exception:
        # Redis недоступен — работаем без кэша
        return DealScoreService()


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


@router.get("/score")
@cache_response(
    prefix="cache:deals:score",
    ttl=settings.CACHE_TTL_STATS_OTHER,  # 300 сек
    key_params=["city", "rooms", "min_score", "currency", "limit", "offset"],
)
async def get_deals_by_score(
    request: Request,
    city: str = Query(..., description="Город для поиска (обязательно)"),
    rooms: Optional[int] = Query(None, ge=1, le=10, description="Количество комнат"),
    min_score: float = Query(70.0, ge=0, le=100, description="Минимальный Deal Score"),
    currency: str = Query("usd", description="Валюта расчётов (usd/byn)"),
    limit: int = Query(20, ge=1, le=100, description="Максимум результатов"),
    offset: int = Query(0, ge=0, description="Смещение"),
    db: AsyncSession = Depends(get_db),
    deal_score_service: DealScoreService = Depends(get_deal_score_service_depends),
):
    """
    Поиск объявлений с Deal Score >= min_score.

    Deal Score (0-100) рассчитывается на основе:
    - PriceScore (0.40) — цена ниже рынка
    - TrendScore (0.20) — динамика цены
    - LiquidityScore (0.15) — ликвидность
    - FreshnessScore (0.10) — свежесть
    - FloorScore (0.05) — этаж
    - BonusScore (0.10) — бонусы

    Исправления (v4.0.2):
    - Batch запрос для drop_percent (устранение N+1 queries)
    - Один db.commit() вместо N коммитов в цикле
    - Поддержка currency=byn через EXCHANGE_RATE_USD_BYN

    - **city**: Город для поиска (обязательно)
    - **rooms**: Количество комнат (опционально)
    - **min_score**: Минимальный Deal Score (0-100, по умолчанию 70)
    - **currency**: Валюта для расчётов (byn или usd, по умолчанию usd)
    - **limit**: Максимум результатов (1-100, по умолчанию 20)
    - **offset**: Смещение для пагинации (по умолчанию 0)

    Response включает:
    - items: Список объявлений с Deal Score
    - total: Общее количество найденных объявлений
    - avg_score: Средний Deal Score
    - min_score_filter: Применённый фильтр min_score
    - currency: Валюта расчётов
    """
    # Валидация city
    if city.lower() not in VALID_CITIES:
        raise HTTPException(
            status_code=422,
            detail=f"Некорректный город. Допустимые значения: {', '.join(VALID_CITIES)}",
        )

    # Валидация currency
    currency_lower = currency.lower()
    if currency_lower not in ["usd", "byn"]:
        raise HTTPException(status_code=422, detail="Валюта должна быть usd или byn")

    logger.info(
        f"Deal Score search: city={city}, rooms={rooms}, min_score={min_score}, "
        f"currency={currency_lower}, limit={limit}, offset={offset}"
    )

    # Получить avg_price_per_m2 в USD
    deal_finder = DealFinderService(db)
    try:
        avg_price_per_m2_usd = await deal_finder.get_avg_price_per_m2(
            city=city, rooms=rooms, currency="usd"
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not avg_price_per_m2_usd:
        logger.info(f"No avg_price_per_m2 for city={city}, rooms={rooms}")
        return DealsScoreResponse(
            items=[],
            total=0,
            avg_score=0.0,
            min_score_filter=min_score,
            currency=currency_lower,
            limit=limit,
            offset=offset,
        )

    # 🔧 FIX #3: Конвертировать в BYN если нужно
    if currency_lower == "byn":
        avg_price_per_m2 = avg_price_per_m2_usd * settings.EXCHANGE_RATE_USD_BYN
    else:
        avg_price_per_m2 = avg_price_per_m2_usd

    # Получить все активные объявления для города/комнат
    filters = [
        Listing.city == city,
        Listing.status.in_(
            [
                ListingStatus.active,
                ListingStatus.new,
                ListingStatus.updated,
                ListingStatus.price_changed_byn,
            ]
        ),
        Listing.price_per_m2_usd.isnot(None),
    ]

    if rooms:
        filters.append(Listing.rooms == rooms)

    result = await db.execute(select(Listing).where(*filters))
    listings = result.scalars().all()

    logger.info(f"Found {len(listings)} listings for city={city}, rooms={rooms}")

    if not listings:
        return DealsScoreResponse(
            items=[],
            total=0,
            avg_score=0.0,
            min_score_filter=min_score,
            currency=currency_lower,
            limit=limit,
            offset=offset,
        )

    # 🔧 FIX #1: Batch запрос для drop_percent (устранение N+1 queries)
    listing_ids = [listing.id for listing in listings]

    from sqlalchemy import func as sql_func

    # Получить всю историю цен одним запросом
    price_history_query = (
        select(
            ListingHistory.listing_id,
            sql_func.max(ListingHistory.price_before).label("max_price"),
            sql_func.min(ListingHistory.price_after).label("min_price"),
        )
        .where(
            ListingHistory.listing_id.in_(listing_ids),
            ListingHistory.event_type.in_(
                ["price_changed", "price_changed_byn", "edited"]
            ),
        )
        .group_by(ListingHistory.listing_id)
    )

    history_result = await db.execute(price_history_query)
    price_history_map = {row.listing_id: row for row in history_result.all()}

    # Рассчитать deal_score для каждого
    scored_listings = []
    updated_listings = []

    for listing in listings:
        # 🔧 FIX #1 (продолжение): Получить drop_percent из batch map
        history = price_history_map.get(listing.id)
        if history and history.max_price and history.max_price > 0:
            drop_percent = (
                (history.max_price - history.min_price) / history.max_price * 100
            )
        else:
            drop_percent = 0.0

        # Рассчитать deal_score
        try:
            score = await deal_score_service.calculate_score(
                listing=listing,
                avg_price_per_m2=avg_price_per_m2,
                drop_percent=drop_percent,
            )
        except Exception as e:
            logger.error(f"Error calculating score for listing {listing.id}: {e}")
            continue

        # Получить label
        label = DealScoreService.calculate_label(score)

        # 🔧 FIX #2: Обновить в памяти (НЕ коммитить ещё)
        if listing.deal_score != score or listing.deal_label != label:
            listing.deal_score = score
            listing.deal_label = label
            updated_listings.append(listing)

        if score >= min_score:
            scored_listings.append(
                {
                    "listing": listing,
                    "score": score,
                    "label": label,
                }
            )

    # 🔧 FIX #2: Один commit для всех обновлений
    if updated_listings:
        try:
            await db.commit()
            logger.info(f"Updated deal_score for {len(updated_listings)} listings")
        except Exception as e:
            logger.warning(f"Error committing deal_score updates: {e}")
            await db.rollback()

    # Сортировка по deal_score DESC
    scored_listings.sort(key=lambda x: x["score"], reverse=True)

    # Пагинация
    total = len(scored_listings)
    paginated = scored_listings[offset : offset + limit]

    # Средний score
    avg_score = (
        sum(item["score"] for item in scored_listings) / len(scored_listings)
        if scored_listings
        else 0.0
    )

    logger.info(
        f"Deal Score search: city={city}, rooms={rooms}, min_score={min_score}, "
        f"found={total}, returned={len(paginated)}"
    )

    # Формируем response
    items = []
    for item in paginated:
        listing = item["listing"]
        items.append(
            DealListingWithScore(
                id=listing.id,
                kufar_id=listing.kufar_id,
                url=listing.url,
                title=listing.title,
                price=listing.price,
                price_usd=listing.price_usd,
                price_per_m2_usd=(
                    float(listing.price_per_m2_usd)
                    if listing.price_per_m2_usd
                    else None
                ),
                city=listing.city,
                rooms=listing.rooms,
                area=listing.area,
                floor=listing.floor,
                total_floors=listing.total_floors,
                address=listing.address,
                status=(
                    listing.status.value
                    if hasattr(listing.status, "value")
                    else str(listing.status)
                ),
                first_seen_at=listing.first_seen_at,
                last_seen_at=listing.last_seen_at,
                deal_score=item["score"],
                deal_label=item["label"],
            )
        )

    return DealsScoreResponse(
        items=items,
        total=total,
        avg_score=round(avg_score, 2),
        min_score_filter=min_score,
        currency=currency_lower,
        limit=limit,
        offset=offset,
    )
