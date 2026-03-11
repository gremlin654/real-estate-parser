from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy import select, func, case, text, Numeric, extract
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, List, Literal

from app.db.database import get_db
from app.models.listing import Listing, ListingStatus, ListingHistory
from app.decorators.cache import cache_response
from app.config import settings
from app.schemas.stats import PricePerM2Stats, PricePerM2Trend, PricePerM2Distribution

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary")
@cache_response(
    prefix="cache:stats:summary",
    ttl=settings.CACHE_TTL_STATS_SUMMARY,
    key_params=["city"],
)
async def get_summary(
    request: Request, city: str = Query(None), db: AsyncSession = Depends(get_db)
):
    today = datetime.utcnow().date()

    # Build base query with optional city filter
    base_filters = []
    if city:
        base_filters.append(Listing.city == city)

    new_result = await db.execute(
        select(func.count(Listing.id)).where(
            func.date(Listing.first_seen_at) == today, *base_filters
        )
    )
    new_today = new_result.scalar() or 0

    deleted_result = await db.execute(
        select(func.count(Listing.id)).where(
            func.date(Listing.deleted_at) == today,
            Listing.status == ListingStatus.deleted,
            *base_filters,
        )
    )
    deleted_today = deleted_result.scalar() or 0

    # Count price changes today (USD)
    price_changed_filters = base_filters.copy() if city else []
    price_changed_result = await db.execute(
        select(func.count(ListingHistory.id))
        .where(
            ListingHistory.event_type == "price_changed",
            func.date(ListingHistory.created_at) == today,
            ListingHistory.price_before.isnot(None),
            ListingHistory.price_after.isnot(None),
            *price_changed_filters,
        )
        .join(Listing, ListingHistory.listing_id == Listing.id)
    )
    price_changed_usd_today = price_changed_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Listing.id)).where(
            Listing.status.in_(
                [
                    ListingStatus.active,
                    ListingStatus.new,
                    ListingStatus.updated,
                    ListingStatus.price_changed_byn,
                ]
            ),
            *base_filters,
        )
    )
    active_total = active_result.scalar() or 0

    # Вычисляем среднюю цену за м²
    avg_price_per_m2_byn = None
    avg_price_per_m2_usd = None
    avg_price_per_m2_by_rooms = None
    
    if city:
        # Средняя цена за м² в BYN
        avg_byn_result = await db.execute(
            select(func.avg(Listing.price_per_m2_byn)).where(
                Listing.price_per_m2_byn.isnot(None),
                Listing.city == city,
                Listing.status.in_([
                    ListingStatus.active,
                    ListingStatus.new,
                    ListingStatus.updated,
                    ListingStatus.price_changed_byn,
                ]),
            )
        )
        avg_byn = avg_byn_result.scalar()
        if avg_byn:
            avg_price_per_m2_byn = round(float(avg_byn), 2)
        
        # Средняя цена за м² в USD
        avg_usd_result = await db.execute(
            select(func.avg(Listing.price_per_m2_usd)).where(
                Listing.price_per_m2_usd.isnot(None),
                Listing.city == city,
                Listing.status.in_([
                    ListingStatus.active,
                    ListingStatus.new,
                    ListingStatus.updated,
                    ListingStatus.price_changed_byn,
                ]),
            )
        )
        avg_usd = avg_usd_result.scalar()
        if avg_usd:
            avg_price_per_m2_usd = round(float(avg_usd), 2)
        
        # Средняя цена за м² по комнатам
        rooms_result = await db.execute(
            select(
                Listing.rooms,
                func.avg(Listing.price_per_m2_usd).label("avg_price")
            ).where(
                Listing.price_per_m2_usd.isnot(None),
                Listing.city == city,
                Listing.status.in_([
                    ListingStatus.active,
                    ListingStatus.new,
                    ListingStatus.updated,
                    ListingStatus.price_changed_byn,
                ]),
                Listing.rooms >= 1,
            ).group_by(Listing.rooms)
        )
        rooms_rows = rooms_result.all()
        if rooms_rows:
            avg_price_per_m2_by_rooms = {
                str(row.rooms): round(float(row.avg_price), 2) 
                for row in rooms_rows if row.avg_price
            }

    return {
        "new_today": new_today,
        "deleted_today": deleted_today,
        "price_changed_usd_today": price_changed_usd_today,
        "price_changed_byn_today": 0,
        "active_total": active_total,
        "archived_total": 0,
        "avg_price_per_m2_byn": avg_price_per_m2_byn,
        "avg_price_per_m2_usd": avg_price_per_m2_usd,
        "avg_price_per_m2_by_rooms": avg_price_per_m2_by_rooms,
    }


