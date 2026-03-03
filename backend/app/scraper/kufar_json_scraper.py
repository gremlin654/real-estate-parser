import httpx
from typing import Optional, List
from loguru import logger


class KufarJSONScraper:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def fetch_page(self, city: str, page: int = 1) -> Optional[List[dict]]:
        url = "https://search-api-service.kufar.by/v2/search/rendered-paginated"
        params = {
            "category": "1010",
            "cur": "USD",
            "lang": "ru",
            "size": "30",
            "sort": "lst.d",
            "page": str(page),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("items", [])
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                return None
