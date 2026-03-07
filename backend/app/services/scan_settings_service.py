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
            settings = ScanSettings(id=1, scan_interval_minutes=30, enabled=True, city="mogilev")
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings

    async def update_settings(
        self,
        scan_interval_minutes: int = None,
        enabled: bool = None,
        city: str = None
    ) -> ScanSettings:
        settings = await self.get_settings()

        # Валидация интервала
        if scan_interval_minutes is not None:
            if scan_interval_minutes < 5:
                raise ValueError("Scan interval must be at least 5 minutes")
            if scan_interval_minutes > 1440:
                raise ValueError("Scan interval must be at most 1440 minutes (24 hours)")
            settings.scan_interval_minutes = scan_interval_minutes
            
        if enabled is not None:
            settings.enabled = enabled
        if city is not None:
            settings.city = city

        settings.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def get_interval_minutes(self) -> int:
        """Получить текущий интервал сканирования в минутах."""
        settings = await self.get_settings()
        return settings.scan_interval_minutes

    async def is_enabled(self) -> bool:
        """Проверить, включено ли автоматическое сканирование."""
        settings = await self.get_settings()
        return settings.enabled
