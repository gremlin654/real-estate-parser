import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.config import settings, CITY_NAMES
from app.scraper.scheduler import get_scheduler
from app.services.scan_history_service import ScanHistoryService
from app.db.database import async_session_maker
from loguru import logger

router = APIRouter(prefix="/scan", tags=["scan"])


class ScanScheduleResponse(BaseModel):
    scan_interval_minutes: int
    enabled: bool
    updated_at: Optional[str] = None


class CityResponse(BaseModel):
    city: str
    city_name: str


class ScanTriggerRequest(BaseModel):
    city: str


class ScanTriggerResponse(BaseModel):
    status: str
    message: str
    city: str
    city_name: str


@router.get("/cities", response_model=list[CityResponse])
async def get_cities():
    return [
        {"city": code, "city_name": name}
        for code, name in CITY_NAMES.items()
    ]


@router.get("/schedule", response_model=ScanScheduleResponse)
async def get_schedule():
    return {
        "scan_interval_minutes": settings.SCAN_INTERVAL_MINUTES,
        "enabled": True,
        "updated_at": None,
    }


@router.get("/city")
async def get_city():
    return {
        "city": settings.KUFAR_CITY,
        "city_name": CITY_NAMES.get(settings.KUFAR_CITY, settings.KUFAR_CITY),
    }


@router.get("/status")
async def get_status():
    scheduler = get_scheduler()
    return {
        "is_scanning": scheduler.is_running,
        "scheduler_running": scheduler.scheduler.running if scheduler.scheduler else False,
    }


@router.get("/progress")
async def get_progress():
    scheduler = get_scheduler()
    return scheduler.scan_progress


@router.post("/trigger", response_model=ScanTriggerResponse)
async def trigger_scan(request: ScanTriggerRequest, background_tasks: BackgroundTasks):
    """Запуск ручного сканирования - асинхронное выполнение в background"""
    if request.city not in CITY_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid city: {request.city}")

    scheduler = get_scheduler()

    if scheduler.is_running:
        raise HTTPException(status_code=409, detail="Scanning already in progress")

    # Создаем запись истории сканирования
    async with async_session_maker() as db:
        scan_history_service = ScanHistoryService(db)
        scan_record = await scan_history_service.create_scan(
            city=request.city,
            city_name=CITY_NAMES.get(request.city, request.city),
            trigger_type="manual"
        )

    # Запускаем сканирование в background
    logger.info(f"Starting manual scan for {request.city}, scan_id: {scan_record.id}")
    background_tasks.add_task(_run_manual_scan, scheduler, request.city, str(scan_record.id))

    # Возвращаем статус сразу
    return ScanTriggerResponse(
        status="started",
        message="Manual scan started in background",
        city=request.city,
        city_name=CITY_NAMES.get(request.city, request.city)
    )


async def _run_manual_scan(scheduler, city: str, scan_id: str):
    """Запуск ручного сканирования"""
    from app.scraper.kufar_scraper import KufarScraper
    from app.services.listing_service import ListingService

    logger.info(f"Starting manual scan for {city}, scan_id: {scan_id}")

    scheduler.is_running = True
    start_time = datetime.now(timezone.utc).replace(tzinfo=None)

    scheduler.scan_progress = {
        "is_scanning": True,
        "city": city,
        "city_name": CITY_NAMES.get(city, city),
        "stage": "starting",
        "pages_scraped": 0,
        "listings_fetched": 0,
        "listings_processed": 0,
        "elapsed_seconds": 0,
        "is_stable": False,
    }
    await scheduler._broadcast_progress()

    try:
        async with async_session_maker() as db:
            scan_history_service = ScanHistoryService(db)
            listing_service = ListingService(db)

            # Парсинг страниц
            scheduler.scan_progress["stage"] = "fetching"
            scheduler.scan_progress["is_stable"] = False
            await scheduler._broadcast_progress()

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
                scheduler.scan_progress["pages_scraped"] = page_num + 1
                scheduler.scan_progress["listings_fetched"] = len(all_listings)
                scheduler.scan_progress["elapsed_seconds"] = int((datetime.now(timezone.utc).replace(tzinfo=None) - start_time).total_seconds())
                await scheduler._broadcast_progress()

                logger.info(f"Page {page_num + 1}: found {len(listings)} listings, total: {len(all_listings)}")

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

            # Обновление записи сканирования
            await scan_history_service.update_scan(
                scan_id=scan_id,
                listings_fetched=len(listings_data),
                pages_scraped=pages_scraped
            )

            # Парсинг и сохранение
            scheduler.scan_progress["stage"] = "upserting"
            scheduler.scan_progress["is_stable"] = False
            await scheduler._broadcast_progress()

            stats = await listing_service.upsert_listings(listings_data, city)

            scheduler.scan_progress["listings_processed"] = stats.get("processed", 0)
            scheduler.scan_progress["elapsed_seconds"] = int((datetime.now(timezone.utc).replace(tzinfo=None) - start_time).total_seconds())
            await scheduler._broadcast_progress()

            scheduler.scan_progress["stage"] = "marking_deleted_final"
            scheduler.scan_progress["is_stable"] = True
            await scheduler._broadcast_progress()

            # Завершение записи сканирования
            await scan_history_service.complete_scan(
                scan_id=scan_id,
                status="completed",
            )

            logger.info(f"Manual scan completed: {stats}")

    except Exception as e:
        logger.error(f"Manual scan error: {e}")
        import traceback
        traceback.print_exc()
        async with async_session_maker() as db:
            scan_history_service = ScanHistoryService(db)
            await scan_history_service.complete_scan(
                scan_id=scan_id,
                status="error",
                error_message=str(e)
            )
        # Отправить ошибку через WebSocket
        scheduler.scan_progress["stage"] = "error"
        scheduler.scan_progress["is_stable"] = True
        await scheduler._broadcast_progress()
    finally:
        scheduler.is_running = False
        scheduler.scan_progress["is_scanning"] = False
        scheduler.scan_progress["stage"] = "idle"
        scheduler.scan_progress["is_stable"] = True
        await scheduler._broadcast_progress()
