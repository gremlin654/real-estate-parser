import asyncio
import math
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, List, Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import BaseModel, Field, field_validator
import redis.asyncio as redis

from app.config import settings, CITY_NAMES
from app.scraper.scheduler import get_scheduler
from app.services.scan_history_service import ScanHistoryService
from app.services.scan_settings_service import ScanSettingsService
from app.db.database import async_session_maker
from app.core.redis_client import get_redis
from app.core.redis_lock import RedisLock, RedisLockError, get_scan_lock_key
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
    scan_interval_minutes: Optional[int] = Field(
        None, ge=5, le=1440, description="Интервал сканирования в минутах (5-1440)"
    )


class AllScanSettingsResponse(BaseModel):
    """Настройки сканирования для всех городов."""

    cities: Dict[str, CitySettingsResponse]


class ScanScheduleResponse(BaseModel):
    scan_interval_minutes: int
    enabled: bool
    updated_at: Optional[str] = None


class ScanScheduleUpdateRequest(BaseModel):
    scan_interval_minutes: int = Field(
        ..., ge=5, le=1440, description="Интервал сканирования в минутах (5-1440)"
    )
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

    @field_validator("id", mode="before")
    @classmethod
    def convert_id(cls, v):
        """Конвертирует UUID в строку."""
        if isinstance(v, UUID):
            return str(v)
        return v

    @field_validator("started_at", "completed_at", mode="before")
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
    return [{"city": code, "city_name": name} for code, name in CITY_NAMES.items()]


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
            detail=f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}",
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
            detail=f"Invalid city: {city}. Must be one of: {', '.join(CITY_NAMES.keys())}",
        )

    async with async_session_maker() as db:
        scan_settings_service = ScanSettingsService(db)

        try:
            settings = await scan_settings_service.update_city_settings(
                city=city,
                enabled=request.enabled,
                interval=request.scan_interval_minutes,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Перезапуск scheduler с новыми настройками
        scheduler = get_scheduler()
        await scheduler.restart_with_settings(
            city=city,
            enabled=settings.enabled,
            interval_minutes=settings.scan_interval_minutes,
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
        detail="This endpoint is deprecated. Use /settings/{city} instead.",
    )


@router.put("/schedule", response_model=ScanScheduleResponse)
async def update_schedule(request: ScanScheduleUpdateRequest):
    """⚠️ Устаревший endpoint. Используйте /settings/{city}."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /settings/{city} instead.",
    )


@router.get("/city", response_model=CityResponse)
async def get_city():
    """⚠️ Устаревший endpoint. Используйте /settings/{city}."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /settings/{city} instead.",
    )


@router.post("/city", response_model=CityUpdateResponse)
async def update_city(request: CityUpdateRequest):
    """⚠️ Устаревший endpoint. Используйте /settings/{city}."""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /settings/{city} instead.",
    )


@router.get("/status")
async def get_status():
    """Получить статус сканирования.

    Возвращает список всех активных сканирований по городам.
    """
    scheduler = get_scheduler()
    return {
        "scanning_cities": scheduler._get_scanning_cities(),
        "scheduler_running": (
            scheduler.scheduler.running if scheduler.scheduler else False
        ),
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
    status: Optional[ScanHistoryStatus] = Query(
        default=None, description="Фильтр по статусу: running, completed, error"
    ),
    trigger_type: Optional[str] = Query(
        default=None, description="Фильтр по типу запуска: manual, scheduled"
    ),
    date_from: Optional[datetime] = Query(
        default=None, description="Дата от (ISO format)"
    ),
    date_to: Optional[datetime] = Query(
        default=None, description="Дата до (ISO format)"
    ),
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
            date_to=date_to,
        )

    total_pages = math.ceil(total / size) if size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
    }


