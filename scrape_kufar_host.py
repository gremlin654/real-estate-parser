#!/usr/bin/env python3
"""Kufar scraper using Playwright on host machine."""

import asyncio
from playwright.async_api import async_playwright
from loguru import logger
import json


async def scrape_kufar():
    """Scrape listings from Kufar using Playwright."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        
        page = await context.new_page()
        
        # Add stealth scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'ru'] });
        """)
        
        try:
            logger.info("Navigating to Kufar...")
            await page.goto("https://kufar.by/l?category=1010", wait_until="networkidle", timeout=60000)
            
            # Wait for content to load
            await page.wait_for_timeout(5000)
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)
            
            # Extract listings
            listings = await page.evaluate("""
                () => {
                    const cards = document.querySelectorAll(
                        "[data-component='AdvertCard'], [class*='AdvertCard'], [class*='advert-card']"
                    );
                    const results = [];
                    
                    cards.forEach(card => {
                        try {
                            const id = card.getAttribute('data-id') || 
                                       card.closest('a')?.href?.split('/').pop() ||
                                       '';
                            const title = card.querySelector('[data-testid="advert-title"]')?.textContent?.trim() 
                                || card.querySelector('[class*="title"]')?.textContent?.trim()
                                || '';
                            const price = card.querySelector('[data-testid="advert-price"]')?.textContent?.trim()
                                || card.querySelector('[class*="price"]')?.textContent?.trim()
                                || '';
                            const address = card.querySelector('[data-testid="advert-location"]')?.textContent?.trim()
                                || card.querySelector('[class*="location"]')?.textContent?.trim()
                                || '';
                            const image = card.querySelector('img')?.src || '';
                            const link = card.closest('a')?.href || '';
                            
                            if (id && title) {
                                results.push({
                                    id: id,
                                    title: title,
                                    price: price,
                                    address: address,
                                    image: image,
                                    url: link,
                                });
                            }
                        } catch (e) {
                            console.error('Error parsing card:', e);
                        }
                    });
                    
                    return results;
                }
            """)
            
            logger.info(f"Found {len(listings)} listings")
            
            if listings:
                logger.info("Sample listings:")
                for i, listing in enumerate(listings[:3]):
                    logger.info(f"{i+1}. {listing['title']} - {listing['price']} ({listing['address']})")
            
            return listings
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            
            # Take screenshot for debugging
            await page.screenshot(path="kufar_error.png")
            logger.error("Screenshot saved to kufar_error.png")
            
            return []
        finally:
            await browser.close()


if __name__ == "__main__":
    logger.info("Starting Kufar scraper on host machine...")
    result = asyncio.run(scrape_kufar())
    logger.info(f"Scraping completed. Found {len(result)} listings.")
