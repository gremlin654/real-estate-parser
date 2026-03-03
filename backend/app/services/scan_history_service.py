from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.listing import ScanHistory
from datetime import datetime
from typing import Optional


class ScanHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_scan(self, city: str, city_name: str, trigger_type: str = 'manual') -> ScanHistory:
        scan = ScanHistory(
            city=city,
            city_name=city_name,
            trigger_type=trigger_type,
            status='running'
        )
        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)
        return scan

    async def update_scan(
        self,
        scan_id: str,
        listings_fetched: int = None,
        listings_created: int = None,
        listings_updated: int = None,
        listings_deleted: int = None,
        pages_scraped: int = None,
        errors: list = None
    ):
        scan = await self.get_scan(scan_id)
        if not scan:
            return

        if listings_fetched is not None:
            scan.listings_fetched = listings_fetched
        if listings_created is not None:
            scan.listings_created = listings_created
        if listings_updated is not None:
            scan.listings_updated = listings_updated
        if listings_deleted is not None:
            scan.listings_deleted = listings_deleted
        if pages_scraped is not None:
            scan.pages_scraped = pages_scraped
        if errors is not None:
            scan.errors = errors

        await self.db.commit()

    async def complete_scan(self, scan_id: str, status: str = 'completed', error_message: str = None):
        scan = await self.get_scan(scan_id)
        if not scan:
            return

        scan.status = status
        scan.completed_at = datetime.utcnow()
        scan.error_message = error_message

        if scan.started_at:
            scan.duration_seconds = int((scan.completed_at - scan.started_at).total_seconds())

        await self.db.commit()

    async def get_scan(self, scan_id: str) -> Optional[ScanHistory]:
        from uuid import UUID
        try:
            uuid_id = UUID(scan_id)
        except ValueError:
            return None

        result = await self.db.execute(select(ScanHistory).where(ScanHistory.id == uuid_id))
        return result.scalar_one_or_none()

    async def get_history(self, limit: int = 50, offset: int = 0, city: str = None) -> list[ScanHistory]:
        query = select(ScanHistory).order_by(ScanHistory.started_at.desc())
        if city:
            query = query.where(ScanHistory.city == city)
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_summary(self) -> dict:
        result = await self.db.execute(select(func.count(ScanHistory.id)))
        total = result.scalar()

        result = await self.db.execute(select(func.count(ScanHistory.id)).where(ScanHistory.status == 'completed'))
        completed = result.scalar()

        result = await self.db.execute(select(func.count(ScanHistory.id)).where(ScanHistory.status == 'error'))
        failed = result.scalar()

        result = await self.db.execute(select(func.count(ScanHistory.id)).where(ScanHistory.status == 'running'))
        running = result.scalar()

        return {
            'total_scans': total or 0,
            'completed_scans': completed or 0,
            'failed_scans': failed or 0,
            'running_scans': running or 0,
        }
