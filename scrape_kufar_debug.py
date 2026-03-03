#!/usr/bin/env python3
"""Kufar scraper debug version."""

import asyncio
from playwright.async_api import async_playwright
from loguru import logger
import json


async def scrape_kufar_debug():
    """Scrape listings from Kufar with debug output."""
    
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
        
        try:
            logger.info("Navigating to Kufar...")
            response = await page.goto("https://kufar.by/l?category=1010", wait_until="domcontentloaded", timeout=60000)
            logger.info(f"Page status: {response.status}")
            
            # Get page title
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Wait for content
            await page.wait_for_timeout(8000)
            
            # Get HTML content length
            html = await page.content()
            logger.info(f"HTML length: {len(html)}")
            
            # Try to find any cards with different selectors
            selectors = [
                "[data-component='AdvertCard']",
                "[class*='AdvertCard']",
                "[class*='advert-card']",
                "[class*='card']",
                "article",
            ]
            
            for selector in selectors:
                try:
                    cards = await page.query_selector_all(selector)
                    logger.info(f"Selector '{selector}' found {len(cards)} elements")
                except Exception as e:
                    logger.warning(f"Selector '{selector}' failed: {e}")
            
            # Get all links (might contain listings)
            links = await page.query_selector_all("a[href*='/l/']")
            logger.info(f"Found {len(links)} listing links")
            
            # Extract listing URLs
            listing_urls = []
            for link in links[:10]:
                try:
                    href = await link.get_attribute("href")
                    if href and "/l/" in href:
                        listing_urls.append(href)
                        logger.info(f"Found listing URL: {href}")
                except:
                    pass
            
            # Save page content for analysis
            with open("/Users/andrey/Desktop/testing_project_ai/qwen 3.5/web/page_debug.html", "w", encoding="utf-8") as f:
                f.write(html[:50000])  # First 50KB
            logger.info("Saved page content to page_debug.html")
            
            # Take screenshot
            await page.screenshot(path="/Users/andrey/Desktop/testing_project_ai/qwen 3.5/web/page_debug.png")
            logger.info("Saved screenshot to page_debug.png")
            
            return listing_urls
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            await browser.close()


if __name__ == "__main__":
    logger.info("Starting Kufar debug scraper...")
    result = asyncio.run(scrape_kufar_debug())
    logger.info(f"Found {len(result)} listing URLs")
