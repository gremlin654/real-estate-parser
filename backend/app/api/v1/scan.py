import asyncio
import math
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field, field_validator

from app.config import settings, CITY_NAMES
from app.scraper.scheduler import get_scheduler
from app.services.scan_history_service import ScanHistoryService
from app.services.scan_settings_service import ScanSettingsService
from app.db.database import async_session_maker
from loguru import logger

router = APIRouter(prefix="/scan", tags=["scan"])


class ScanHistoryStatus(str, Enum):
    """Статусы сканирования для валидации."""
    running = "running"
    completed = "completed"
    error = "error"


# ============== Pydantic Models ==============

class CitySettingsResponse(BaseModel):
    """Настройки сканирования для конкретного города."""
    enabled: bool
    scan_interval_minutes: int
    updated_at: Optional[str] = None


class CitySettingsUpdateRequest(BaseModel):
    """Запрос на обновление настроек сканирования для города."""
    enabled: Optional[bool] = None
    scan_interval_minutes: Optional[int] = Field(None, ge=5, le=1440, description="Интервал сканирования в минутах (5-1440)")


class AllScanSettingsResponse(BaseModel):
    """Настройки сканирования для всех городов."""
    cities: Dict[str, CitySettingsResponse]


class ScanScheduleResponse(BaseModel):
    scan_interval_minutes: int
    enabled: bool
    updated_at: Optional[str] = None


class ScanScheduleUpdateRequest(BaseModel):
    scan_interval_minutes: int = Field(..., ge=5, le=1440, description="Интервал сканирования в минутах (5-1440)")
    enabled: bool


class CityResponse(BaseModel):
    city: str
    city_name: str


class CityUpdateRequest(BaseModel):
    city: str


class CityUpdateResponse(BaseModel):
    city: str
    city_name: str
    message: str


class ScanTriggerRequest(BaseModel):
    city: str


class ScanTriggerResponse(BaseModel):
    status: str
    message: str
    city: str
    city_name: str


class ScanHistoryItem(BaseModel):
    """Элемент истории сканирования."""
    id: str
    started_at: str
    completed_at: Optional[str]
    city: str
    city_name: str
    status: str
    trigger_type: str
    listings_fetched: int
    listings_created: int
    listings_updated: int
    listings_changed_byn: int
    listings_deleted: int
    pages_scraped: int
    duration_seconds: Optional[int]
    error_message: Optional[str]

    class Config:
        from_attributes = True

    @field_validator('id', mode='before')
    @classmethod
    def convert_id(cls, v):
        """Конвертирует UUID в строку."""
        if isinstance(v, UUID):
            return str(v)
        return v

    @field_validator('started_at', 'completed_at', mode='before')
    @classmethod
    def convert_datetime(cls, v):
        """Конвертирует datetime в ISO строку."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class ScanHistoryResponse(BaseModel):
    """Пагинированный ответ истории сканирований."""
    items: List[ScanHistoryItem]
    total: int
    page: int
    size: int
    total_pages: int


# ============== Endpoints ==============


@router.get("/cities", response_model=list[CityResponse])
async def get_cities():
    """Получить список всех доступных городов."""
    return [
        {"city": code, "city_name": name}
        for code, name in CITY_NAMES.items()
    ]


@router.get("/settings", response_model=AllScanSettingsResponse)
async def get_all_settings():
    """Получить настройки сканирования для всех городов."""
    async with async_session_maker() as db:
        scan_settings_service = ScanSettingsService(db)
        all_settings = await scan_settings_service.get_all_settings()
    
    # Конвертировать в response формат
    cities = {}
    for city, settings in all_settings.items():
        cities[city] = CitySettingsResponse(
            enabled=settings.enabled,
            scan_interval_minutes=settings.scan_interval_minutes,
            updated_at=settings.updated_at.isoformat() if settings.updated_at else None,
        )
    
    return {"cities": cities}


@router.get("/settings/{city}", response_model=CitySettingsResponse)
async def get_city_settings(city: str):
    """Получить настройки сканирования для конкретного города."""
    if city not in CITY_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}"
        )
    
    async with async_session_maker() as db:
        scan_settings_service = ScanSettingsService(db)
        settings = await scan_settings_service.get_or_create_city_settings(city)
    
    return CitySettingsResponse(
        enabled=settings.enabled,
        scan_interval_minutes=settings.scan_interval_minutes,
        updated_at=settings.updated_at.isoformat() if settings.updated_at else None,
    )


@router.put("/settings/{city}", response_model=CitySettingsResponse)
async def update_city_settings(city: str, request: CitySettingsUpdateRequest):
    """Обновить настройки сканирования для конкретного города.
    
    - **enabled**: Включить/выключить автосканирование для города
    - **scan_interval_minutes**: Интервал сканирования в минутах (5-1440)
    """
    if city not in CITY_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}"
        )
    
    async with async_session_maker() as db:
        scan_settings_service = ScanSettingsService(db)
        
        try:
            settings = await scan_settings_service.update_city_settings(
                city=city,
                enabled=request.enabled,
                interval=request.scan_interval_minutes
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Перезапуск scheduler с новыми настройками
        scheduler = get_scheduler()
        await scheduler.restart_with_settings(
            city=city,
            enabled=settings.enabled,
            interval_minutes=settings.scan_interval_minutes
        )
    
    return CitySettingsResponse(
        enabled=settings.enabled,
        scan_interval_minutes=settings.scan_interval_minutes,
        updated_at=settings.updated_at.isoformat() if settings.updated_at else None,
    )


@router.get("/schedule", response_model=ScanScheduleResponse)
async def get_schedule():
    """⚠️ Устаревший endpoint. Используйте /settings/{city}."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /settings/{city} instead."
    )


