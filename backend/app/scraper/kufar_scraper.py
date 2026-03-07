"""Kufar scraper using aiohttp with cursor pagination."""

import asyncio
from typing import Optional, List, Dict, Any
import aiohttp
from loguru import logger
import json
import re
from datetime import datetime


class KufarScraper:
    """Scraper for Kufar.by that extracts data from __NEXT_DATA__ using HTTP requests."""

    def __init__(
        self,
        timeout: int = 30,
    ):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with browser-like headers."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Referer": "https://re.kufar.by/",
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "Upgrade-Insecure-Requests": "1",
                }
            )
        return self.session

    async def close(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def _extract_next_data(self, html: str) -> Optional[dict]:
        """Extract __NEXT_DATA__ from HTML."""
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not match:
            return None
        
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.error("Failed to parse __NEXT_DATA__ JSON")
            return None

    def _parse_ad(self, ad: dict, city: str = "") -> Optional[dict]:
        """Parse ad data into listing dict."""
        try:
            # Extract price - Kufar returns price_byn and price_usd directly
            price_byn = ad.get("price_byn", 0)
            price_usd = ad.get("price_usd", 0)
            currency = ad.get("currency", "BYN")
            
            # Extract location
            location = ad.get("location", {})
            address = location.get("geography", {}).get("displayName", "") if location else ""
            
            # Extract parameters - can be dict or list of dicts
            ad_params_raw = ad.get("ad_parameters", {})
            ad_params = {}
            if isinstance(ad_params_raw, dict):
                ad_params = ad_params_raw
            elif isinstance(ad_params_raw, list):
                # Convert list of dicts to single dict
                # Support both formats: {name, value} and {p, v, pl}
                for param in ad_params_raw:
                    if isinstance(param, dict):
                        # Format 1: {name, value}
                        if "name" in param:
                            name = param.get("name", "")
                            value = param.get("value", "")
                            if name:
                                ad_params[name] = value
                        # Format 2: {p, v, pl} - Kufar API format
                        elif "p" in param:
                            p_name = param.get("p", "")
                            p_value = param.get("v", "")
                            if p_name:
                                ad_params[p_name] = p_value

            # Extract rooms - use 'rooms' key from new format
            rooms_raw = ad_params.get("rooms", "")
            try:
                # rooms can be string or number
                if isinstance(rooms_raw, (int, float)):
                    rooms = int(rooms_raw)
                elif rooms_raw and str(rooms_raw).isdigit():
                    rooms = int(rooms_raw)
                else:
                    rooms = 0
            except (ValueError, TypeError):
                rooms = 0

            # Extract area - use 'size' key for total area
            area_raw = ad_params.get("size", "")
            try:
                if isinstance(area_raw, (int, float)):
                    area = float(area_raw)
                elif area_raw:
                    area = float(str(area_raw).replace(",", "."))
                else:
                    area = 0.0
            except (ValueError, TypeError):
                area = 0.0

            # Extract floor - use 'floor' key
            floor_raw = ad_params.get("floor", "")
            try:
                # floor can be array [5] or number
                if isinstance(floor_raw, list) and len(floor_raw) > 0:
                    floor = int(floor_raw[0])
                elif isinstance(floor_raw, (int, float)):
                    floor = int(floor_raw)
                elif floor_raw and str(floor_raw).isdigit():
                    floor = int(floor_raw)
                else:
                    floor = 0
            except (ValueError, TypeError):
                floor = 0

            # Extract total_floors - use 're_number_floors' key
            total_floors = None
            total_floors_raw = ad_params.get("re_number_floors", "")
            if total_floors_raw is not None and total_floors_raw != "":
                try:
                    if isinstance(total_floors_raw, (int, float)):
                        total_floors = int(total_floors_raw)
                    elif isinstance(total_floors_raw, str) and total_floors_raw.strip().isdigit():
                        total_floors = int(total_floors_raw.strip())
                    # Иначе оставляем None
                except (ValueError, TypeError):
                    # Если не удалось преобразовать, оставляем None
                    pass

            # Extract images
            images = ad.get("images", [])
            image_urls = []
            for img in images:
                if isinstance(img, dict):
                    path = img.get("path", "")
                    if path:
                        # Используем rms{kufar.by формат для картинок
                        image_urls.append(f"https://rms.kufar.by/v1/gallery/{path}")

            # Extract description from body_short
            description = ad.get("body_short", "") or ad.get("body", "")

            # Extract category
            category = ad.get("category", "")

            # Extract house_year from ad_parameters
            house_year = None
            year_built_raw = ad_params.get("year_built", "")
            try:
                if isinstance(year_built_raw, (int, float)):
                    house_year = int(year_built_raw)
                elif year_built_raw and str(year_built_raw).isdigit():
                    house_year = int(year_built_raw)
            except (ValueError, TypeError):
                pass

            # Extract district and metro if available
            district = None
            metro = None

            # Create listing
            # Kufar возвращает цены в копейках/центах (умноженные на 100)
            # Поэтому делим на 100 для получения целой цены
            price_byn_int = int(price_byn) if price_byn else 0
            price_usd_int = int(price_usd) if price_usd else 0

            ad_id = str(ad.get("ad_id", ""))

            listing = {
                "kufar_id": ad_id,
                "url": f"https://re.kufar.by/vi/{city}/kupit/kvartiru/{ad_id}" if city else f"https://re.kufar.by/vi/{ad_id}",
                "title": ad.get("subject", ""),
                "price": price_byn_int // 100 if price_byn_int > 0 else 0,
                "price_usd": price_usd_int // 100 if price_usd_int > 0 else 0,
                "currency": currency,
                "city": city,
                "address": address,
                "rooms": rooms,
                "area": area,
                "floor": floor,
                "total_floors": total_floors,
                "category": category if category else None,
                "description": description if description else None,
                "district": district,
                "metro": metro,
                "house_year": house_year,
                "images": image_urls,
                "raw_data": ad,
            }

            return listing
        except Exception as e:
            logger.error(f"Error parsing ad: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def scrape_page(
        self,
        url: str,
        city: str = "",
        max_listings: Optional[int] = None,
    ) -> tuple[list[dict], Optional[str]]:
        """
        Scrape listings from a Kufar page using HTTP request.

        Args:
            url: URL of the Kufar page to scrape.
            city: City code to associate with listings.
            max_listings: Maximum number of listings to return.

        Returns:
            Tuple of (listings list, next_cursor or None)
        """
        try:
            session = await self._get_session()
            
            logger.info(f"Fetching via HTTP: {url}")
            async with session.get(url, timeout=self.timeout) as response:
                html = await response.text()
            
            logger.info(f"HTTP HTML size: {len(html)} bytes")
            
            # Extract __NEXT_DATA__
            next_data = self._extract_next_data(html)
            if not next_data:
                logger.warning("__NEXT_DATA__ not found in HTML")
                return [], None
            
            # Extract ads from props.initialState.listing.ads
            ads = next_data.get("props", {}).get("initialState", {}).get("listing", {}).get("ads", [])
            
            # Extract cursor from pagination
            next_cursor = None
            pagination = next_data.get("props", {}).get("initialState", {}).get("listing", {}).get("pagination", [])
            if isinstance(pagination, list):
                for item in pagination:
                    if isinstance(item, dict) and item.get("label") == "next":
                        next_cursor = item.get("token")
                        break
            
            logger.info(f"Found {len(ads)} ads in __NEXT_DATA__")
            logger.info(f"Pagination items: {len(pagination) if isinstance(pagination, list) else 0}")
            logger.info(f"Next cursor: {next_cursor[:50] if next_cursor else None}...")
            
            if not ads:
                logger.warning("No ads found in __NEXT_DATA__")
                return [], None
            
            # Parse ads
            listings = []
            for ad in ads:
                try:
                    listing = self._parse_ad(ad, city=city)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.error(f"Error parsing ad: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(listings)} listings")
            
            if max_listings and len(listings) > max_listings:
                listings = listings[:max_listings]
            
            return listings, next_cursor

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return [], None
        except Exception as e:
            logger.error(f"Error scraping page: {e}")
            import traceback
            traceback.print_exc()
            return [], None

    async def scrape_all_pages(
        self,
        base_url: str,
        city: str,
        max_pages: int = 10,
    ) -> list[dict]:
        """
        Scrape all pages using cursor pagination.

        Args:
            base_url: Base URL without cursor parameter.
            city: City code.
            max_pages: Maximum number of pages to scrape.

        Returns:
            List of all listings.
        """
        all_listings = []
        cursor = None
        page_num = 0
        
        while page_num < max_pages:
            # Build URL with cursor
            url = f"{base_url}&cursor={cursor}" if cursor else base_url
            logger.info(f"Scraping page {page_num + 1}: {url}")
            
            listings, next_cursor = await self.scrape_page(url, city=city)
            
            if not listings:
                logger.info(f"No more listings found on page {page_num + 1}")
                break
            
            all_listings.extend(listings)
            logger.info(f"Page {page_num + 1}: found {len(listings)} listings, total: {len(all_listings)}")
            
            # Check if there's a next cursor
            if not next_cursor or next_cursor == cursor:
                logger.info("No more pages")
                break
            
            cursor = next_cursor
            page_num += 1
            
            # Wait between pages to avoid rate limiting
            await asyncio.sleep(1)
        
        return all_listings
