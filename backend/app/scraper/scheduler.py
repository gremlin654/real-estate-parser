import asyncio
from datetime import datetime, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlalchemy import select

from app.db.database import async_session_maker
from app.config import settings, CITY_NAMES
from app.services.scan_settings_service import ScanSettingsService
from app.api.v1.ws import get_scan_manager


class ScraperScheduler:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self.scan_progress = {
            "is_scanning": False,
            "city": None,
            "city_name": None,
            "stage": "idle",
            "pages_scraped": 0,
            "listings_fetched": 0,
            "listings_processed": 0,
            "elapsed_seconds": 0,
            "is_stable": True,
        }
        self._ws_manager = None
    
    async def _broadcast_progress(self):
        """Отправить текущий прогресс всем WebSocket клиентам."""
        if self._ws_manager is None:
            self._ws_manager = get_scan_manager()

        try:
            logger.info(f"Broadcasting progress: stage={self.scan_progress['stage']}, pages={self.scan_progress['pages_scraped']}, listings={self.scan_progress['listings_fetched']}")
            await self._ws_manager.broadcast_progress(self.scan_progress)
        except Exception as e:
            logger.warning(f"Failed to broadcast WebSocket progress: {e}")

    async def start(self) -> None:
        if self.scheduler and self.scheduler.running:
            return

        async with async_session_maker() as db:
            settings_service = ScanSettingsService(db)
            scan_settings = await settings_service.get_settings()

        if scan_settings.enabled:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.add_job(
                self._run_scan_scheduled,
                trigger=IntervalTrigger(minutes=scan_settings.scan_interval_minutes),
                id="scheduled_scan",
                replace_existing=True,
            )
            self.scheduler.start()
            logger.info(f"Scheduler started with interval {scan_settings.scan_interval_minutes} min")
        else:
            logger.info("Scheduler disabled in settings")

    async def _run_scan_scheduled(self):
        logger.info("Starting scheduled scan")

    def stop(self):
        if self.scheduler:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")

    def update_interval(self, interval_minutes: int):
        if self.scheduler and self.scheduler.running:
            self.scheduler.remove_job("scheduled_scan")
            self.scheduler.add_job(
                self._run_scan_scheduled,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="scheduled_scan",
                replace_existing=True,
            )
            logger.info(f"Scheduler interval updated to {interval_minutes} min")


_scheduler_instance: Optional[ScraperScheduler] = None


def get_scheduler() -> ScraperScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ScraperScheduler()
    return _scheduler_instance


def init_scheduler() -> ScraperScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ScraperScheduler()
    return _scheduler_instance