@router.get("/price-trends")
@cache_response(
    prefix="cache:stats:price-trends",
    ttl=settings.CACHE_TTL_STATS_OTHER,
    key_params=["city", "rooms", "period_months"],
)
async def get_price_trends(
    request: Request,
    city: str = Query(...),
    rooms: int = Query(2),
    period_months: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
):
    """Динамика цен по месяцам для выбранной комнаты"""
    from sqlalchemy import text, Numeric

    # Get data from listing_history snapshot for created events
    # Use func.extract for PostgreSQL
    year_col = func.extract("year", ListingHistory.created_at).label("year")
    month_col = func.extract("month", ListingHistory.created_at).label("month")

    query = (
        select(
            year_col,
            month_col,
            func.avg(
                func.cast(ListingHistory.snapshot["price_usd"].astext, Numeric)
            ).label("avg_price"),
            func.count(Listing.id).label("count"),
        )
        .join(Listing, ListingHistory.listing_id == Listing.id)
        .where(
            ListingHistory.event_type == "created",
            Listing.city == city,
            Listing.rooms == rooms,
            ListingHistory.snapshot["price_usd"].astext != "null",
            ListingHistory.created_at
            >= text(f"NOW() - INTERVAL '{period_months} months'"),
        )
        .group_by(
            year_col,
            month_col,
        )
        .order_by(
            year_col,
            month_col,
        )
    )

    result = await db.execute(query)
    rows = result.all()

    data = [
        {
            "year": int(row.year),
            "month": int(row.month),
            "avg_price_usd": round(float(row.avg_price), 2) if row.avg_price else 0,
            "listings_count": row.count,
        }
        for row in rows
    ]

    return {
        "city": city,
        "rooms": rooms,
        "period_months": period_months,
        "data": data,
    }


@router.get("/room-distribution")
@cache_response(
    prefix="cache:stats:room-distribution",
    ttl=settings.CACHE_TTL_STATS_OTHER,
    key_params=["city"],
)
async def get_room_distribution(
    request: Request, city: str = Query(...), db: AsyncSession = Depends(get_db)
):
    """Распределение по комнатам"""
    query = (
        select(
            Listing.rooms,
            func.count(Listing.id).label("count"),
            func.avg(Listing.price_usd).label("avg_price"),
        )
        .where(
            Listing.city == city,
            Listing.status.in_(
                [
                    ListingStatus.active,
                    ListingStatus.new,
                    ListingStatus.updated,
                    ListingStatus.price_changed_byn,
                ]
            ),
            Listing.rooms >= 1,  # Все комнаты от 1 и больше
        )
        .group_by(
            Listing.rooms,
        )
        .order_by(
            Listing.rooms,
        )
    )

    result = await db.execute(query)
    rows = result.all()

    data = [
        {
            "rooms": row.rooms,
            "count": row.count,
            "avg_price": round(float(row.avg_price), 2) if row.avg_price else 0,
        }
        for row in rows
    ]

    return {
        "city": city,
        "data": data,
    }