@router.post("/trigger", response_model=ScanTriggerResponse)
async def trigger_scan(
    request: ScanTriggerRequest,
    background_tasks: BackgroundTasks,
    redis_client: redis.Redis = Depends(get_redis),
):
    """Запуск ручного сканирования - асинхронное выполнение в background

    Использует Redis distributed lock для предотвращения дублирования сканирования.
    Поддерживает параллельные сканирования для разных городов.
    Если город уже сканируется - вернёт 409 Conflict.

    Redis lock:
    - Ключ: lock:scan:{city}
    - TTL: 3600 секунд (1 час)
    - Атомарный захват через SETNX
    - Проверка owner при релизе
    """
    if request.city not in CITY_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid city: {request.city}")

    scheduler = get_scheduler()
    lock_key = get_scan_lock_key(request.city)
    scan_id = f"{request.city}:{time.time_ns()}"  # Уникальный ID

    # Попытка захватить Redis lock
    lock = RedisLock(redis_client, lock_key, timeout=600)
    acquired = await lock.acquire()

    if not acquired:
        # Проверяем кто держит lock
        current_lock = await redis_client.get(lock_key)
        logger.warning(
            f"Scan lock conflict for {request.city}. Lock holder: {current_lock}"
        )
        raise HTTPException(
            status_code=409,
            detail=f"Scanning already in progress for {request.city}. Lock: {current_lock}",
        )

    logger.info(f"Scan lock acquired for {request.city}, scan_id={scan_id}")

    # Создаем запись истории сканирования
    async with async_session_maker() as db:
        scan_history_service = ScanHistoryService(db)
        scan_record = await scan_history_service.create_scan_record(
            city=request.city,
            city_name=CITY_NAMES.get(request.city, request.city),
            trigger_type="manual",
        )

    # Запускаем сканирование в background с передачей lock для освобождения
    logger.info(f"Starting manual scan for {request.city}, scan_id: {scan_record.id}")
    background_tasks.add_task(
        _run_manual_scan,
        scheduler,
        request.city,
        str(scan_record.id),
        lock,
        lock_key,
        redis_client,
    )

    # Возвращаем статус сразу
    return ScanTriggerResponse(
        status="started",
        message="Manual scan started in background",
        city=request.city,
        city_name=CITY_NAMES.get(request.city, request.city),
    )


