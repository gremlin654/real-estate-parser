from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, and_, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from loguru import logger

from app.db.database import get_db
from app.models.listing import Listing, ListingStatus
from app.schemas.listing import ListingResponse, PaginatedResponse
from app.decorators.cache import cache_response
from app.config import settings
from app.services.deal_finder_service import get_deal_finder_service

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=PaginatedResponse)
@cache_response(
    prefix="cache:listings",
    ttl=settings.CACHE_TTL_LISTINGS,
    key_params=[
        "page",
        "size",
        "status",
        "city",
        "rooms",
        "sort_order",
        "currency",
        "price_per_m2_min",
        "price_per_m2_max",
        "include_deal_metrics",
    ],
)
async def get_listings(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    price_from: Optional[int] = None,
    price_to: Optional[int] = None,
    price_per_m2_min: Optional[float] = Query(
        None, description="Минимальная цена за м²"
    ),
    price_per_m2_max: Optional[float] = Query(
        None, description="Максимальная цена за м²"
    ),
    rooms: Optional[list[int]] = Query(None, description="Room counts to filter"),
    rooms_other: Optional[bool] = Query(
        None, description="Include listings with rooms outside 1-4 range"
    ),
    sort_order: Optional[str] = Query(
        None, description="Sort by price: 'asc' or 'desc'"
    ),
    currency: Optional[str] = Query(None, description="Filter by currency: USD or BYN"),
    include_deal_metrics: bool = Query(
        False, description="Включить метрики выгоды (deal_percent, avg_price_per_m2)"
    ),
    deal_currency: str = Query(
        "usd", description="Валюта для расчёта метрик выгоды (byn/usd)"
    ),
    db: AsyncSession = Depends(get_db),
):
    conditions = []

    if not status:
        conditions.append(Listing.status != ListingStatus.deleted)
        conditions.append(Listing.status != ListingStatus.archived)
    elif status:
        conditions.append(Listing.status == status)

    if category:
        conditions.append(Listing.category == category)

    if city:
        conditions.append(Listing.city == city)

    # Фильтр currency НЕ фильтрует объявления, а только влияет на отображение
    # Поэтому убираем эту логику

    if price_from is not None:
        conditions.append(
            or_(Listing.price >= price_from, Listing.price_usd >= price_from)
        )

    if price_to is not None:
        conditions.append(or_(Listing.price <= price_to, Listing.price_usd <= price_to))

    # Фильтр по цене за м²
    if price_per_m2_min is not None and price_per_m2_max is not None:
        if price_per_m2_min > price_per_m2_max:
            raise HTTPException(
                status_code=400,
                detail="price_per_m2_min не может быть больше price_per_m2_max",
            )

    if price_per_m2_min is not None:
        # Используем price_per_m2_usd по умолчанию если currency не указан
        conditions.append(Listing.price_per_m2_usd >= price_per_m2_min)

    if price_per_m2_max is not None:
        conditions.append(Listing.price_per_m2_usd <= price_per_m2_max)

    # Фильтр по комнатам
    if rooms and len(rooms) > 0:
        # Если выбраны конкретные комнаты (1-4)
        room_conditions = [Listing.rooms == r for r in rooms]

        # Если также выбран rooms_other, добавляем условие для 5+ комнат
        if rooms_other:
            room_conditions.append(or_(Listing.rooms >= 5, Listing.rooms.is_(None)))

        conditions.append(or_(*room_conditions))
    elif rooms_other:
        # Только rooms_other выбран - показываем 5+ комнат и None
        conditions.append(or_(Listing.rooms >= 5, Listing.rooms.is_(None)))

    query = select(Listing).where(and_(*conditions))

    # Сортировка
    if sort_order == "asc":
        # По возрастанию цены (0 в начале, потом price_usd или price)
        query = query.order_by(
            case(
                (Listing.price_usd.isnot(None), Listing.price_usd), else_=Listing.price
            ).asc()
        )
    elif sort_order == "desc":
        # По убыванию цены (0 в конце, потом price_usd или price)
        query = query.order_by(
            case(
                (Listing.price_usd.isnot(None), Listing.price_usd), else_=Listing.price
            ).desc()
        )
    elif sort_order == "newest":
        # Сначала новые (по дате создания)
        query = query.order_by(Listing.first_seen_at.desc())
    elif sort_order == "oldest":
        # Сначала старые (по дате создания)
        query = query.order_by(Listing.first_seen_at.asc())

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    listings = result.scalars().all()

    # Если запрошены метрики выгоды, добавляем их
    if include_deal_metrics:
        logger.info(
            f"Adding deal metrics for {len(listings)} listings, currency={deal_currency}"
        )
        service = get_deal_finder_service(db)

        # Группируем объявления по city и rooms для эффективного расчёта средней цены
        from collections import defaultdict

        avg_prices_cache = {}

        items_with_metrics = []
        for listing in listings:
            # Кэш для средней цены за м²
            cache_key = (listing.city, listing.rooms, deal_currency)
            if cache_key not in avg_prices_cache:
                avg_prices_cache[cache_key] = await service.get_avg_price_per_m2(
                    city=listing.city, rooms=listing.rooms, currency=deal_currency
                )

            avg_price_per_m2 = avg_prices_cache[cache_key]

            # Вычисляем deal_percent
            if avg_price_per_m2:
                price_per_m2 = (
                    float(listing.price_per_m2_byn)
                    if deal_currency == "byn"
                    else (
                        float(listing.price_per_m2_usd)
                        if listing.price_per_m2_usd
                        else None
                    )
                )

                if price_per_m2:
                    deal_percent = service.calculate_deal_percent(
                        price_per_m2, avg_price_per_m2
                    )
                else:
                    deal_percent = None
            else:
                deal_percent = None

            # Создаём dict с данными
            item_dict = {
                "id": listing.id,
                "kufar_id": listing.kufar_id,
                "url": listing.url,
                "title": listing.title,
                "price": listing.price,
                "price_usd": listing.price_usd,
                "currency": listing.currency,
                "city": listing.city,
                "address": listing.address,
                "rooms": listing.rooms,
                "area": listing.area,
                "floor": listing.floor,
                "total_floors": listing.total_floors,
                "images": listing.images or [],
                "price_per_m2_byn": (
                    float(listing.price_per_m2_byn)
                    if listing.price_per_m2_byn
                    else None
                ),
                "price_per_m2_usd": (
                    float(listing.price_per_m2_usd)
                    if listing.price_per_m2_usd
                    else None
                ),
                "status": (
                    listing.status.value
                    if hasattr(listing.status, "value")
                    else str(listing.status)
                ),
                "first_seen_at": listing.first_seen_at,
                "last_seen_at": listing.last_seen_at,
                "deleted_at": listing.deleted_at,
                "deal_percent": deal_percent,
                "avg_price_per_m2": avg_price_per_m2,
            }
            items_with_metrics.append(item_dict)

        return {
            "items": items_with_metrics,
            "total": total,
            "page": page,
            "size": size,
        }

    return {
        "items": [ListingResponse.model_validate(l) for l in listings],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID

    try:
        uuid_id = UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Listing).where(Listing.id == uuid_id))
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    return ListingResponse.model_validate(listing)
