from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.listing import Listing, ListingStatus, EventType, ListingHistory
from datetime import datetime, timedelta
from loguru import logger
from typing import Optional


class ListingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_kufar_id(self, kufar_id: str) -> Listing | None:
        result = await self.db.execute(select(Listing).where(Listing.kufar_id == kufar_id))
        return result.scalar_one_or_none()

    async def upsert(self, listing_data: dict) -> tuple[Listing, str]:
        kufar_id = listing_data['kufar_id']
        existing = await self.get_by_kufar_id(kufar_id)

        if existing:
            # Update existing
            for key, value in listing_data.items():
                if key != 'kufar_id':
                    setattr(existing, key, value)
            existing.last_seen_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing, 'updated'
        else:
            # Create new
            new_listing = Listing(**listing_data)
            self.db.add(new_listing)
            await self.db.commit()
            await self.db.refresh(new_listing)
            return new_listing, 'created'

    async def upsert_listings(self, listings_data: list[dict], city: str) -> dict:
        """Массовое обновление/создание объявлений"""
        stats = {
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "processed": 0,
        }
        
        kufar_ids = set()
        
        for listing_data in listings_data:
            try:
                listing, action = await self.upsert(listing_data)
                kufar_ids.add(listing.kufar_id)
                
                if action == 'created':
                    stats["created"] += 1
                else:
                    stats["updated"] += 1
                    
                stats["processed"] += 1
            except Exception as e:
                logger.error(f"Error upserting listing: {e}")
        
        # Помечаем удалённые объявления
        if kufar_ids:
            deleted_count = await self.mark_deleted(kufar_ids, city)
            stats["deleted"] = deleted_count
        
        return stats

    async def mark_deleted(self, kufar_ids: set[str], city: str) -> int:
        result = await self.db.execute(
            select(Listing).where(
                and_(
                    Listing.kufar_id.not_in(kufar_ids),
                    Listing.city == city,
                    Listing.status.in_([ListingStatus.active, ListingStatus.new, ListingStatus.updated])
                )
            )
        )
        listings = result.scalars().all()

        for listing in listings:
            listing.status = ListingStatus.deleted
            listing.deleted_at = datetime.utcnow()

        await self.db.commit()
        return len(listings)
