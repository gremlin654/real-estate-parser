import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List
from functools import partial
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlalchemy import select

from app.db.database import async_session_maker
from app.config import settings, CITY_NAMES
from app.services.scan_settings_service import ScanSettingsService
from app.services.scan_stats_service import ScanStatsService
from app.services.listing_service import ListingService
from app.services.scan_history_service import ScanHistoryService


class ScraperScheduler:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = (
            False  # Обратная совместимость: True если len(scanning_cities) > 0
        )
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
        # Параллельные сканирования: ключ - city код, значение - информация о сканировании
        self.scanning_cities: Dict[str, Dict] = {}
        # Lock для thread-safe операций со scanning_cities
        self._lock = asyncio.Lock()
        self._ws_manager = None

    async def _add_scanning_city(self, city: str, trigger_type: str, scan_id: str):
        """Добавить город в сканирование (thread-safe)."""
        async with self._lock:
            self.scanning_cities[city] = {
                "trigger_type": trigger_type,
                "started_at": datetime.now(timezone.utc).replace(tzinfo=None),
                "scan_id": scan_id,
                "progress": {
                    "is_scanning": True,
                    "city": city,
                    "city_name": CITY_NAMES.get(city, city),
                    "stage": "starting",
                    "pages_scraped": 0,
                    "listings_fetched": 0,
                    "listings_processed": 0,
                    "elapsed_seconds": 0,
                    "is_stable": False,
                },
            }
            # Обратная совместимость
            self.is_running = len(self.scanning_cities) > 0

    async def _remove_scanning_city(self, city: str):
        """Удалить город из сканирования после завершения (thread-safe)."""
        async with self._lock:
            self.scanning_cities.pop(city, None)
            # Обратная совместимость
            self.is_running = len(self.scanning_cities) > 0

    def _is_city_scanning(self, city: str) -> bool:
        """Проверка: сканируется ли город в данный момент."""
        return city in self.scanning_cities

    def _get_scanning_cities(self) -> List[Dict]:
        """Получить список всех активных сканирований."""
        result = []
        for city, data in self.scanning_cities.items():
            progress = data.get("progress", {})
            result.append(
                {
                    "city": city,
                    "city_name": CITY_NAMES.get(city, city),
                    "trigger_type": data["trigger_type"],
                    "started_at": data["started_at"].isoformat(),
                    "stage": progress.get("stage", "unknown"),
                    "pages_scraped": progress.get("pages_scraped", 0),
                    "listings_fetched": progress.get("listings_fetched", 0),
                    "listings_processed": progress.get("listings_processed", 0),
                    "elapsed_seconds": progress.get("elapsed_seconds", 0),
                    "is_stable": progress.get("is_stable", False),
                }
            )
        return result

    async def _update_city_progress(self, city: str, progress: Dict):
        """Обновить прогресс для конкретного города (thread-safe)."""
        async with self._lock:
            if city in self.scanning_cities:
                self.scanning_cities[city]["progress"] = progress

    async def _broadcast_progress(self):
        """Отправить текущий прогресс всем WebSocket клиентам."""
        if self._ws_manager is None:
            from app.api.v1.ws import get_scan_manager

            self._ws_manager = get_scan_manager()

        try:
            # Обновить список сканируемых городов в ws_manager
            await self._ws_manager.update_scanning_cities(self._get_scanning_cities())

            logger.info(
                f"Broadcasting progress: stage={self.scan_progress['stage']}, pages={self.scan_progress['pages_scraped']}, listings={self.scan_progress['listings_fetched']}"
            )
            await self._ws_manager.broadcast_progress(self.scan_progress)
        except Exception as e:
            logger.warning(f"Failed to broadcast WebSocket progress: {e}")

    async def start(self) -> None:
        """Запуск scheduler с проверкой включённых городов."""
        # Если scheduler уже запущен - ничего не делаем
        if self.scheduler and self.scheduler.running:
            logger.info("Scheduler already running")
            return

        async with async_session_maker() as db:
            settings_service = ScanSettingsService(db)
            enabled_cities = await settings_service.get_enabled_cities()

        if not enabled_cities:
            logger.info("No cities enabled for auto-scan")
            # Создаём пустой scheduler чтобы он был готов к работе
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()
            return

        # Создаём новый scheduler или перезапускаем существующий
        self.scheduler = AsyncIOScheduler()

        # Для каждого включённого города добавить job
        for city in enabled_cities:
            city_settings = await settings_service.get_city_settings(city)
            self.scheduler.add_job(
                partial(self._run_scan_scheduled, city),
                trigger=IntervalTrigger(minutes=city_settings.scan_interval_minutes),
                id=f"scheduled_scan_{city}",
                replace_existing=True,
            )

        self.scheduler.start()
        logger.info(f"Scheduled scan started for cities: {enabled_cities}")

    async def _run_scan_scheduled(self, city: str):
        """Запуск планового сканирования по расписанию для конкретного города."""
        from app.scraper.kufar_scraper import KufarScraper

        logger.info(f"Starting scheduled scan for {city}")

        start_time = datetime.now(timezone.utc).replace(tzinfo=None)

        # Создать запись истории сканирования
        async with async_session_maker() as db:
            scan_history_service = ScanHistoryService(db)
            scan_record = await scan_history_service.create_scan_record(
                city=city,
                city_name=CITY_NAMES.get(city, city),
                trigger_type="scheduled",
            )

        logger.info(f"Starting scheduled scan for {city}, scan_id: {scan_record.id}")

        # Добавить город в scanning_cities
        await self._add_scanning_city(city, "scheduled", str(scan_record.id))
        await self._broadcast_progress()

        logger.info(
            f"Broadcasting progress: stage={self.scan_progress['stage']}, pages={self.scan_progress['pages_scraped']}, listings={self.scan_progress['listings_fetched']}"
        )

        # Background task для периодической отправки прогресса (каждую 1 секунду)
        async def periodic_progress():
            while city in self.scanning_cities:
                await asyncio.sleep(1)
                await self._broadcast_progress()

        periodic_task = asyncio.create_task(periodic_progress())

        try:
            async with async_session_maker() as db:
                scan_history_service = ScanHistoryService(db)
                listing_service = ListingService(db)
                scan_stats_service = ScanStatsService(db)

                # Парсинг страниц
                await self._update_city_progress(
                    city,
                    {
                        **self.scanning_cities[city]["progress"],
                        "stage": "fetching",
                        "is_stable": False,
                    },
                )
                await self._broadcast_progress()

                # Запускаем сканирование через HTTP (быстро и надежно)
                scraper = KufarScraper()

                base_url = f"https://re.kufar.by/l/{city}/kupit/kvartiru"
                all_listings = []
                cursor = None
                page_num = 0
                max_pages = 500  # Максимум 500 страниц (~15000 объявлений)

                while page_num < max_pages:
                    # Build URL with cursor (use ? for first param, & for subsequent)
                    url = f"{base_url}?cursor={cursor}" if cursor else base_url
                    logger.info(f"Scraping page {page_num + 1}: {url}")

                    listings, next_cursor = await scraper.scrape_page(url, city=city)

                    if not listings:
                        logger.info(f"No more listings found on page {page_num + 1}")
                        break

                    all_listings.extend(listings)

                    # Обновляем прогресс после каждой страницы
                    progress = self.scanning_cities[city]["progress"]
                    progress["pages_scraped"] = page_num + 1
                    progress["listings_fetched"] = len(all_listings)
                    progress["elapsed_seconds"] = int(
                        (
                            datetime.now(timezone.utc).replace(tzinfo=None) - start_time
                        ).total_seconds()
                    )
                    await self._update_city_progress(city, progress)
                    await self._broadcast_progress()

                    logger.info(
                        f"Page {page_num + 1}: found {len(listings)} listings, total: {len(all_listings)}"
                    )

                    # Check if there's a next cursor
                    if not next_cursor or next_cursor == cursor:
                        logger.info("No more pages")
                        break

                    cursor = next_cursor
                    page_num += 1

                    # Wait between pages to avoid rate limiting
                    await asyncio.sleep(1)

                listings_data = all_listings
                pages_scraped = page_num
                total_listings_fetched = len(listings_data)

                logger.info(
                    f"Fetching completed for {city}: {total_listings_fetched} listings from {pages_scraped} pages"
                )

                # Обновление записи сканирования
                await scan_history_service.update_scan_record(
                    scan_id=str(scan_record.id),
                    listings_fetched=total_listings_fetched,
                    pages_scraped=pages_scraped,
                )

                # === ВАЛИДАЦИЯ КОЛИЧЕСТВА ОБЪЯВЛЕНИЙ ===
                # Валидация выполняется перед транзакцией
                is_valid, validation_message, expected_count = (
                    await scan_stats_service.validate_listings_count(
                        city, total_listings_fetched, use_lock=False
                    )
                )

                if not is_valid:
                    # Аномалия: получено < 50% от ожидаемого
                    logger.error(f"Scan aborted for {city}: {validation_message}")

                    # Завершаем сканирование со статусом "error" БЕЗ upsert и mark_deleted
                    end_time = datetime.now(timezone.utc).replace(tzinfo=None)
                    await scan_history_service.complete_scan_record(
                        scan_id=str(scan_record.id),
                        status="error",
                        error_message=validation_message,
                        pages_scraped=pages_scraped,
                        duration_seconds=int((end_time - start_time).total_seconds()),
                    )

                    # Обновляем прогресс
                    await self._update_city_progress(
                        city,
                        {
                            **self.scanning_cities[city]["progress"],
                            "stage": "error",
                            "is_stable": True,
                        },
                    )
                    await self._broadcast_progress()

                    # Возвращаемся без upsert и mark_deleted
                    return

                # === ЕДИНАЯ ТРАНЗАКЦИЯ: upsert + mark_deleted + update_stats ===
                # Все три операции выполняются в одной сессии для атомарности
                # При ошибке любой операции - откат всех трёх через rollback
                try:
                    # === UPSERT В ТРАНЗАКЦИИ ===
                    await self._update_city_progress(
                        city,
                        {
                            **self.scanning_cities[city]["progress"],
                            "stage": "upserting",
                            "is_stable": False,
                        },
                    )
                    await self._broadcast_progress()

                    # Выполняем upsert в транзакции (без commit внутри)
                    stats = await listing_service.upsert_listings_no_commit(
                        listings_data, city, db
                    )

                    progress = self.scanning_cities[city]["progress"]
                    progress["listings_processed"] = stats.get("processed", 0)
                    progress["elapsed_seconds"] = int(
                        (
                            datetime.now(timezone.utc).replace(tzinfo=None) - start_time
                        ).total_seconds()
                    )
                    await self._update_city_progress(city, progress)
                    await self._broadcast_progress()

                    # === MARK DELETED (только после успешной валидации и upsert) ===
                    await self._update_city_progress(
                        city,
                        {
                            **self.scanning_cities[city]["progress"],
                            "stage": "marking_deleted",
                            "is_stable": False,
                        },
                    )
                    await self._broadcast_progress()

                    # Помечаем удалённые объявления (без commit внутри)
                    kufar_ids = stats.get("kufar_ids", set())
                    if kufar_ids:
                        deleted_count = await listing_service.mark_deleted_no_commit(
                            kufar_ids, city, db
                        )
                        stats["deleted"] = deleted_count
                        logger.info(
                            f"Marked {deleted_count} listings as deleted for {city}"
                        )
                    else:
                        stats["deleted"] = 0
                        logger.info(f"No listings to mark as deleted for {city}")

                    await self._update_city_progress(
                        city,
                        {
                            **self.scanning_cities[city]["progress"],
                            "stage": "marking_deleted_final",
                            "is_stable": True,
                        },
                    )
                    await self._broadcast_progress()

                    # === ОБНОВЛЕНИЕ СТАТИСТИКИ (в той же сессии!) ===
                    # Валидация с блокировкой для предотвращения гонок
                    await scan_stats_service.validate_listings_count(
                        city, total_listings_fetched, use_lock=True
                    )
                    await scan_stats_service.update_stats_no_commit(
                        city, total_listings_fetched, db
                    )

                    # === ЕДИНЫЙ COMMIT ВСЕХ ОПЕРАЦИЙ ===
                    await db.commit()
                    logger.info(f"Transaction committed for {city}: {stats}")

                    # Завершение записи сканирования
                    end_time = datetime.now(timezone.utc).replace(tzinfo=None)
                    await scan_history_service.complete_scan_record(
                        scan_id=str(scan_record.id),
                        status="completed",
                        listings_created=stats.get("created", 0),
                        listings_updated=stats.get("updated", 0),
                        listings_changed_byn=stats.get("changed_byn", 0),
                        listings_deleted=stats.get("deleted", 0),
                        listings_restored=stats.get("restored", 0),
                        listings_unchanged=stats.get("unchanged", 0),
                        pages_scraped=pages_scraped,
                        duration_seconds=int((end_time - start_time).total_seconds()),
                    )

                    logger.info(
                        f"Scheduled scan completed for {city}: {stats}, "
                        f"duration: {int((end_time - start_time).total_seconds())}s"
                    )

                except Exception as e:
                    logger.error(f"[Scan {scan_record.id}] Error in transaction: {e}")
                    await db.rollback()
                    logger.info(
                        f"[Scan {scan_record.id}] Transaction rolled back for {city}"
                    )
                    raise

        except Exception as e:
            logger.error(f"Scheduled scan error: {e}")
            import traceback

            traceback.print_exc()

            # Откат транзакции при ошибке
            async with async_session_maker() as db:
                scan_history_service = ScanHistoryService(db)
                await scan_history_service.complete_scan_record(
                    scan_id=str(scan_record.id),
                    status="error",
                    error_message=f"{type(e).__name__}: {str(e)}",
                )

            # Отправить ошибку через WebSocket
            if city in self.scanning_cities:
                await self._update_city_progress(
                    city,
                    {
                        **self.scanning_cities[city]["progress"],
                        "stage": "error",
                        "is_stable": True,
                    },
                )
                await self._broadcast_progress()
        finally:
            # Всегда очищать scanning_cities
            await self._remove_scanning_city(city)
            await self._broadcast_progress()
            # Отменить periodic task
            periodic_task.cancel()
            try:
                await periodic_task
            except asyncio.CancelledError:
                pass

    def stop(self):
        if self.scheduler:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped")

    async def restart_with_settings(
        self, city: str, enabled: bool, interval_minutes: int
    ):
        """Перезапуск scheduler для конкретного города."""
        # Если scheduler не создан или не запущен - создаём и запускаем
        if not self.scheduler or not self.scheduler.running:
            logger.info(f"Scheduler not running, starting fresh for {city}")
            await self.start()
            if not self.scheduler or not self.scheduler.running:
                logger.error(f"Failed to start scheduler for {city}")
                return

        job_id = f"scheduled_scan_{city}"

        # Удалить существующий job для этого города
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        # Добавить новый job если город включён
        if enabled:
            self.scheduler.add_job(
                partial(self._run_scan_scheduled, city),
                trigger=IntervalTrigger(minutes=interval_minutes),
                id=job_id,
                replace_existing=True,
            )
            logger.info(
                f"Scheduled scan enabled for {city} with interval {interval_minutes} min"
            )
        else:
            logger.info(f"Scheduled scan disabled for {city}")


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
