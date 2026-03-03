#!/usr/bin/env python3
"""Debug script to explore Kufar API response structure."""

import asyncio
import aiohttp
import json
from typing import Optional


async def fetch_kufar_ads(city: str = "mogilev", limit: int = 1) -> Optional[dict]:
    """Fetch ads from Kufar API."""
    base_url = "https://re.kufar.by/api/v1/search-ads"
    params = {
        "cursor": "",
        "limit": limit,
        "only_geo": 1,
        "prc": 1,
        "rg": 1124,  # Real estate category
        "region": city
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error: {response.status}")
                return None


def print_structure(obj, indent=0, max_depth=3, max_items=5):
    """Recursively print structure of dict/list."""
    prefix = "  " * indent
    
    if isinstance(obj, dict):
        print(f"{prefix}Dict with {len(obj)} keys:")
        if indent < max_depth:
            for i, (key, value) in enumerate(obj.items()):
                if i >= max_items:
                    print(f"{prefix}  ... and {len(obj) - max_items} more")
                    break
                print(f"{prefix}  {key}:", end=" ")
                if isinstance(value, (dict, list)):
                    print()
                    print_structure(value, indent + 2, max_depth, max_items)
                elif value is None:
                    print("None")
                else:
                    print(f"{type(value).__name__} = {repr(value)[:100]}")
    
    elif isinstance(obj, list):
        print(f"{prefix}List with {len(obj)} items:")
        if indent < max_depth and len(obj) > 0:
            print(f"{prefix}  First item:")
            print_structure(obj[0], indent + 2, max_depth, max_items)
            if len(obj) > 1:
                print(f"{prefix}  ... and {len(obj) - 1} more items")
    
    else:
        print(f"{prefix}{type(obj).__name__} = {repr(obj)[:100]}")


async def main():
    print("Fetching ads from Kufar API...")
    data = await fetch_kufar_ads("mogilev", 1)
    
    if data:
        print("\n=== TOP LEVEL STRUCTURE ===")
        print(f"Keys: {list(data.keys())}")
        
        print("\n=== ADS STRUCTURE ===")
        if 'ads' in data and len(data['ads']) > 0:
            ad = data['ads'][0]
            print(f"\nAd has {len(ad)} fields:")
            print_structure(ad, max_depth=2, max_items=20)
            
            print("\n=== ACCOUNT PARAMETERS ===")
            if 'account_parameters' in ad:
                for param in ad['account_parameters'][:10]:
                    print(f"  {param.get('p')}: {param.get('v')}")
            
            print("\n=== AD PARAMETERS ===")
            if 'ad_parameters' in ad:
                for param in ad['ad_parameters'][:15]:
                    print(f"  {param.get('p')}: {param.get('v')}")
            
            print("\n=== IMAGES ===")
            if 'images' in ad:
                print(f"  Number of images: {len(ad['images'])}")
                if ad['images']:
                    print(f"  First image structure:")
                    print_structure(ad['images'][0], max_depth=2)
            
            print("\n=== PRICE ===")
            print(f"  price_byn: {ad.get('price_byn')}")
            print(f"  price_usd: {ad.get('price_usd')}")
            
            print("\n=== FULL FIRST AD (JSON) ===")
            print(json.dumps(ad, indent=2, ensure_ascii=False)[:3000])
        else:
            print("No ads found")
    else:
        print("Failed to fetch data")


if __name__ == "__main__":
    asyncio.run(main())
