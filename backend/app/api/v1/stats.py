from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.database import get_db
from app.models.listing import Listing, ListingStatus

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary")
async def get_summary(city: str = Query(None), db: AsyncSession = Depends(get_db)):
    today = datetime.utcnow().date()

    city_filter = Listing.city == city if city else None

    new_result = await db.execute(
        select(func.count(Listing.id)).where(
            func.date(Listing.first_seen_at) == today,
            *(city_filter,) if city_filter else ()
        )
    )
    new_today = new_result.scalar() or 0

    deleted_result = await db.execute(
        select(func.count(Listing.id)).where(
            func.date(Listing.deleted_at) == today,
            Listing.status == ListingStatus.deleted,
            *(city_filter,) if city_filter else ()
        )
    )
    deleted_today = deleted_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Listing.id)).where(
            Listing.status.in_([ListingStatus.active, ListingStatus.new, ListingStatus.updated]),
            *(city_filter,) if city_filter else ()
        )
    )
    active_total = active_result.scalar() or 0

    return {
        "new_today": new_today,
        "deleted_today": deleted_today,
        "price_changed_usd_today": 0,
        "price_changed_byn_today": 0,
        "active_total": active_total,
        "archived_total": 0,
    }
