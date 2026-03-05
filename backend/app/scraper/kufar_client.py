import httpx
from typing import Optional
from loguru import logger


class KufarAPIClient:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def fetch_listings(self, city: str = "mogilev", page: int = 1) -> Optional[dict]:
        # Используем публичный API Kufar с параметрами города
        url = f"https://search-api.kufar.by/v1/search/rendered-paginated"
        params = {
            "category": "1010",
            "cur": "USD",
            "lang": "ru",
            "size": "30",
            "sort": "lst.d",
            "page": str(page),
            "region": city,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching listings: {e}")
                return None
            except Exception as e:
                logger.error(f"Error fetching listings: {e}")
                return None
