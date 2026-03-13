from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Literal
import io
import json
from datetime import datetime
from uuid import UUID

from app.db.database import get_db
from app.models.listing import Listing, ListingStatus
from app.models.favorite import Favorite

router = APIRouter(prefix="/export", tags=["export"])


# Типы для валидации формата экспорта
ExportFormat = Literal["csv", "xlsx", "json"]


# Заглушка для user_id (session-based, пока без реальной аутентификации)
DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


def get_user_id() -> UUID:
    """Получает ID текущего пользователя."""
    return DEFAULT_USER_ID


@router.get("/listings")
async def export_listings(
    format: ExportFormat = Query("csv", description="Export format: csv, xlsx, json"),
    city: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    conditions = []

    if not status:
        conditions.append(Listing.status != ListingStatus.deleted)
        conditions.append(Listing.status != ListingStatus.archived)
    elif status:
        conditions.append(Listing.status == ListingStatus(status))

    if city:
        conditions.append(Listing.city == city)

    query = select(Listing).where(*conditions) if conditions else select(Listing)
    result = await db.execute(query)
    listings = result.scalars().all()

    if format == "json":
        data = []
        for l in listings:
            data.append(
                {
                    "id": str(l.id),
                    "kufar_id": l.kufar_id,
                    "title": l.title,
                    "price": l.price,
                    "price_usd": l.price_usd,
                    "currency": l.currency,
                    "city": l.city,
                    "address": l.address,
                    "rooms": l.rooms,
                    "area": l.area,
                    "floor": l.floor,
                    "url": l.url,
                    "status": l.status,
                    "first_seen_at": (
                        l.first_seen_at.isoformat() if l.first_seen_at else None
                    ),
                }
            )
        return {"items": data, "total": len(listings)}

    elif format == "csv":
        output = io.StringIO()
        output.write(
            "id,kufar_id,title,price,price_usd,currency,city,rooms,area,floor,url,status\n"
        )
        for l in listings:
            output.write(
                f"{l.id},{l.kufar_id},{l.title},{l.price},{l.price_usd},{l.currency},{l.city},{l.rooms},{l.area},{l.floor},{l.url},{l.status}\n"
            )
        return {"content": output.getvalue(), "total": len(listings)}

    return {"error": "Unsupported format"}


@router.get("/favorites")
async def export_favorites(
    format: ExportFormat = Query("csv", description="Формат экспорта: csv, xlsx, json"),
    city: Optional[str] = Query(None),
    price_from: Optional[int] = Query(None),
    price_to: Optional[int] = Query(None),
    rooms: Optional[List[int]] = Query(None),
    user_id: UUID = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Экспорт избранных объявлений пользователя.

    - **format**: Формат экспорта: csv, xlsx, json
    - **city**: Фильтр по городу
    - **price_from**: Минимальная цена
    - **price_to**: Максимальная цена
    - **rooms**: Количество комнат (можно указать несколько)

    Returns:
        JSON с данными или CSV/XLSX контентом

    Raises:
        HTTPException: При неверном формате (400) или ошибке экспорта (500)
    """
    # Валидация формата (Literal уже валидирует на уровне FastAPI)
    if format not in ["csv", "xlsx", "json"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Allowed: csv, xlsx, json",
        )

    # Получаем избранные объявления пользователя
    query = select(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(query)
    favorites = result.scalars().all()

    # Извлекаем listing_id
    listing_ids = [fav.listing_id for fav in favorites]

    if not listing_ids:
        # Пустой список
        if format == "json":
            return {"items": [], "total": 0}
        elif format == "csv":
            output = io.StringIO()
            output.write(
                "id,kufar_id,title,price,price_usd,currency,city,rooms,area,floor,url,status\n"
            )
            return {"content": output.getvalue(), "total": 0}
        elif format == "xlsx":
            try:
                import pandas as pd

                df = pd.DataFrame()
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Favorites")
                output.seek(0)
                return {"content": output.getvalue(), "total": 0}
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="pandas/openpyxl not installed. Install with: pip install pandas openpyxl",
                )

    # Получаем данные объявлений
    listings_query = select(Listing).where(Listing.id.in_(listing_ids))

    # Применяем фильтры
    filters = []
    if city:
        filters.append(Listing.city == city)
    if price_from:
        filters.append(Listing.price >= price_from)
    if price_to:
        filters.append(Listing.price <= price_to)
    if rooms:
        filters.append(Listing.rooms.in_(rooms))

    if filters:
        listings_query = listings_query.where(*filters)

    result = await db.execute(listings_query)
    listings = result.scalars().all()

    if format == "json":
        data = []
        for l in listings:
            data.append(
                {
                    "id": str(l.id),
                    "kufar_id": l.kufar_id,
                    "title": l.title,
                    "price": l.price,
                    "price_usd": l.price_usd,
                    "currency": l.currency,
                    "city": l.city,
                    "address": l.address,
                    "rooms": l.rooms,
                    "area": l.area,
                    "floor": l.floor,
                    "url": l.url,
                    "status": l.status,
                    "first_seen_at": (
                        l.first_seen_at.isoformat() if l.first_seen_at else None
                    ),
                }
            )
        return {"items": data, "total": len(listings)}

    elif format == "csv":
        output = io.StringIO()
        output.write(
            "id,kufar_id,title,price,price_usd,currency,city,rooms,area,floor,url,status\n"
        )
        for l in listings:
            output.write(
                f"{l.id},{l.kufar_id},{l.title},{l.price},{l.price_usd},{l.currency},{l.city},{l.rooms},{l.area},{l.floor},{l.url},{l.status}\n"
            )
        return {"content": output.getvalue(), "total": len(listings)}

    elif format == "xlsx":
        # XLSX формат с использованием pandas
        try:
            import pandas as pd

            data = []
            for l in listings:
                data.append(
                    {
                        "ID": str(l.id),
                        "Kufar ID": l.kufar_id,
                        "Title": l.title,
                        "Price (BYN)": l.price,
                        "Price (USD)": l.price_usd,
                        "Currency": l.currency,
                        "City": l.city,
                        "Rooms": l.rooms,
                        "Area (m²)": l.area,
                        "Floor": l.floor,
                        "URL": l.url,
                        "Status": l.status,
                        "First Seen": (
                            l.first_seen_at.isoformat() if l.first_seen_at else None
                        ),
                    }
                )

            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Favorites")
                # Авто-ширина колонок
                worksheet = writer.sheets["Favorites"]
                for idx, col in enumerate(worksheet.columns, 1):
                    max_length = 0
                    column = [cell.value for cell in col if cell.value is not None]
                    if column:
                        max_length = min(max(len(str(max(column, key=len))), 50), 100)
                    worksheet.column_dimensions[chr(64 + idx)].width = max_length

            output.seek(0)
            return {"content": output.getvalue(), "total": len(listings)}
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="pandas/openpyxl not installed. Install with: pip install pandas openpyxl",
            )

    # Эта ветка никогда не будет достигнута благодаря Literal валидации
    raise HTTPException(
        status_code=400,
        detail=f"Unsupported format: {format}. Allowed: csv, xlsx, json",
    )
