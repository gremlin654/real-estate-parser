from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import io
import json
from datetime import datetime

from app.db.database import get_db
from app.models.listing import Listing, ListingStatus

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/listings")
async def export_listings(
    format: str = Query("csv", description="Export format: csv, json"),
    city: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    conditions = []

    if not status:
        conditions.append(Listing.status != ListingStatus.deleted)
        conditions.append(Listing.status != ListingStatus.archived)
    elif status:
        conditions.append(Listing.status == ListingStatus(status))

    if city:
        conditions.append(Listing.city == city)

    query = select(Listing).where(*conditions) if conditions else select(Listing)
    result = await db.execute(query)
    listings = result.scalars().all()

    if format == "json":
        data = []
        for l in listings:
            data.append(
                {
                    "id": str(l.id),
                    "kufar_id": l.kufar_id,
                    "title": l.title,
                    "price": l.price,
                    "price_usd": l.price_usd,
                    "currency": l.currency,
                    "city": l.city,
                    "address": l.address,
                    "rooms": l.rooms,
                    "area": l.area,
                    "floor": l.floor,
                    "url": l.url,
                    "status": l.status,
                    "first_seen_at": (
                        l.first_seen_at.isoformat() if l.first_seen_at else None
                    ),
                }
            )
        return {"items": data, "total": len(listings)}

    elif format == "csv":
        output = io.StringIO()
        output.write(
            "id,kufar_id,title,price,price_usd,currency,city,rooms,area,floor,url,status\n"
        )
        for l in listings:
            output.write(
                f"{l.id},{l.kufar_id},{l.title},{l.price},{l.price_usd},{l.currency},{l.city},{l.rooms},{l.area},{l.floor},{l.url},{l.status}\n"
            )
        return {"content": output.getvalue(), "total": len(listings)}

    return {"error": "Unsupported format"}


@router.get("/summary")
async def export_summary(
    format: str = Query("json"), db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import func

    result = await db.execute(select(func.count(Listing.id)))
    total = result.scalar() or 0

    result = await db.execute(
        select(func.count(Listing.id)).where(Listing.status == ListingStatus.active)
    )
    active = result.scalar() or 0

    return {
        "total_listings": total,
        "active_listings": active,
        "exported_at": datetime.utcnow().isoformat(),
    }
