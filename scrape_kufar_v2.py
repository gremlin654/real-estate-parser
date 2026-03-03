#!/usr/bin/env python3
"""Kufar scraper with better waiting strategy."""

import asyncio
from playwright.async_api import async_playwright
from loguru import logger


async def scrape_kufar_v2():
    """Scrape listings from Kufar with improved strategy."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu",
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        
        page = await context.new_page()
        
        try:
            logger.info("Navigating to Kufar...")
            await page.goto("https://kufar.by/l?category=1010", wait_until="networkidle", timeout=90000)
            
            # Wait for initial load
            logger.info("Waiting for page to load...")
            await page.wait_for_timeout(10000)
            
            # Scroll multiple times to trigger lazy loading
            logger.info("Scrolling to load content...")
            for i in range(5):
                await page.evaluate(f"window.scrollTo(0, {1000 * (i+1)})")
                await page.wait_for_timeout(2000)
            
            # Scroll back up
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)
            
            # Get all hrefs that look like listing URLs
            logger.info("Extracting listing URLs...")
            listing_hrefs = await page.evaluate("""
                () => {
                    const allLinks = document.querySelectorAll('a[href]');
                    const listings = [];
                    
                    allLinks.forEach(link => {
                        const href = link.getAttribute('href');
                        const text = link.textContent?.trim() || '';
                        
                        // Look for listing URLs (not category pages)
                        if (href && href.match(/\/l\/\d+/)) {
                            const title = link.querySelector('[class*="title"]')?.textContent?.trim() || 
                                         link.querySelector('[data-testid="advert-title"]')?.textContent?.trim() ||
                                         text;
                            const price = link.querySelector('[class*="price"]')?.textContent?.trim() ||
                                         link.querySelector('[data-testid="advert-price"]')?.textContent?.trim() ||
                                         '';
                            const location = link.querySelector('[class*="location"]')?.textContent?.trim() ||
                                            link.querySelector('[data-testid="advert-location"]')?.textContent?.trim() ||
                                            '';
                            
                            if (title && !title.includes('category') && href.includes('/l/')) {
                                listings.push({
                                    href: href,
                                    title: title,
                                    price: price,
                                    location: location
                                });
                            }
                        }
                    });
                    
                    return listings;
                }
            """)
            
            logger.info(f"Found {len(listing_hrefs)} potential listings")
            
            # Deduplicate
            seen = set()
            unique_listings = []
            for listing in listing_hrefs:
                if listing['href'] not in seen:
                    seen.add(listing['href'])
                    unique_listings.append(listing)
            
            logger.info(f"Unique listings: {len(unique_listings)}")
            
            for i, listing in enumerate(unique_listings[:5]):
                logger.info(f"{i+1}. {listing['title'][:50]} - {listing['price']} ({listing['location']})")
                logger.info(f"   URL: {listing['href']}")
            
            # Save screenshot
            await page.screenshot(path="/Users/andrey/Desktop/testing_project_ai/qwen 3.5/web/kufar_listings.png", full_page=True)
            logger.info("Saved full page screenshot")
            
            return unique_listings
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            await browser.close()


if __name__ == "__main__":
    logger.info("Starting Kufar scraper v2...")
    result = asyncio.run(scrape_kufar_v2())
    logger.info(f"Scraping completed. Found {len(result)} listings.")
