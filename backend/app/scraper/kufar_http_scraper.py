"""Kufar scraper using httpx and BeautifulSoup for HTML parsing."""

import httpx
from bs4 import BeautifulSoup
from typing import Optional, List
from loguru import logger
import re
import asyncio


class KufarHTTPScraper:
    """Simple HTTP scraper for Kufar.by using httpx and BeautifulSoup."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def scrape_page(
        self,
        url: str,
        max_listings: Optional[int] = None,
    ) -> List[dict]:
        """
        Scrape listings from a Kufar page.

        Args:
            url: URL of the Kufar page to scrape.
            max_listings: Maximum number of listings to return.

        Returns:
            List of parsed listing dictionaries.
        """
        try:
            logger.info(f"Fetching {url}...")
            
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                html_content = response.text
                logger.info(f"Page fetched, size: {len(html_content)} bytes")
                
                # Parse HTML
                soup = BeautifulSoup(html_content, "lxml")
                
                # Extract listings
                listings = self._extract_listings(soup, url)
                
                logger.info(f"Extracted {len(listings)} listings")
                
                if max_listings and len(listings) > max_listings:
                    listings = listings[:max_listings]
                
                return listings
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while fetching {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error scraping page: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_listings(self, soup: BeautifulSoup, base_url: str) -> List[dict]:
        """Extract all listings from parsed HTML."""
        listings = []
        
        # Kufar uses specific data attributes and class patterns
        # Strategy: Find all article/div elements with listing data
        
        # Look for elements with listing-specific attributes
        listing_containers = soup.find_all(
            lambda tag: (
                tag.name in ['article', 'div'] and
                (
                    tag.has_attr('data-testid') and 'advert' in tag.get('data-testid', '').lower() or
                    tag.has_attr('class') and any('card' in str(c).lower() or 'listing' in str(c).lower() for c in tag.get('class', [])) or
                    tag.has_attr('data-advert-id')
                )
            )
        )
        
        # If no specific containers found, try finding by price patterns
        if not listing_containers:
            # Find all elements containing price in BYN
            all_elements = soup.find_all(string=re.compile(r'\d+\s*р\.'))
            for text in all_elements:
                parent = text.parent
                # Walk up to find card container
                for _ in range(5):
                    if parent and parent.name in ['article', 'div']:
                        if parent not in listing_containers:
                            listing_containers.append(parent)
                        break
                    if parent:
                        parent = parent.parent
        
        logger.info(f"Found {len(listing_containers)} potential listing containers")
        
        for container in listing_containers:
            try:
                text = container.get_text(" ", strip=True)
                
                # Skip if no price indicator
                if "р." not in text and " $" not in text:
                    continue
                
                # Extract price in BYN (primary price)
                price = None
                price_match = re.search(r'(\d[\d\s]*)\s*р\.', text)
                if price_match:
                    price_str = price_match.group(1).replace(" ", "").replace("\u00a0", "")
                    try:
                        price = int(float(price_str))
                    except ValueError:
                        pass
                
                # If no BYN price, try USD
                if price is None:
                    usd_match = re.search(r'(\d[\d\s]*)\s*\$', text)
                    if usd_match:
                        price_str = usd_match.group(1).replace(" ", "").replace("\u00a0", "")
                        try:
                            price = int(float(price_str))
                        except ValueError:
                            pass
                
                if price is None or price == 0:
                    continue
                
                # Extract rooms
                rooms = None
                rooms_match = re.search(r'(\d+)\s*комн\.?', text)
                if rooms_match:
                    rooms = int(rooms_match.group(1))
                
                # Extract area
                area = None
                area_match = re.search(r'([\d,]+)\s*м²', text)
                if area_match:
                    try:
                        area = float(area_match.group(1).replace(",", "."))
                    except ValueError:
                        pass
                
                # Extract floor
                floor = None
                floor_match = re.search(r'этаж\s*(\d+)', text)
                if floor_match:
                    floor = int(floor_match.group(1))
                
                # Extract address - look for location elements
                address = None
                location_el = container.find(
                    lambda tag: tag.name and (
                        tag.has_attr('data-testid') and 'location' in tag.get('data-testid', '').lower() or
                        tag.has_attr('class') and any('location' in str(c).lower() for c in tag.get('class', []))
                    )
                )
                if location_el:
                    address = location_el.get_text(strip=True)
                
                # If no location element, try to find city in text
                if not address:
                    cities = ["Минск", "Гомель", "Могилёв", "Витебск", "Гродно", "Брест"]
                    for city in cities:
                        if city in text:
                            address = city
                            break
                
                # Extract title
                title = None
                title_el = container.find(
                    lambda tag: tag.name and (
                        tag.has_attr('data-testid') and 'title' in tag.get('data-testid', '').lower() or
                        tag.has_attr('class') and any('title' in str(c).lower() for c in tag.get('class', []))
                    )
                )
                if title_el:
                    title = title_el.get_text(strip=True)
                
                # Extract URL and kufar_id
                url = ""
                kufar_id = ""
                link = container.find("a", href=lambda x: x and re.search(r'/l/\d+', x))
                if link:
                    href = link.get("href", "")
                    if href:
                        if href.startswith("/"):
                            url = "https://re.kufar.by" + href
                        elif href.startswith("http"):
                            url = href
                        
                        # Extract ID from URL
                        id_match = re.search(r'/l/(\d+)', url)
                        if id_match:
                            kufar_id = id_match.group(1)
                
                # Generate ID if not found
                if not kufar_id:
                    import hashlib
                    kufar_id = hashlib.md5((url + str(price) + str(rooms)).encode()).hexdigest()[:16]
                
                # Build URL if missing
                if not url and kufar_id:
                    url = f"https://re.kufar.by/l/{kufar_id}"
                
                listings.append({
                    "kufar_id": kufar_id,
                    "url": url,
                    "title": title.strip() if title else "Без названия",
                    "price": price,
                    "rooms": rooms,
                    "area": area,
                    "floor": floor,
                    "address": address.strip() if address else "Беларусь",
                })
                
            except Exception as e:
                logger.debug(f"Error parsing container: {e}")
                continue
        
        # Deduplicate by kufar_id
        seen = set()
        unique_listings = []
        for listing in listings:
            if listing["kufar_id"] not in seen:
                seen.add(listing["kufar_id"])
                unique_listings.append(listing)
        
        logger.info(f"Extracted {len(unique_listings)} unique listings")
        return unique_listings

    async def scrape_with_pagination(
        self,
        base_url: str,
        max_pages: int = 3,
        max_listings_total: Optional[int] = None,
    ) -> List[dict]:
        """
        Scrape multiple pages of listings.

        Args:
            base_url: Base URL of the Kufar search page.
            max_pages: Maximum number of pages to scrape.
            max_listings_total: Maximum total listings to return.

        Returns:
            List of parsed listing dictionaries.
        """
        all_listings = []

        for page_num in range(1, max_pages + 1):
            # Build URL with page parameter
            if page_num == 1:
                url = base_url
            else:
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page_num}"

            logger.info(f"Scraping page {page_num}/{max_pages}: {url}")
            listings = await self.scrape_page(url)

            if not listings:
                logger.warning(f"No listings found on page {page_num}")
                break

            all_listings.extend(listings)
            logger.info(f"Page {page_num}: found {len(listings)} listings, total: {len(all_listings)}")

            if max_listings_total and len(all_listings) >= max_listings_total:
                all_listings = all_listings[:max_listings_total]
                break

            # Wait between pages to avoid rate limiting
            if page_num < max_pages:
                await asyncio.sleep(2)

        return all_listings


async def scrape_kufar_listings(
    url: str = "https://re.kufar.by/l/belarus/kupit/kvartiru",
    max_pages: int = 2,
    max_listings: int = 50,
) -> List[dict]:
    """
    Convenience function to scrape Kufar listings.

    Args:
        url: URL to scrape.
        max_pages: Maximum pages to scrape.
        max_listings: Maximum listings to return.

    Returns:
        List of listing dictionaries.
    """
    scraper = KufarHTTPScraper()
    listings = await scraper.scrape_with_pagination(
        base_url=url,
        max_pages=max_pages,
        max_listings_total=max_listings,
    )
    return listings


if __name__ == "__main__":
    logger.info("Starting Kufar HTTP scraper...")
    result = asyncio.run(scrape_kufar_listings())
    logger.info(f"Scraping completed. Found {len(result)} listings.")
    
    # Print first few listings
    for i, listing in enumerate(result[:5]):
        logger.info(f"{i+1}. {listing.get('title', 'N/A')[:50]} - {listing.get('price', 'N/A')} ({listing.get('address', 'N/A')})")
