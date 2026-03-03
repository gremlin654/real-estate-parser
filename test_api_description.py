#!/usr/bin/env python3
"""Test script to check what Kufar API returns for description field."""

import asyncio
import httpx
import json
from loguru import logger

async def test_api():
    """Test Kufar API response."""
    url = "https://search-api-service.kufar.by/v2/search/rendered-paginated"
    params = {
        "category": "1010",
        "region": "4",  # Mogilev
        "size": "5",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    
    async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:
        try:
            logger.info(f"Fetching {url}...")
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Response keys: {list(data.keys())}")
            
            # Get listings
            listings = data.get("listing", {}).get("ads", [])
            logger.info(f"Found {len(listings)} listings")
            
            if listings:
                # Check first listing
                first_ad = listings[0]
                ad_id = first_ad.get("ad_id") or first_ad.get("list_id")
                logger.info(f"\n=== First Ad ID: {ad_id} ===")
                logger.info(f"Ad keys: {list(first_ad.keys())[:30]}")
                
                # Check description
                description = first_ad.get("description")
                logger.info(f"Description field: {repr(description)}")
                
                # Check ad_parameters
                ad_params = first_ad.get("ad_parameters", [])
                logger.info(f"ad_parameters count: {len(ad_params)}")
                
                # Look for description in params
                for param in ad_params[:20]:  # First 20 params
                    param_name = param.get("p")
                    param_value = param.get("v")
                    if "desc" in str(param_name).lower() if param_name else False:
                        logger.info(f"Found param with 'desc': {param_name} = {repr(param_value)[:100]}")
                
                # Print all params for debugging
                logger.info("\n=== All ad_parameters (first 30): ===")
                for param in ad_params[:30]:
                    param_name = param.get("p")
                    param_value = param.get("v")
                    logger.info(f"  {param_name}: {repr(str(param_value)[:80])}")
                
                # Check full ad data
                logger.info("\n=== Full ad JSON (first 500 chars): ===")
                logger.info(json.dumps(first_ad, ensure_ascii=False)[:500])
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())
