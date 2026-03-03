from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.config import settings, CITY_NAMES
from app.scraper.scheduler import get_scheduler

router = APIRouter(prefix="/scan", tags=["scan"])


class ScanScheduleResponse(BaseModel):
    scan_interval_minutes: int
    enabled: bool
    updated_at: Optional[str] = None


class CityResponse(BaseModel):
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