@router.get("/daily-activity")
@cache_response(
    prefix="cache:stats:daily-activity",
    ttl=settings.CACHE_TTL_STATS_OTHER,
    key_params=["city", "period_days"],
)
async def get_daily_activity(
    request: Request,
    city: str = Query(...),
    period_days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Ежедневная активность (новые, удалённые, изменения цены)"""
    from sqlalchemy import case, text

    # Get activity from listing_history
    query = (
        select(
            func.date(ListingHistory.created_at).label("date"),
            func.sum(
                case(
                    (ListingHistory.event_type == "created", 1),
                    else_=0,
                )
            ).label("new_count"),
            func.sum(
                case(
                    (ListingHistory.event_type == "deleted", 1),
                    else_=0,
                )
            ).label("deleted_count"),
            func.sum(
                case(
                    (ListingHistory.event_type == "price_changed", 1),
                    else_=0,
                )
            ).label("price_changed_count"),
        )
        .join(Listing, ListingHistory.listing_id == Listing.id)
        .where(
            Listing.city == city,
            ListingHistory.created_at >= text(f"NOW() - INTERVAL '{period_days} days'"),
        )
        .group_by(
            func.date(ListingHistory.created_at),
        )
        .order_by(
            func.date(ListingHistory.created_at),
        )
    )

    result = await db.execute(query)
    rows = result.all()

    data = [
        {
            "date": str(row.date),
            "new_count": row.new_count or 0,
            "deleted_count": row.deleted_count or 0,
            "price_changed_count": row.price_changed_count or 0,
        }
        for row in rows
    ]

    return {
        "city": city,
        "period_days": period_days,
        "data": data,
    }


@router.get("/price-per-m2", response_model=PricePerM2Stats)
@cache_response(
    prefix="cache:stats:price_per_m2",
    ttl=settings.CACHE_TTL_STATS_OTHER,
    key_params=["city", "rooms", "currency"],
)
async def get_price_per_m2_stats(
    request: Request,
    city: str = Query(
        ..., description="Город (minsk, mogilev, grodno, brest, gomel, vitebsk)"
    ),
    rooms: Optional[int] = Query(None, ge=1, le=10, description="Количество комнат"),
    date_from: Optional[datetime] = Query(None, description="Дата от"),
    date_to: Optional[datetime] = Query(None, description="Дата до"),
    currency: Literal["byn", "usd"] = Query("usd", description="Валюта (byn/usd)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить статистику цены за м²: average, median, min, max, count.

    - **city**: Город для анализа
    - **rooms**: Фильтр по количеству комнат (опционально)
    - **date_from**: Дата начала периода (опционально)
    - **date_to**: Дата окончания периода (опционально)
    - **currency**: Валюта для расчёта (byn или usd)
    """
    # Определяем колонку цены в зависимости от валюты
    price_col = (
        Listing.price_per_m2_byn if currency == "byn" else Listing.price_per_m2_usd
    )

    # Базовые фильтры
    filters = [
        price_col.isnot(None),
        Listing.city == city,
        Listing.status.in_(
            [
                ListingStatus.active,
                ListingStatus.new,
                ListingStatus.updated,
                ListingStatus.price_changed_byn,
            ]
        ),
    ]

    if rooms is not None:
        filters.append(Listing.rooms == rooms)

    if date_from is not None:
        filters.append(Listing.first_seen_at >= date_from)

    if date_to is not None:
        filters.append(Listing.first_seen_at <= date_to)

    # Запрос статистики
    query = select(
        func.avg(price_col).label("average"),
        func.percentile_cont(0.5).within_group(price_col.asc()).label("median"),
        func.min(price_col).label("min"),
        func.max(price_col).label("max"),
        func.count(Listing.id).label("count"),
    ).where(*filters)

    result = await db.execute(query)
    row = result.first()

    if not row or row.count == 0:
        raise HTTPException(
            status_code=404, detail="Нет данных для указанных параметров"
        )

    return PricePerM2Stats(
        average=round(float(row.average), 2) if row.average else 0,
        median=round(float(row.median), 2) if row.median else 0,
        min=round(float(row.min), 2) if row.min else 0,
        max=round(float(row.max), 2) if row.max else 0,
        count=row.count,
        currency=currency,
    )


@router.get("/price-per-m2-trends", response_model=List[PricePerM2Trend])
@cache_response(
    prefix="cache:stats:price_per_m2_trends",
    ttl=settings.CACHE_TTL_STATS_OTHER,
    key_params=["city", "rooms", "period_days", "interval", "currency"],
)
async def get_price_per_m2_trends(
    request: Request,
    city: str = Query(..., description="Город"),
    rooms: Optional[int] = Query(None, ge=1, le=10, description="Количество комнат"),
    period_days: int = Query(30, ge=1, le=365, description="Период в днях"),
    interval: Literal["day", "week", "month"] = Query(
        "day", description="Интервал группировки"
    ),
    currency: Literal["byn", "usd"] = Query("usd", description="Валюта"),
    db: AsyncSession = Depends(get_db),
):
    """
    Динамика изменения цены за м² по времени.

    - **interval**: day - по дням, week - по неделям, month - по месяцам
    """
    # Определяем колонку цены
    price_col = (
        Listing.price_per_m2_byn if currency == "byn" else Listing.price_per_m2_usd
    )

    # Базовые фильтры
    filters = [
        price_col.isnot(None),
        Listing.city == city,
        Listing.status.in_(
            [
                ListingStatus.active,
                ListingStatus.new,
                ListingStatus.updated,
                ListingStatus.price_changed_byn,
            ]
        ),
        Listing.first_seen_at >= text(f"NOW() - INTERVAL '{period_days} days'"),
    ]

    if rooms is not None:
        filters.append(Listing.rooms == rooms)

    # Определяем функцию для группировки по времени
    if interval == "day":
        date_trunc = func.date(Listing.first_seen_at).label("date")
    elif interval == "week":
        date_trunc = func.date_trunc("week", Listing.first_seen_at).label("date")
    else:  # month
        date_trunc = func.date_trunc("month", Listing.first_seen_at).label("date")

    # Запрос трендов
    query = (
        select(
            date_trunc,
            func.avg(price_col).label("average"),
            func.percentile_cont(0.5).within_group(price_col.asc()).label("median"),
            func.count(Listing.id).label("count"),
        )
        .where(*filters)
        .group_by(date_trunc)
        .order_by(text("date ASC"))
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        PricePerM2Trend(
            date=str(row.date),
            average=round(float(row.average), 2) if row.average else 0,
            median=round(float(row.median), 2) if row.median else 0,
            count=row.count,
        )
        for row in rows
    ]


@router.get("/price-per-m2-distribution", response_model=List[PricePerM2Distribution])
@cache_response(
    prefix="cache:stats:price_per_m2_distribution",
    ttl=settings.CACHE_TTL_STATS_OTHER,
    key_params=["city", "rooms", "bins", "currency"],
)
async def get_price_per_m2_distribution(
    request: Request,
    city: str = Query(..., description="Город"),
    rooms: Optional[int] = Query(None, ge=1, le=10, description="Количество комнат"),
    bins: int = Query(10, ge=5, le=50, description="Количество бинов"),
    currency: Literal["byn", "usd"] = Query("usd", description="Валюта"),
    db: AsyncSession = Depends(get_db),
):
    """
    Распределение цены за м² (гистограмма).

    Разбивает диапазон цен на равные интервалы (бины) и показывает количество объявлений в каждом.
    """
    # Определяем колонку цены
    price_col = (
        Listing.price_per_m2_byn if currency == "byn" else Listing.price_per_m2_usd
    )

    # Базовые фильтры
    filters = [
        price_col.isnot(None),
        Listing.city == city,
        Listing.status.in_(
            [
                ListingStatus.active,
                ListingStatus.new,
                ListingStatus.updated,
                ListingStatus.price_changed_byn,
            ]
        ),
    ]

    if rooms is not None:
        filters.append(Listing.rooms == rooms)

    # Получаем все значения цены
    query = select(price_col).where(*filters)
    result = await db.execute(query)
    prices = [row[0] for row in result.all() if row[0] is not None]

    if not prices:
        raise HTTPException(
            status_code=404, detail="Нет данных для указанных параметров"
        )

    price_min = min(prices)
    price_max = max(prices)
    total_count = len(prices)

    # Рассчитываем размер бина
    bin_size = (price_max - price_min) / bins if price_max > price_min else 1

    # Распределяем по бинам
    bin_counts = [0] * bins
    for price in prices:
        # Определяем индекс бина
        bin_index = int((price - price_min) / bin_size)
        # Для максимального значения последний бин
        if bin_index >= bins:
            bin_index = bins - 1
        bin_counts[bin_index] += 1

    # Формируем результат
    distribution = []
    for i in range(bins):
        bin_min = price_min + (i * bin_size)
        bin_max = price_min + ((i + 1) * bin_size)
        count = bin_counts[i]

        distribution.append(
            PricePerM2Distribution(
                range_min=round(bin_min, 2),
                range_max=round(bin_max, 2),
                count=count,
                percentage=(
                    round((count / total_count) * 100, 2) if total_count > 0 else 0
                ),
            )
        )

    return distribution
