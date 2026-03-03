#!/usr/bin/env python3
"""Test script for the new Kufar JSON scraper."""

import asyncio
import sys
sys.path.insert(0, '/Users/andrey/Desktop/testing_project_ai/qwen 3.5/web/backend')

from loguru import logger
from app.scraper.kufar_json_scraper import scrape_kufar_listings
from app.scraper.parser import parse_scraper_listing


async def test_scraper():
    """Test the scraper with Mogilev rentals URL."""
    logger.info("=" * 60)
    logger.info("Testing Kufar JSON Scraper")
    logger.info("=" * 60)
    
    url = "https://re.kufar.by/l/mogilev/snyat/kvartiru"
    logger.info(f"URL: {url}")
    
    # Scrape listings
    logger.info("\n📡 Scraping listings...")
    raw_listings = await scrape_kufar_listings(
        url=url,
        max_pages=2,
        max_listings=20,
    )
    
    logger.info(f"\n✅ Found {len(raw_listings)} raw listings")
    
    # Print raw data samples
    logger.info("\n📋 Raw listing samples:")
    for i, listing in enumerate(raw_listings[:3]):
        logger.info(f"\n--- Listing {i+1} ---")
        for key, value in listing.items():
            if value:
                logger.info(f"  {key}: {value}")
    
    # Parse listings
    logger.info("\n🔧 Parsing listings...")
    parsed_listings = []
    for raw in raw_listings:
        parsed = parse_scraper_listing(raw)
        if parsed:
            parsed_listings.append(parsed)
    
    logger.info(f"✅ Parsed {len(parsed_listings)} listings")
    
    # Print parsed samples
    logger.info("\n📋 Parsed listing samples:")
    for i, listing in enumerate(parsed_listings[:3]):
        logger.info(f"\n--- Parsed {i+1} ---")
        logger.info(f"  kufar_id: {listing['kufar_id']}")
        logger.info(f"  title: {listing['title'][:50]}...")
        logger.info(f"  price: {listing['price']} BYN")
        logger.info(f"  rooms: {listing['rooms']}")
        logger.info(f"  area: {listing['area']} м²")
        logger.info(f"  floor: {listing['floor']}")
        logger.info(f"  address: {listing['address']}")
        logger.info(f"  url: {listing['url']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Test completed successfully!")
    logger.info("=" * 60)
    
    return len(parsed_listings) > 0


if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )
    
    success = asyncio.run(test_scraper())
    sys.exit(0 if success else 1)
