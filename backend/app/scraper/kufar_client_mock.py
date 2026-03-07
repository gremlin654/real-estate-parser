"""Mock Kufar API client for testing when real API is unavailable."""

import random
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

# Mock data templates
MOCK_TITLES = [
    "2-комнатная квартира, ул. Ленина",
    "3-комнатная квартира, пр. Независимости",
    "1-комнатная квартира, ул. Советская",
    "2-комнатная квартира, ул. Якуба Коласа",
    "3-комнатная квартира, ул. Богдановича",
    "4-комнатная квартира, ул. Мельникайте",
    "2-комнатная квартира, ул. Притыцкого",
    "1-комнатная квартира, ул. Калиновского",
    "3-комнатная квартира, ул. Сургучева",
    "2-комнатная квартира, ул. Чюрлёниса",
]

MOCK_ADDRESSES = [
    "Минск, Центральный район",
    "Минск, Советский район",
    "Минск, Первомайский район",
    "Минск, Московский район",
    "Минск, Фрунзенский район",
    "Брест, центр",
    "Гомель, центральный район",
    "Гродно, центр",
    "Витебск, центральный район",
    "Могилев, центр",
]

MOCK_IMAGES = [
    "https://content.kufar.by/image1.jpg",
    "https://content.kufar.by/image2.jpg",
    "https://content.kufar.by/image3.jpg",
]


class KufarAPIClient:
    """Mock client that generates realistic test data."""

    def __init__(self, base_url: str = "", timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        logger.warning("Using MOCK Kufar API client - generating test data")

    async def fetch_all_listings(self, max_pages: int = 2) -> list[dict]:
        """
        Generate mock listings.

        Args:
            max_pages: Number of pages to generate.

        Returns:
            List of mock listing dictionaries.
        """
        results = []
        listings_per_page = 30

        for page in range(max_pages):
            page_listings = []
            for i in range(listings_per_page):
                listing_id = page * listings_per_page + i + 1

                # Generate random data
                price = random.randint(50000, 250000)
                rooms = random.randint(1, 4)
                area = round(random.uniform(30, 120), 1)
                floor = random.randint(1, 12)

                # Generate date offset
                days_ago = random.randint(0, 30)
                created_date = datetime.now() - timedelta(days=days_ago)

                listing = {
                    "id": str(listing_id),
                    "title": random.choice(MOCK_TITLES),
                    "price": f"${price:,}",
                    "address": random.choice(MOCK_ADDRESSES),
                    "rooms": rooms,
                    "area": area,
                    "floor": floor,
                    "image": random.choice(MOCK_IMAGES),
                    "url": f"https://kufar.by/l/{listing_id}",
                    "created_at": created_date.isoformat(),
                    "raw_data": {
                        "scraped_at": datetime.now().isoformat(),
                        "source": "mock",
                    },
                }
                page_listings.append(listing)

            results.extend(page_listings)
            logger.info(f"Generated page {page + 1}, total: {len(results)} listings")

        logger.success(f"Generated {len(results)} mock listings")
        return results

    async def fetch_listing_page(self, page: int = 1) -> tuple[list[dict], bool]:
        """
        Fetch a single page of mock listings.

        Args:
            page: Page number to generate.

        Returns:
            Tuple of (listings list, has_more flag).
        """
        listings = await self.fetch_all_listings(max_pages=page)
        has_more = page < 10  # Always has more pages
        return listings, has_more
