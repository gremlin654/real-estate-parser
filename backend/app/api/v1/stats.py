from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, List

from app.db.database import get_db
from app.models.listing import Listing, ListingStatus, ListingHistory
from app.decorators.cache import cache_response
from app.config import settings

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary")
@cache_response(prefix="cache:stats:summary", ttl=settings.CACHE_TTL_STATS_SUMMARY, key_params=["city"])
async def get_summary(request: Request, city: str = Query(None), db: AsyncSession = Depends(get_db)):
    today = datetime.utcnow().date()

    # Build base query with optional city filter
    base_filters = []
    if city:
        base_filters.append(Listing.city == city)

    new_result = await db.execute(
        select(func.count(Listing.id)).where(
            func.date(Listing.first_seen_at) == today, *base_filters
        )
    )
    new_today = new_result.scalar() or 0

    deleted_result = await db.execute(
        select(func.count(Listing.id)).where(
            func.date(Listing.deleted_at) == today,
            Listing.status == ListingStatus.deleted,
            *base_filters,
        )
    )
    deleted_today = deleted_result.scalar() or 0

    # Count price changes today (USD)
    price_changed_filters = base_filters.copy() if city else []
    price_changed_result = await db.execute(
        select(func.count(ListingHistory.id))
        .where(
            ListingHistory.event_type == "price_changed",
            func.date(ListingHistory.created_at) == today,
            ListingHistory.price_before.isnot(None),
            ListingHistory.price_after.isnot(None),
            *price_changed_filters,
        )
        .join(Listing, ListingHistory.listing_id == Listing.id)
    )
    price_changed_usd_today = price_changed_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Listing.id)).where(
            Listing.status.in_(
                [ListingStatus.active, ListingStatus.new, ListingStatus.updated, ListingStatus.price_changed_byn]
            ),
            *base_filters,
        )
    )
    active_total = active_result.scalar() or 0

    return {
        "new_today": new_today,
        "deleted_today": deleted_today,
        "price_changed_usd_today": price_changed_usd_today,
        "price_changed_byn_today": 0,
        "active_total": active_total,
        "archived_total": 0,
    }


@router.get("/price-trends")
@cache_response(prefix="cache:stats:price-trends", ttl=settings.CACHE_TTL_STATS_OTHER, key_params=["city", "rooms", "period_months"])
async def get_price_trends(request: Request, city: str = Query(...), rooms: int = Query(2), period_months: int = Query(12, ge=1, le=24), db: AsyncSession = Depends(get_db)):
    """Динамика цен по месяцам для выбранной комнаты"""
    from sqlalchemy import text, Numeric

    # Get data from listing_history snapshot for created events
    # Use func.extract for PostgreSQL
    year_col = func.extract("year", ListingHistory.created_at).label("year")
    month_col = func.extract("month", ListingHistory.created_at).label("month")

    query = (
        select(
            year_col,
            month_col,
            func.avg(
                func.cast(ListingHistory.snapshot["price_usd"].astext, Numeric)
            ).label("avg_price"),
            func.count(Listing.id).label("count"),
        )
        .join(Listing, ListingHistory.listing_id == Listing.id)
        .where(
            ListingHistory.event_type == "created",
            Listing.city == city,
            Listing.rooms == rooms,
            ListingHistory.snapshot["price_usd"].astext != "null",
            ListingHistory.created_at
            >= text(f"NOW() - INTERVAL '{period_months} months'"),
        )
        .group_by(
            year_col,
            month_col,
        )
        .order_by(
            year_col,
            month_col,
        )
    )

    result = await db.execute(query)
    rows = result.all()

    data = [
        {
            "year": int(row.year),
            "month": int(row.month),
            "avg_price_usd": round(float(row.avg_price), 2) if row.avg_price else 0,
            "listings_count": row.count,
        }
        for row in rows
    ]

    return {
        "city": city,
        "rooms": rooms,
        "period_months": period_months,
        "data": data,
    }


@router.get("/room-distribution")
@cache_response(prefix="cache:stats:room-distribution", ttl=settings.CACHE_TTL_STATS_OTHER, key_params=["city"])
async def get_room_distribution(request: Request, city: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Распределение по комнатам"""
    query = (
        select(
            Listing.rooms,
            func.count(Listing.id).label("count"),
            func.avg(Listing.price_usd).label("avg_price"),
        )
        .where(
            Listing.city == city,
            Listing.status.in_(
                [ListingStatus.active, ListingStatus.new, ListingStatus.updated, ListingStatus.price_changed_byn]
            ),
            Listing.rooms >= 1,  # Все комнаты от 1 и больше
        )
        .group_by(
            Listing.rooms,
        )
        .order_by(
            Listing.rooms,
        )
    )

    result = await db.execute(query)
    rows = result.all()

    data = [
        {
            "rooms": row.rooms,
            "count": row.count,
            "avg_price": round(float(row.avg_price), 2) if row.avg_price else 0,
        }
        for row in rows
    ]

    return {
        "city": city,
        "data": data,
    }


@router.get("/daily-activity")
@cache_response(prefix="cache:stats:daily-activity", ttl=settings.CACHE_TTL_STATS_OTHER, key_params=["city", "period_days"])
async def get_daily_activity(request: Request, city: str = Query(...), period_days: int = Query(30, ge=1, le=90), db: AsyncSession = Depends(get_db)):
    """Ежедневная активность (новые, удалённые, изменения цены)"""
    from sqlalchemy import case, text

    # Get activity from listing_history
    query = (
        select(
            func.date(ListingHistory.created_at).label("date"),
            func.sum(
                case(
                    (ListingHistory.event_type == "created", 1),
                    else_=0,
                )
            ).label("new_count"),
            func.sum(
                case(
                    (ListingHistory.event_type == "deleted", 1),
                    else_=0,
                )
            ).label("deleted_count"),
            func.sum(
                case(
                    (ListingHistory.event_type == "price_changed", 1),
                    else_=0,
                )
            ).label("price_changed_count"),
        )
        .join(Listing, ListingHistory.listing_id == Listing.id)
        .where(
            Listing.city == city,
            ListingHistory.created_at >= text(f"NOW() - INTERVAL '{period_days} days'"),
        )
        .group_by(
            func.date(ListingHistory.created_at),
        )
        .order_by(
            func.date(ListingHistory.created_at),
        )
    )

    result = await db.execute(query)
    rows = result.all()

    data = [
        {
            "date": str(row.date),
            "new_count": row.new_count or 0,
            "deleted_count": row.deleted_count or 0,
            "price_changed_count": row.price_changed_count or 0,
        }
        for row in rows
    ]

    return {
        "city": city,
        "period_days": period_days,
        "data": data,
    }
