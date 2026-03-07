import httpx
from typing import Optional
from loguru import logger


class KufarAPIClient:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        }

    async def fetch_listings(
        self, city: str = "mogilev", page: int = 1
    ) -> Optional[dict]:
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
                response = await client.get(url, params=params, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching listings: {e}")
                return None
            except Exception as e:
                logger.error(f"Error fetching listings: {e}")
                return None
