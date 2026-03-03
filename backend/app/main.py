from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db.database import engine, async_session_maker
from app.models import Listing, ListingHistory, ScanHistory
from app.api.v1 import listings_router, history_router, stats_router, scan_router, export_router
from app.scraper.scheduler import init_scheduler
from app.core.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


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
            .where(ScanHistory.status == 'running')
            .values(
                status='error',
                error_message='Backend restarted - scan interrupted',
                completed_at=datetime.utcnow()
            )
        )
        await db.commit()
        logger.info("Cleaned up stuck 'running' scans")

    scheduler = init_scheduler()
    await scheduler.start()
    logger.info("Scheduler started with settings from database")

    logger.info("Application startup completed successfully")

    yield

    logger.info("Application shutdown initiated")
    scheduler.stop()
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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
