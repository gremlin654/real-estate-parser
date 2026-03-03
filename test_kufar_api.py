#!/usr/bin/env python3
"""Test script to fetch Kufar listings from host machine."""

import asyncio
import httpx
from loguru import logger
import sys

# Add backend to path
sys.path.insert(0, '/Users/andrey/Desktop/testing_project_ai/qwen 3.5/web/backend')

async def test_kufar_api():
    """Test fetching listings from Kufar API."""
    
    # Try different API endpoints
    endpoints = [
        "https://search-api-service.kufar.by/v2/search/rendered-paginated",
        "https://api.kufar.by/listing/search",
        "https://cre.kufar.by/v1/search/rendered-paginated",
    ]
    
    params = {
        "category": "1010",
        "cur": "USD",
        "lang": "ru",
        "size": 5,
        "sort": "lst.d",
        "rgn": "",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Referer": "https://www.kufar.by/",
    }
    
    for endpoint in endpoints:
        logger.info(f"Testing endpoint: {endpoint}")
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                response = await client.get(endpoint, params=params)
                logger.info(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    listings = data.get("listing") or data.get("ads") or data.get("items") or []
                    logger.success(f"Found {len(listings)} listings!")
                    
                    if listings:
                        logger.info("Sample listing:")
                        import json
                        print(json.dumps(listings[0], indent=2, ensure_ascii=False))
                    return True
                else:
                    logger.error(f"Response: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Error: {e}")
    
    return False

if __name__ == "__main__":
    logger.info("Testing Kufar API from host machine...")
    result = asyncio.run(test_kufar_api())
    if result:
        logger.success("API is accessible from host!")
    else:
        logger.error("Could not access API from host")
