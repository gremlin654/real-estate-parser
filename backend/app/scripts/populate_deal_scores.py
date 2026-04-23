"""
Скрипт для заполнения deal_score и deal_label для всех существующих активных объявлений.

Deal Score фича реализована, но поля пусты в БД для существующих объявлений.
Этот скрипт рассчитывает score для всех активных объявлений и сохраняет в БД.

Использование:
    cd backend
    python -m app.scripts.populate_deal_scores

Или через docker-compose:
    docker-compose exec backend python -m app.scripts.populate_deal_scores
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_maker
from app.models.listing import Listing, ListingStatus, ListingHistory
from app.services.deal_finder_service import DealFinderService
from app.services.deal_score_service import DealScoreService, get_deal_score_service
from app.core.redis_client import get_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_CITIES = ["minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"]

ACTIVE_STATUSES = [
    ListingStatus.active,
    ListingStatus.new,
    ListingStatus.updated,
]


async def populate_deal_scores():
    """Рассчитать и сохранить deal_score для всех активных объявлений."""

    deal_score_service = get_deal_score_service()
    updated_count = 0
    error_count = 0

    async with async_session_maker() as db:
        for city in VALID_CITIES:
            logger.info(f"Processing city: {city}")

            # Получить avg_price_per_m2 для города (без фильтра по комнатам)
            deal_finder = DealFinderService(db=db)
            try:
                avg_price_per_m2 = await deal_finder.get_avg_price_per_m2(
                    city=city, rooms=None, currency="usd"
                )
            except Exception as e:
                logger.error(f"Error getting avg_price_per_m2 for {city}: {e}")
                continue

            if not avg_price_per_m2:
                logger.warning(f"No avg_price_per_m2 for {city}, skipping")
                continue

            logger.info(f"avg_price_per_m2 for {city}: ${avg_price_per_m2:.2f}")

            # Получить все активные объявления для города
            query = select(Listing).where(
                and_(
                    Listing.city == city,
                    Listing.status.in_(ACTIVE_STATUSES),
                )
            )
            result = await db.execute(query)
            listings = result.scalars().all()

            logger.info(f"Found {len(listings)} active listings in {city}")

            if not listings:
                logger.info(f"No listings in {city}")
                continue

            # Batch запрос для drop_percent
            listing_ids = [listing.id for listing in listings]

            # Получить историю цен для всех listing_ids
            price_history_query = (
                select(
                    ListingHistory.listing_id,
                    func.max(ListingHistory.price_before).label("max_price"),
                    func.min(ListingHistory.price_after).label("min_price"),
                )
                .where(
                    and_(
                        ListingHistory.listing_id.in_(listing_ids),
                        ListingHistory.event_type.in_(
                            ["price_changed", "price_changed_byn", "edited"]
                        ),
                    )
                )
                .group_by(ListingHistory.listing_id)
            )
            history_result = await db.execute(price_history_query)
            price_history_map = {row.listing_id: row for row in history_result.all()}

            # Рассчитать deal_score для каждого
            city_updated = 0
            city_errors = 0
            for listing in listings:
                try:
                    # Получить drop_percent
                    history = price_history_map.get(listing.id)
                    if history and history.max_price and history.max_price > 0:
                        drop_percent = (
                            (history.max_price - history.min_price)
                            / history.max_price
                            * 100
                        )
                    else:
                        drop_percent = 0.0

                    # Рассчитать deal_score
                    score = await deal_score_service.calculate_score(
                        listing=listing,
                        avg_price_per_m2=avg_price_per_m2,
                        drop_percent=drop_percent,
                    )

                    label = DealScoreService.calculate_label(score)

                    # Обновить в памяти если изменилось
                    if listing.deal_score != score or listing.deal_label != label:
                        listing.deal_score = score
                        listing.deal_label = label
                        city_updated += 1

                except Exception as e:
                    logger.error(f"Error processing listing {listing.id}: {e}")
                    city_errors += 1

            # Один commit для всех объявлений города
            try:
                await db.commit()
                updated_count += city_updated
                error_count += city_errors
                logger.info(
                    f"✅ Updated {city_updated} listings in {city} ({city_errors} errors)"
                )
            except Exception as e:
                logger.error(f"Error committing updates for {city}: {e}")
                await db.rollback()

    logger.info(
        f"🎉 Done! Updated {updated_count} total listings ({error_count} errors)"
    )


if __name__ == "__main__":
    asyncio.run(populate_deal_scores())
