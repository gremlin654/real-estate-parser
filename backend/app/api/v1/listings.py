from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, and_, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.models.listing import Listing, ListingStatus
from app.schemas.listing import ListingResponse, PaginatedResponse
from app.decorators.cache import cache_response
from app.config import settings

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=PaginatedResponse)
@cache_response(prefix="cache:listings", ttl=settings.CACHE_TTL_LISTINGS, key_params=["page", "size", "status", "city", "rooms", "sort_order", "currency"])
async def get_listings(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    price_from: Optional[int] = None,
    price_to: Optional[int] = None,
    rooms: Optional[list[int]] = Query(None, description="Room counts to filter"),
    rooms_other: Optional[bool] = Query(
        None, description="Include listings with rooms outside 1-4 range"
    ),
    sort_order: Optional[str] = Query(
        None, description="Sort by price: 'asc' or 'desc'"
    ),
    currency: Optional[str] = Query(None, description="Filter by currency: USD or BYN"),
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
