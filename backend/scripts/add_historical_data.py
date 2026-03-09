#!/usr/bin/env python3
"""
Script to add historical data for testing price trends.
Creates fake historical records by backdating first_seen_at for existing listings.
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import random

# Import models
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.listing import Listing, ListingStatus
from app.db.database import Base

DATABASE_URL = "postgresql+asyncpg://postgres:secret@db/kufar_monitor"


async def add_historical_data():
    """Backdate some listings to create historical data."""
    
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all active listings
        result = await session.execute(
            select(Listing).where(
                Listing.status.in_([ListingStatus.active, ListingStatus.new, ListingStatus.updated, ListingStatus.price_changed_byn]),
                Listing.price_usd > 0
            )
        )
        listings = result.scalars().all()
        
        print(f"Found {len(listings)} active listings with price_usd > 0")
        
        # Group by city and rooms
        grouped = {}
        for listing in listings:
            key = (listing.city, listing.rooms)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(listing)
        
        # For each group, backdate some listings
        total_updated = 0
        for (city, rooms), city_listings in grouped.items():
            # Sort by price to simulate price changes over time
            city_listings.sort(key=lambda x: x.price_usd)
            
            # Divide into 6 groups (one for each month)
            num_months = 6
            listings_per_month = len(city_listings) // num_months
            
            for month_idx in range(num_months):
                start_idx = month_idx * listings_per_month
                end_idx = start_idx + listings_per_month if month_idx < num_months - 1 else len(city_listings)
                
                # Backdate these listings
                days_ago = (num_months - month_idx - 1) * 30 + random.randint(1, 15)
                backdated_date = datetime.utcnow() - timedelta(days=days_ago)
                
                for listing in city_listings[start_idx:end_idx]:
                    # Adjust price slightly to simulate price changes
                    # Older listings (higher index) should have lower prices
                    price_adjustment = 1.0 - (month_idx * 0.03)  # 3% decrease per month going back
                    new_price = int(listing.price_usd * price_adjustment)
                    
                    await session.execute(
                        update(Listing)
                        .where(Listing.id == listing.id)
                        .values(
                            first_seen_at=backdated_date,
                            price_usd=new_price
                        )
                    )
                    total_updated += 1
        
        await session.commit()
        print(f"Updated {total_updated} listings with historical dates and adjusted prices")
        
        # Show summary
        for (city, rooms), city_listings in grouped.items():
            result = await session.execute(
                select(Listing.first_seen_at, Listing.price_usd)
                .where(Listing.id == city_listings[0].id)
            )
            row = result.first()
            print(f"\n{city} - {rooms} rooms:")
            print(f"  Sample: {row.first_seen_at} - ${row.price_usd}")


if __name__ == "__main__":
    asyncio.run(add_historical_data())
