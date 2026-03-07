from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.listing import ScanSettings
from app.config import CITY_NAMES
from datetime import datetime
from typing import Optional, List, Dict
import uuid


class ScanSettingsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_city_settings(self, city: str) -> Optional[ScanSettings]:
        """Получить настройки для конкретного города."""
        if city not in CITY_NAMES:
            raise ValueError(
                f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}"
            )

        result = await self.db.execute(
            select(ScanSettings).where(ScanSettings.city == city)
        )
        return result.scalar_one_or_none()

    async def get_or_create_city_settings(self, city: str) -> ScanSettings:
        """Получить или создать настройки для города."""
        if city not in CITY_NAMES:
            raise ValueError(
                f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}"
            )

        settings = await self.get_city_settings(city)

        if not settings:
            settings = ScanSettings(
                id=uuid.uuid4(), city=city, scan_interval_minutes=30, enabled=False
            )
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings

    async def get_all_settings(self) -> Dict[str, ScanSettings]:
        """Получить настройки для всех городов."""
        result = await self.db.execute(select(ScanSettings))
        settings_list = result.scalars().all()
        return {settings.city: settings for settings in settings_list}

    async def update_city_settings(
        self, city: str, enabled: bool = None, interval: int = None
    ) -> ScanSettings:
        """Обновить настройки для города."""
        if city not in CITY_NAMES:
            raise ValueError(
                f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}"
            )

        # Валидация интервала
        if interval is not None:
            if interval < 5:
                raise ValueError("Scan interval must be at least 5 minutes")
            if interval > 1440:
                raise ValueError(
                    "Scan interval must be at most 1440 minutes (24 hours)"
                )

        # Получить или создать настройки
        settings = await self.get_or_create_city_settings(city)

        if enabled is not None:
            settings.enabled = enabled

        if interval is not None:
            settings.scan_interval_minutes = interval

        settings.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def is_city_enabled(self, city: str) -> bool:
        """Проверить, включено ли сканирование для города."""
        if city not in CITY_NAMES:
            raise ValueError(
                f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}"
            )

        settings = await self.get_city_settings(city)
        if not settings:
            return False
        return settings.enabled

    async def get_enabled_cities(self) -> List[str]:
        """Получить список включённых городов."""
        result = await self.db.execute(
            select(ScanSettings).where(ScanSettings.enabled == True)
        )
        settings_list = result.scalars().all()
        return [settings.city for settings in settings_list]

    async def get_interval_minutes(self, city: str) -> int:
        """Получить интервал сканирования для конкретного города."""
        if city not in CITY_NAMES:
            raise ValueError(
                f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}"
            )

        settings = await self.get_city_settings(city)
        if not settings:
            return 30  # Default interval
        return settings.scan_interval_minutes

    async def is_enabled(self, city: str) -> bool:
        """Проверить, включено ли автоматическое сканирование для города."""
        return await self.is_city_enabled(city)