@router.put("/schedule", response_model=ScanScheduleResponse)
async def update_schedule(request: ScanScheduleUpdateRequest):
    """⚠️ Устаревший endpoint. Используйте /settings/{city}."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /settings/{city} instead."
    )


@router.get("/city", response_model=CityResponse)
async def get_city():
    """⚠️ Устаревший endpoint. Используйте /settings/{city}."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /settings/{city} instead."
    )


@router.post("/city", response_model=CityUpdateResponse)
async def update_city(request: CityUpdateRequest):
    """⚠️ Устаревший endpoint. Используйте /settings/{city}."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /settings/{city} instead."
    )


@router.get("/status")
async def get_status():
    """Получить статус сканирования.
    
    Возвращает список всех активных сканирований по городам.
    """
    scheduler = get_scheduler()
    return {
        "scanning_cities": scheduler._get_scanning_cities(),
        "scheduler_running": scheduler.scheduler.running if scheduler.scheduler else False,
        "is_running": scheduler.is_running,  # Обратная совместимость
    }


@router.get("/progress")
async def get_progress():
    """Получить прогресс всех активных сканирований.
    
    Возвращает список сканируемых городов и агрегированный прогресс.
    """
    scheduler = get_scheduler()
    scanning_cities = scheduler._get_scanning_cities()
    
    # Агрегированный прогресс (обратная совместимость)
    # Используем первое сканирование или default значение
    global_progress = scheduler.scan_progress.copy()
    if scanning_cities:
        # Если есть активные сканирования, используем первое для совместимости
        global_progress = scanning_cities[0]["progress"].copy()
    
    return {
        "scanning_cities": scanning_cities,
        "global_progress": global_progress,
    }


@router.get("/history", response_model=ScanHistoryResponse)
async def get_scan_history(
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    size: int = Query(default=20, ge=1, le=100, description="Размер страницы (1-100)"),
    city: Optional[str] = Query(default=None, description="Фильтр по городу"),
    status: Optional[ScanHistoryStatus] = Query(default=None, description="Фильтр по статусу: running, completed, error"),
    trigger_type: Optional[str] = Query(default=None, description="Фильтр по типу запуска: manual, scheduled"),
    date_from: Optional[datetime] = Query(default=None, description="Дата от (ISO format)"),
    date_to: Optional[datetime] = Query(default=None, description="Дата до (ISO format)"),
):
    """
    Получение истории сканирований с пагинацией и фильтрами.

    - **page**: Номер страницы (default: 1, min: 1)
    - **size**: Размер страницы (default: 20, min: 1, max: 100)
    - **city**: Фильтр по городу (опционально)
    - **status**: Фильтр по статусу: running, completed, error (опционально)
    - **trigger_type**: Фильтр по типу запуска: manual, scheduled (опционально)
    - **date_from**: Дата от в формате ISO (опционально)
    - **date_to**: Дата до в формате ISO (опционально)

    Сортировка: started_at DESC (новые сверху)
    """
    async with async_session_maker() as db:
        scan_history_service = ScanHistoryService(db)

        items, total = await scan_history_service.get_scan_history_paginated(
            page=page,
            size=size,
            city=city,
            status=status.value if status else None,
            trigger_type=trigger_type,
            date_from=date_from,
            date_to=date_to
        )
    
    total_pages = math.ceil(total / size) if size > 0 else 0
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages
    }


@router.post("/trigger", response_model=ScanTriggerResponse)
async def trigger_scan(request: ScanTriggerRequest, background_tasks: BackgroundTasks):
    """Запуск ручного сканирования - асинхронное выполнение в background
    
    Поддерживает параллельные сканирования для разных городов.
    Если город уже сканируется - вернёт 409 Conflict.
    """
    if request.city not in CITY_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid city: {request.city}")

    scheduler = get_scheduler()

    # Проверка: если город уже сканируется - вернуть 409
    if scheduler._is_city_scanning(request.city):
        raise HTTPException(
            status_code=409, 
            detail=f"Scanning already in progress for {request.city}"
        )

    # Создаем запись истории сканирования
    async with async_session_maker() as db:
        scan_history_service = ScanHistoryService(db)
        scan_record = await scan_history_service.create_scan_record(
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

    start_time = datetime.now(timezone.utc).replace(tzinfo=None)

    # Добавить город в scanning_cities
    await scheduler._add_scanning_city(city, "manual", scan_id)
    await scheduler._broadcast_progress()

    # Background task для периодической отправки прогресса (каждую 1 секунду)
    async def periodic_progress():
        while city in scheduler.scanning_cities:
            await asyncio.sleep(1)
            await scheduler._broadcast_progress()

    periodic_task = asyncio.create_task(periodic_progress())

    try:
        async with async_session_maker() as db:
            scan_history_service = ScanHistoryService(db)
            listing_service = ListingService(db)

            # Парсинг страниц
            await scheduler._update_city_progress(city, {
                **scheduler.scanning_cities[city]["progress"],
                "stage": "fetching",
                "is_stable": False,
            })
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
                progress = scheduler.scanning_cities[city]["progress"]
                progress["pages_scraped"] = page_num + 1
                progress["listings_fetched"] = len(all_listings)
                progress["elapsed_seconds"] = int((datetime.now(timezone.utc).replace(tzinfo=None) - start_time).total_seconds())
                await scheduler._update_city_progress(city, progress)
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
            await scan_history_service.update_scan_record(
                scan_id=scan_id,
                listings_fetched=len(listings_data),
                pages_scraped=pages_scraped
            )

            # Парсинг и сохранение
            await scheduler._update_city_progress(city, {
                **scheduler.scanning_cities[city]["progress"],
                "stage": "upserting",
                "is_stable": False,
            })
            await scheduler._broadcast_progress()

            stats = await listing_service.upsert_listings(listings_data, city)

            progress = scheduler.scanning_cities[city]["progress"]
            progress["listings_processed"] = stats.get("processed", 0)
            progress["elapsed_seconds"] = int((datetime.now(timezone.utc).replace(tzinfo=None) - start_time).total_seconds())
            await scheduler._update_city_progress(city, progress)
            await scheduler._broadcast_progress()

            await scheduler._update_city_progress(city, {
                **scheduler.scanning_cities[city]["progress"],
                "stage": "marking_deleted_final",
                "is_stable": True,
            })
            await scheduler._broadcast_progress()

            # Завершение записи сканирования
            end_time = datetime.now(timezone.utc).replace(tzinfo=None)
            await scan_history_service.complete_scan_record(
                scan_id=scan_id,
                status="completed",
                listings_created=stats.get("created", 0),
                listings_updated=stats.get("updated", 0),
                listings_changed_byn=stats.get("changed_byn", 0),
                listings_deleted=stats.get("deleted", 0),
                listings_restored=stats.get("restored", 0),
                listings_unchanged=stats.get("unchanged", 0),
                pages_scraped=pages_scraped,
                duration_seconds=int((end_time - start_time).total_seconds())
            )

            logger.info(f"Manual scan completed: {stats}")

    except Exception as e:
        logger.error(f"Manual scan error: {e}")
        import traceback
        traceback.print_exc()
        async with async_session_maker() as db:
            scan_history_service = ScanHistoryService(db)
            await scan_history_service.complete_scan_record(
                scan_id=scan_id,
                status="error",
                error_message=str(e)
            )
        # Отправить ошибку через WebSocket
        if city in scheduler.scanning_cities:
            await scheduler._update_city_progress(city, {
                **scheduler.scanning_cities[city]["progress"],
                "stage": "error",
                "is_stable": True,
            })
            await scheduler._broadcast_progress()
    finally:
        # Всегда очищать scanning_cities
        await scheduler._remove_scanning_city(city)
        await scheduler._broadcast_progress()
        # Отменить periodic task
        periodic_task.cancel()
        try:
            await periodic_task
        except asyncio.CancelledError:
            pass
