from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from typing import Optional

from app.config import settings
from app.db.database import engine, async_session_maker
from app.models import Listing, ListingHistory, ScanHistory, Favorite
from app.api.v1 import (
    listings_router,
    history_router,
    stats_router,
    scan_router,
    export_router,
    ws_router,
    cache_router,
    monitoring_router,
    deals_router,
    price_drop_router,
    favorites_router,
)
from app.scraper.scheduler import init_scheduler
from app.core.logging_config import setup_logging, get_logger
from app.core.redis_client import get_redis, close_redis, health_check_redis
from app.core.redis_watchdog import (
    start_lock_watchdog,
    stop_lock_watchdog,
    RedisLockWatchdog,
)
from app.telegram.bot import create_bot, create_dispatcher
from app.telegram.middlewares.db_session import DbSessionMiddleware

setup_logging()
logger = get_logger(__name__)

# Глобальный watchdog для очистки застрявших lock
_lock_watchdog: Optional[RedisLockWatchdog] = None

# Глобальная задача для Telegram бота
_telegram_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup initiated")

    async with engine.begin() as conn:
        await conn.run_sync(Listing.metadata.create_all)
    logger.info("Database tables created/verified")

    async with async_session_maker() as db:
        from sqlalchemy import update
        from datetime import datetime

        await db.execute(
            update(ScanHistory)
            .where(ScanHistory.status == "running")
            .values(
                status="error",
                error_message="Backend restarted - scan interrupted",
                completed_at=datetime.utcnow(),
            )
        )
        await db.commit()
        logger.info("Cleaned up stuck 'running' scans")

    # Инициализация Redis подключения
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        logger.info("Redis connection established successfully")

        # Инициализация rate limiter в scraper
        from app.scraper.kufar_scraper import kufar_scraper

        await kufar_scraper.initialize(redis_client)
        logger.info("Kufar scraper rate limiter initialized")

        # Инициализация scan_state в scheduler
        from app.scraper.scheduler import get_scheduler

        scheduler = get_scheduler()
        await scheduler.initialize(redis_client)
        logger.info("Scan scheduler initialized with Redis state")

        # Инициализация WebSocket manager с Redis
        from app.api.v1.ws import get_scan_manager

        ws_manager = get_scan_manager()
        await ws_manager.initialize(redis_client)
        logger.info("WebSocket manager initialized with Redis state")

        # Запуск watchdog для очистки застрявших lock (каждые 10 минут)
        global _lock_watchdog
        _lock_watchdog = await start_lock_watchdog(redis_client, interval_seconds=600)
        logger.info("Lock watchdog started (cleanup every 10 minutes)")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Continuing without Redis...")
        scheduler = init_scheduler()
        _lock_watchdog = None
    await scheduler.start()
    logger.info("Scheduler started with settings from database")

    # Запуск Telegram бота (если включён)
    global _telegram_task
    if settings.TELEGRAM_BOT_ENABLED and settings.TELEGRAM_BOT_TOKEN:
        try:
            bot = create_bot()
            
            # Установить shared bot для переиспользования в notification service
            from app.services.telegram_notification_service import (
                TelegramNotificationService,
            )
            TelegramNotificationService.set_shared_bot(bot)

            dp = create_dispatcher()

            # Middleware уже добавлен в create_dispatcher
            logger.info("Telegram bot middleware configured")

            # Запускаем polling в фоне
            _telegram_task = asyncio.create_task(dp.start_polling(bot))
            logger.info("Telegram bot started in polling mode")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            _telegram_task = None
    else:
        logger.info("Telegram bot disabled or token not set, skipping startup")

    logger.info("Application startup completed successfully")

    yield

    logger.info("Application shutdown initiated")
    scheduler.stop()

    # Остановка Telegram бота
    if _telegram_task:
        _telegram_task.cancel()
        try:
            await _telegram_task
        except asyncio.CancelledError:
            logger.info("Telegram bot task cancelled")
        _telegram_task = None
        logger.info("Telegram bot stopped")

    # Остановка watchdog
    if _lock_watchdog:
        await stop_lock_watchdog(_lock_watchdog)
        logger.info("Lock watchdog stopped")

    # Graceful shutdown Redis
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Error closing Redis connection: {e}")

    await engine.dispose()
    logger.info("Application shutdown completed")


app = FastAPI(
    title="Kufar Monitor API",
    description="API for monitoring Kufar.by real estate listings",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings_router, prefix=settings.API_PREFIX)
app.include_router(history_router, prefix=settings.API_PREFIX)
app.include_router(stats_router, prefix=settings.API_PREFIX)
app.include_router(scan_router, prefix=settings.API_PREFIX)
app.include_router(export_router, prefix=settings.API_PREFIX)
app.include_router(ws_router)  # WebSocket без префикса
app.include_router(cache_router, prefix=settings.API_PREFIX)
app.include_router(monitoring_router)  # Monitoring без префикса
app.include_router(deals_router, prefix=settings.API_PREFIX)  # Deal Finder
app.include_router(price_drop_router, prefix=settings.API_PREFIX)  # Price Drop Tracker
app.include_router(favorites_router, prefix=settings.API_PREFIX)  # Favorites


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
