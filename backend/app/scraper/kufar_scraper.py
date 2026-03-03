"""Kufar scraper using Playwright to parse HTML pages directly."""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Page
from loguru import logger
import re


class KufarScraper:
    """Scraper for Kufar.by that parses HTML pages directly."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 60000,
        scroll_delay: int = 2000,
        scroll_count: int = 5,
    ):
        self.headless = headless
        self.timeout = timeout
        self.scroll_delay = scroll_delay
        self.scroll_count = scroll_count

    async def scrape_page(
        self,
        url: str,
        max_listings: Optional[int] = None,
    ) -> list[dict]:
        """
        Scrape listings from a Kufar page.

        Args:
            url: URL of the Kufar page to scrape.
            max_listings: Maximum number of listings to return (None for all).

        Returns:
            List of parsed listing dictionaries.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-software-rasterizer",
                    "--disable-features=VizDisplayCompositor",
                ],
            )

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )

            page = await context.new_page()

            try:
                logger.info(f"Navigating to {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

                # Wait for initial content to load
                await page.wait_for_timeout(5000)

                # Scroll to trigger lazy loading
                logger.info("Scrolling to load lazy content...")
                await self._scroll_page(page)

                # Extract listings
                logger.info("Extracting listings...")
                listings = await self._extract_listings(page)

                logger.info(f"Extracted {len(listings)} listings")

                if max_listings and len(listings) > max_listings:
                    listings = listings[:max_listings]

                return listings

            except Exception as e:
                logger.error(f"Error scraping page: {e}")
                import traceback
                traceback.print_exc()
                return []
            finally:
                await browser.close()

    async def _scroll_page(self, page: Page):
        """Scroll page to trigger lazy loading of content."""
        for i in range(self.scroll_count):
            await page.evaluate(f"window.scrollTo(0, {1000 * (i + 1)})")
            await page.wait_for_timeout(self.scroll_delay)

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)

    async def _extract_listings(self, page: Page) -> list[dict]:
        """Extract all listings from the page."""
        listings_data = await page.evaluate("""
            () => {
                const listings = [];
                
                // Find all listing cards - try multiple selectors
                const cardSelectors = [
                    '[data-testid="advert"]',
                    '[class*="ListingCard"]',
                    '[class*="AdvertCard"]',
                    'article[class*="card"]',
                    'div[class*="listing"]',
                    'div[class*="advert"]',
                ];
                
                let cards = [];
                for (const selector of cardSelectors) {
                    const found = document.querySelectorAll(selector);
                    if (found.length > 0) {
                        cards = Array.from(found);
                        break;
                    }
                }
                
                // If no cards found, try to find any div with price and location
                if (cards.length === 0) {
                    const allDivs = document.querySelectorAll('div');
                    cards = Array.from(allDivs).filter(div => {
                        const text = div.textContent || '';
                        return text.includes('р.') && (text.includes('комн.') || text.includes('м²'));
                    });
                }
                
                cards.forEach((card, index) => {
                    try {
                        // Extract price
                        let price = '';
                        const priceSelectors = [
                            '[data-testid="advert-price"]',
                            '[class*="price"]',
                            '[class*="Price"]',
                        ];
                        for (const selector of priceSelectors) {
                            const el = card.querySelector(selector);
                            if (el) {
                                price = el.textContent?.trim() || '';
                                break;
                            }
                        }
                        
                        // Extract rooms
                        let rooms = '';
                        const roomsMatch = card.textContent?.match(/(\\d+)\\s*комн\\.?/);
                        if (roomsMatch) {
                            rooms = roomsMatch[1];
                        }
                        
                        // Extract area
                        let area = '';
                        const areaMatch = card.textContent?.match(/(\\d+[.,]?\\d*)\\s*м²/);
                        if (areaMatch) {
                            area = areaMatch[1];
                        }
                        
                        // Extract floor
                        let floor = '';
                        const floorMatch = card.textContent?.match(/этаж\\s*(\\d+)/);
                        if (floorMatch) {
                            floor = floorMatch[1];
                        }
                        
                        // Extract address/location
                        let address = '';
                        const addressSelectors = [
                            '[data-testid="advert-location"]',
                            '[class*="location"]',
                            '[class*="Location"]',
                            '[class*="address"]',
                        ];
                        for (const selector of addressSelectors) {
                            const el = card.querySelector(selector);
                            if (el) {
                                address = el.textContent?.trim() || '';
                                break;
                            }
                        }
                        
                        // Extract title/description
                        let title = '';
                        const titleSelectors = [
                            '[data-testid="advert-title"]',
                            '[class*="title"]',
                            '[class*="Title"]',
                        ];
                        for (const selector of titleSelectors) {
                            const el = card.querySelector(selector);
                            if (el) {
                                title = el.textContent?.trim() || '';
                                break;
                            }
                        }
                        
                        // Extract URL
                        let url = '';
                        const linkEl = card.querySelector('a[href*="/l/"]');
                        if (linkEl) {
                            url = linkEl.getAttribute('href') || '';
                            if (!url.startsWith('http')) {
                                url = 'https://re.kufar.by' + url;
                            }
                        }
                        
                        // Extract kufar_id from URL
                        let kufar_id = '';
                        const idMatch = url.match(/\\/l\\/(\\d+)/);
                        if (idMatch) {
                            kufar_id = idMatch[1];
                        }
                        
                        // Only add if we have at least price or title
                        if (price || title || kufar_id) {
                            listings.push({
                                kufar_id: kufar_id || `unknown_${index}`,
                                url: url || '',
                                title: title || 'Без названия',
                                price: price,
                                rooms: rooms,
                                area: area,
                                floor: floor,
                                address: address,
                            });
                        }
                    } catch (e) {
                        console.error('Error extracting card:', e);
                    }
                });
                
                return listings;
            }
        """)

        return listings_data

    async def scrape_with_pagination(
        self,
        base_url: str,
        max_pages: Optional[int] = None,
        max_listings_total: Optional[int] = None,
    ) -> list[dict]:
        """
        Scrape multiple pages of listings.

        Args:
            base_url: Base URL of the Kufar search page.
            max_pages: Maximum number of pages to scrape (None for unlimited).
            max_listings_total: Maximum total listings to return.

        Returns:
            List of parsed listing dictionaries.
        """
        all_listings = []
        page_num = 1

        while True:
            # Check max_pages limit
            if max_pages and page_num > max_pages:
                logger.info(f"Reached max pages limit: {max_pages}")
                break

            # Build URL with page parameter
            if page_num == 1:
                url = base_url
            else:
                # Add page parameter to URL
                separator = "&" if "?" in base_url else "?"
                url = f"{base_url}{separator}page={page_num}"

            logger.info(f"Scraping page {page_num}: {url}")
            listings = await self.scrape_page(url)

            if not listings:
                logger.info(f"No more listings found on page {page_num}")
                break

            all_listings.extend(listings)
            logger.info(f"Page {page_num}: found {len(listings)} listings, total: {len(all_listings)}")

            if max_listings_total and len(all_listings) >= max_listings_total:
                all_listings = all_listings[:max_listings_total]
                break

            # Wait between pages to avoid rate limiting
            await asyncio.sleep(2)
            page_num += 1

        logger.info(f"Scraping completed. Total listings: {len(all_listings)}")
        return all_listings


async def scrape_kufar_listings(
    url: str = "https://re.kufar.by/l/belarus/kupit/kvartiru",
    max_pages: int = 2,
    max_listings: int = 50,
) -> list[dict]:
    """
    Convenience function to scrape Kufar listings.

    Args:
        url: URL to scrape.
        max_pages: Maximum pages to scrape (default 2 for speed).
        max_listings: Maximum listings to return.

    Returns:
        List of listing dictionaries.
    """
    scraper = KufarScraper(headless=True)
    listings = await scraper.scrape_with_pagination(
        base_url=url,
        max_pages=max_pages,
        max_listings_total=max_listings,
    )
    return listings


if __name__ == "__main__":
    logger.info("Starting Kufar scraper...")
    result = asyncio.run(scrape_kufar_listings())
    logger.info(f"Scraping completed. Found {len(result)} listings.")
    
    # Print first few listings
    for i, listing in enumerate(result[:5]):
        logger.info(f"{i+1}. {listing.get('title', 'N/A')[:50]} - {listing.get('price', 'N/A')} ({listing.get('address', 'N/A')})")
