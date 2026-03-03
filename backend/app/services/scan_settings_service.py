from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.listing import ScanSettings
from datetime import datetime
from typing import Optional


class ScanSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self) -> ScanSettings:
        result = await self.db.execute(select(ScanSettings).where(ScanSettings.id == 1))
        settings = result.scalar_one_or_none()

        if not settings:
            settings = ScanSettings(id=1, scan_interval_minutes=30, enabled=True)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings

    async def update_settings(
        self,
        scan_interval_minutes: int = None,
        enabled: bool = None
    ) -> ScanSettings:
        settings = await self.get_settings()

        if scan_interval_minutes is not None:
            settings.scan_interval_minutes = scan_interval_minutes
        if enabled is not None:
            settings.enabled = enabled

        settings.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(settings)
        return settings
