from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.listing import ListingHistory, Listing
from app.schemas.listing import ListingHistoryResponse

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{listing_id}", response_model=list[ListingHistoryResponse])
async def get_listing_history(listing_id: str, db: AsyncSession = Depends(get_db)):
    from uuid import UUID

    try:
        uuid_id = UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Listing).where(Listing.id == uuid_id))
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    result = await db.execute(
        select(ListingHistory)
        .where(ListingHistory.listing_id == uuid_id)
        .order_by(ListingHistory.created_at.desc())
    )
    history = result.scalars().all()

    return [ListingHistoryResponse.model_validate(h) for h in history]