async def _run_manual_scan(
    scheduler, city: str, scan_id: str, lock: RedisLock, lock_key: str, redis_client
):
    """Запуск ручного сканирования

    Args:
        scheduler: Экземпляр scheduler
        city: Код города
        scan_id: ID записи сканирования
        lock: Redis lock для освобождения после завершения
    """
    from app.scraper.kufar_scraper import KufarScraper
    from app.services.listing_service import ListingService
    from app.services.scan_stats_service import ScanStatsService

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
            scan_stats_service = ScanStatsService(db)

            # Парсинг страниц
            await scheduler._update_city_progress(
                city,
                {
                    **scheduler.scanning_cities[city]["progress"],
                    "stage": "fetching",
                    "is_stable": False,
                },
            )
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
                progress["elapsed_seconds"] = int(
                    (
                        datetime.now(timezone.utc).replace(tzinfo=None) - start_time
                    ).total_seconds()
                )
                await scheduler._update_city_progress(city, progress)
                await scheduler._broadcast_progress()

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
                scan_id=scan_id,
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
                logger.error(f"Manual scan aborted for {city}: {validation_message}")

                # Завершаем сканирование со статусом "error" БЕЗ upsert и mark_deleted
                end_time = datetime.now(timezone.utc).replace(tzinfo=None)
                await scan_history_service.complete_scan_record(
                    scan_id=scan_id,
                    status="error",
                    error_message=validation_message,
                    pages_scraped=pages_scraped,
                    duration_seconds=int((end_time - start_time).total_seconds()),
                )

                # Обновляем прогресс
                await scheduler._update_city_progress(
                    city,
                    {
                        **scheduler.scanning_cities[city]["progress"],
                        "stage": "error",
                        "is_stable": True,
                    },
                )
                await scheduler._broadcast_progress()

                # Возвращаемся без upsert и mark_deleted
                return

            # === ЕДИНАЯ ТРАНЗАКЦИЯ: upsert + mark_deleted + update_stats ===
            # Все три операции выполняются в одной сессии для атомарности
            # При ошибке любой операции - откат всех трёх через rollback
            try:
                # === UPSERT В ТРАНЗАКЦИИ ===
                await scheduler._update_city_progress(
                    city,
                    {
                        **scheduler.scanning_cities[city]["progress"],
                        "stage": "upserting",
                        "is_stable": False,
                    },
                )
                await scheduler._broadcast_progress()

                # Выполняем upsert в транзакции (без commit внутри)
                stats = await listing_service.upsert_listings_no_commit(
                    listings_data, city, db
                )

                progress = scheduler.scanning_cities[city]["progress"]
                progress["listings_processed"] = stats.get("processed", 0)
                progress["elapsed_seconds"] = int(
                    (
                        datetime.now(timezone.utc).replace(tzinfo=None) - start_time
                    ).total_seconds()
                )
                await scheduler._update_city_progress(city, progress)
                await scheduler._broadcast_progress()

                # === MARK DELETED (только после успешной валидации и upsert) ===
                await scheduler._update_city_progress(
                    city,
                    {
                        **scheduler.scanning_cities[city]["progress"],
                        "stage": "marking_deleted",
                        "is_stable": False,
                    },
                )
                await scheduler._broadcast_progress()

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

                await scheduler._update_city_progress(
                    city,
                    {
                        **scheduler.scanning_cities[city]["progress"],
                        "stage": "marking_deleted_final",
                        "is_stable": True,
                    },
                )
                await scheduler._broadcast_progress()

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
                    scan_id=scan_id,
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
                    f"Manual scan completed for {city}: {stats}, "
                    f"duration: {int((end_time - start_time).total_seconds())}s"
                )

                # === ОТПРАВКА TELEGRAM УВЕДОМЛЕНИЙ ===
                # Отправляем только для CREATED объявлений
                from sqlalchemy import select
                from app.services.telegram_notification_service import (
                    TelegramNotificationService,
                )
                from app.models.listing import Listing
                from app.config import settings

                created_count = stats.get("created", 0)
                if settings.TELEGRAM_BOT_ENABLED and created_count > 0:
                    # Находим только что созданные объявления — у которых first_seen_at в пределах последних 2 минут
                    two_minutes_ago = datetime.now() - timedelta(minutes=2)
                    result = await db.execute(
                        select(Listing)
                        .where(
                            Listing.city == city,
                            Listing.first_seen_at >= two_minutes_ago,
                        )
                        .order_by(Listing.first_seen_at.desc())
                        .limit(created_count * 2)
                    )
                    new_listings = list(result.scalars().all())

                    logger.info(
                        f"Found {len(new_listings)} new listings for Telegram notifications"
                    )

                    if new_listings:
                        async with async_session_maker() as notify_db:
                            notification_service = TelegramNotificationService(
                                notify_db
                            )
                            try:
                                telegram_stats = await notification_service.send_new_listings_notifications(
                                    new_listings
                                )
                                logger.info(
                                    f"Telegram new_listing notifications: {telegram_stats['sent']} sent, "
                                    f"{telegram_stats['failed']} failed, "
                                    f"{telegram_stats['blocked']} blocked, "
                                    f"{telegram_stats['rate_limited']} rate_limited, "
                                    f"{telegram_stats['skipped_no_match']} skipped_no_match"
                                )
                            finally:
                                await notification_service.close()

                    # === ОТПРАВКА PRICE_DROP УВЕДОМЛЕНИЙ ===
                    if settings.TELEGRAM_BOT_ENABLED:
                        from sqlalchemy import select, and_
                        from app.models.listing import (
                            Listing,
                            ListingHistory,
                            EventType,
                        )

                        scan_started_at = datetime.now() - timedelta(minutes=2)
                        listing_ids_result = await db.execute(
                            select(Listing.id)
                            .where(Listing.city == city)
                            .where(Listing.last_seen_at >= scan_started_at)
                        )
                        listing_ids = [r for r in listing_ids_result.scalars().all()]

                        if listing_ids:
                            history_result = await db.execute(
                                select(ListingHistory)
                                .where(
                                    and_(
                                        ListingHistory.listing_id.in_(listing_ids),
                                        ListingHistory.event_type == EventType.price_changed,
                                        ListingHistory.created_at >= scan_started_at,
                                    ),
                                )
                                .order_by(ListingHistory.created_at.desc())
                            )
                            history_rows = list(history_result.scalars().all())

                            drop_percent_by_listing_id = {}
                            price_before_by_listing_id = {}
                            for item in history_rows:
                                if item.listing_id in drop_percent_by_listing_id:
                                    continue
                                if (
                                    item.price_before
                                    and item.price_after is not None
                                    and item.price_before > item.price_after
                                ):
                                    drop_percent = (
                                        (item.price_before - item.price_after)
                                        / item.price_before
                                    ) * 100
                                    drop_percent = round(float(drop_percent), 2)
                                    if drop_percent < settings.PRICE_CHANGE_MIN_PERCENT:
                                        continue
                                    drop_percent_by_listing_id[item.listing_id] = drop_percent
                                    price_before_by_listing_id[item.listing_id] = (
                                        item.price_before
                                    )

                            listings_result = await db.execute(
                                select(Listing).where(Listing.id.in_(listing_ids))
                            )
                            db_listings = list(listings_result.scalars().all())

                            price_drop_listings = []
                            for listing in db_listings:
                                drop_percent = drop_percent_by_listing_id.get(
                                    listing.id
                                )
                                if drop_percent is None:
                                    continue
                                # Пропускаем дубликаты
                                if any(
                                    l.id == listing.id for l in price_drop_listings
                                ):
                                    continue
                                listing.drop_percent = drop_percent
                                price_before_usd = price_before_by_listing_id.get(
                                    listing.id
                                )
                                if price_before_usd and listing.price_usd:
                                    price_drop_amount_usd = round(
                                        price_before_usd - listing.price_usd
                                    )
                                    listing.price_drop_amount = price_drop_amount_usd
                                price_drop_listings.append(listing)

                            logger.info(
                                f"Found {len(price_drop_listings)} price-drop listings for notifications"
                            )

                            if price_drop_listings:
                                async with async_session_maker() as notify_db:
                                    notification_service = TelegramNotificationService(
                                        notify_db
                                    )
                                    try:
                                        telegram_stats_drop = await notification_service.send_price_drop_notifications(
                                            price_drop_listings
                                        )
                                        logger.info(
                                            f"Telegram price_drop notifications: {telegram_stats_drop['sent']} sent, "
                                            f"{telegram_stats_drop['failed']} failed, "
                                            f"{telegram_stats_drop['blocked']} blocked, "
                                            f"{telegram_stats_drop['rate_limited']} rate_limited, "
                                            f"{telegram_stats_drop['skipped_no_match']} skipped_no_match"
                                        )
                                    finally:
                                        await notification_service.close()

            except Exception as e:
                logger.error(f"[Scan {scan_id}] Error in transaction: {e}")
                await db.rollback()
                logger.info(f"[Scan {scan_id}] Transaction rolled back for {city}")
                raise

    except Exception as e:
        logger.error(f"Manual scan error: {e}")
        import traceback

        traceback.print_exc()

        # Откат транзакции при ошибке
        async with async_session_maker() as db:
            scan_history_service = ScanHistoryService(db)
            await scan_history_service.complete_scan_record(
                scan_id=scan_id,
                status="error",
                error_message=f"{type(e).__name__}: {str(e)}",
            )

        # Отправить ошибку через WebSocket
        if city in scheduler.scanning_cities:
            await scheduler._update_city_progress(
                city,
                {
                    **scheduler.scanning_cities[city]["progress"],
                    "stage": "error",
                    "is_stable": True,
                },
            )
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
        # === ОСВОБОДИТЬ REDIS LOCK ===
        try:
            released = await lock.release()
            if released:
                logger.info(f"Scan lock released for {city}, scan_id={scan_id}")
            else:
                # Если release не сработал (owner mismatch) — принудительно удаляем
                logger.warning(f"Lock release skipped, force deleting for {city}")
                await redis_client.delete(lock_key)
                logger.info(f"Scan lock force deleted for {city}")
        except Exception as e:
            logger.error(f"Failed to release scan lock for {city}: {e}")
            # Последняя попытка — принудительно удалить
            try:
                await redis_client.delete(lock_key)
            except Exception:
                pass
