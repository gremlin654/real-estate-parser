"""
Тесты для KufarAPIClient
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.scraper.kufar_client import KufarAPIClient, BASE_URL, DEFAULT_PARAMS, HEADERS, SEARCH_URLS


@pytest.mark.asyncio
class TestKufarAPIClientInit:
    """Тесты инициализации KufarAPIClient."""

    def test_init_default(self):
        """Проверка инициализации с параметрами по умолчанию."""
        client = KufarAPIClient()

        assert client.base_url == BASE_URL
        assert client.timeout == 30.0
        assert client.use_scraper is True
        assert client.scraper_url == SEARCH_URLS["buy_apartments"]

    def test_init_custom_params(self):
        """Проверка инициализации с кастомными параметрами."""
        custom_url = "https://custom.url"
        client = KufarAPIClient(
            base_url=custom_url,
            timeout=60.0,
            use_scraper=False,
            scraper_url=SEARCH_URLS["rent_apartments"],
        )

        assert client.base_url == custom_url
        assert client.timeout == 60.0
        assert client.use_scraper is False
        assert client.scraper_url == SEARCH_URLS["rent_apartments"]


@pytest.mark.asyncio
class TestKufarAPIClientFetchAll:
    """Тесты метода fetch_all_listings."""

    async def test_fetch_all_via_scraper(self):
        """Проверка получения данных через скрапер."""
        client = KufarAPIClient(use_scraper=True)

        mock_listings = [
            {"id": 1, "title": "Listing 1"},
            {"id": 2, "title": "Listing 2"},
        ]

        with patch('app.scraper.kufar_client.scrape_html', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_listings

            result = await client.fetch_all_listings(max_pages=3)

            assert result == mock_listings
            mock_scrape.assert_called_once()

    async def test_fetch_all_via_scraper_fallback_to_api(self):
        """Проверка fallback на API при ошибке скрапера."""
        client = KufarAPIClient(use_scraper=True)

        mock_api_listings = [{"id": 1, "title": "API Listing"}]

        with patch('app.scraper.kufar_client.scrape_html', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = Exception("Scraper failed")

            with patch.object(client, '_fetch_via_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = mock_api_listings

                result = await client.fetch_all_listings(max_pages=3)

                assert result == mock_api_listings
                assert client.use_scraper is False  # Переключился на API
                mock_scrape.assert_called_once()
                mock_api.assert_called_once()

    async def test_fetch_all_via_api(self):
        """Проверка получения данных через API."""
        client = KufarAPIClient(use_scraper=False)

        mock_listings = [
            {"id": 1, "title": "Listing 1"},
            {"id": 2, "title": "Listing 2"},
        ]

        with patch.object(client, '_fetch_via_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_listings

            result = await client.fetch_all_listings(max_pages=3)

            assert result == mock_listings
            mock_api.assert_called_once()


@pytest.mark.asyncio
class TestKufarAPIClientFetchViaScraper:
    """Тесты метода _fetch_via_scraper."""

    async def test_fetch_via_scraper_success(self):
        """Проверка успешного получения через скрапер."""
        client = KufarAPIClient()

        mock_listings = [
            {"id": 1, "title": "Listing 1"},
            {"id": 2, "title": "Listing 2"},
            {"id": 3, "title": "Listing 3"},
        ]

        with patch('app.scraper.kufar_client.scrape_html', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = mock_listings

            result = await client._fetch_via_scraper(max_pages=2)

            assert result == mock_listings
            mock_scrape.assert_called_once_with(
                url=client.scraper_url,
                max_pages=2,
                max_listings=60,  # 2 * 30
            )

    async def test_fetch_via_scraper_error_fallback(self):
        """Проверка обработки ошибки скрапера."""
        client = KufarAPIClient()

        with patch('app.scraper.kufar_client.scrape_html', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.side_effect = Exception("Network error")

            with patch.object(client, '_fetch_via_api', new_callable=AsyncMock) as mock_api:
                mock_api.return_value = []

                result = await client._fetch_via_scraper(max_pages=1)

                assert result == []
                assert client.use_scraper is False


@pytest.mark.asyncio
class TestKufarAPIClientFetchViaApi:
    """Тесты метода _fetch_via_api."""

    async def test_fetch_via_api_single_page(self):
        """Проверка получения одной страницы через API."""
        client = KufarAPIClient(use_scraper=False)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "listing": [{"id": 1}, {"id": 2}],
            "hasMore": False,
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client._fetch_via_api(max_pages=1)

            assert len(result) == 2
            mock_client.get.assert_called_once()

    async def test_fetch_via_api_multiple_pages(self):
        """Проверка получения нескольких страниц через API."""
        client = KufarAPIClient(use_scraper=False)

        mock_responses = [
            MagicMock(json=MagicMock(return_value={"listing": [{"id": 1}], "hasMore": True})),
            MagicMock(json=MagicMock(return_value={"listing": [{"id": 2}], "hasMore": False})),
        ]
        for resp in mock_responses:
            resp.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = mock_responses
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client._fetch_via_api(max_pages=2)

            assert len(result) == 2
            assert mock_client.get.call_count == 2

    async def test_fetch_via_api_http_error(self):
        """Проверка обработки HTTP ошибки."""
        client = KufarAPIClient(use_scraper=False)

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=MagicMock()
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client._fetch_via_api(max_pages=3)

            assert result == []

    async def test_fetch_via_api_invalid_json(self):
        """Проверка обработки невалидного JSON."""
        client = KufarAPIClient(use_scraper=False)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client._fetch_via_api(max_pages=1)

            assert result == []

    async def test_fetch_via_api_no_more_listings(self):
        """Проверка остановки при отсутствии данных."""
        client = KufarAPIClient(use_scraper=False)

        mock_response = MagicMock()
        mock_response.json.return_value = {"listing": [], "hasMore": False}
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client._fetch_via_api(max_pages=3)

            assert result == []

    async def test_fetch_via_api_different_response_formats(self):
        """Проверка обработки разных форматов ответа."""
        client = KufarAPIClient(use_scraper=False)

        # Тест с разными ключами
        test_cases = [
            {"ads": [{"id": 1}], "has_more": True},
            {"items": [{"id": 2}], "hasMore": True},
            {"listing": [{"id": 3}], "hasMore": False},
        ]

        for i, data in enumerate(test_cases):
            mock_response = MagicMock()
            mock_response.json.return_value = data
            mock_response.raise_for_status = MagicMock()

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get.return_value = mock_response
                mock_client.__aenter__.return_value = mock_client
                mock_client_class.return_value = mock_client

                result = await client._fetch_via_api(max_pages=1)
                assert len(result) == 1
                assert result[0]["id"] == i + 1

    async def test_fetch_via_api_stops_when_no_has_more(self):
        """Проверка остановки когда hasMore=False."""
        client = KufarAPIClient(use_scraper=False)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "listing": [{"id": 1}],
            "hasMore": False,
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client._fetch_via_api(max_pages=5)

            # Должна остановиться после первой страницы
            assert len(result) == 1
            mock_client.get.assert_called_once()

    async def test_fetch_via_api_stops_when_less_than_size(self):
        """Проверка остановки когда получено меньше чем size."""
        client = KufarAPIClient(use_scraper=False)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "listing": [{"id": 1}],  # Меньше чем DEFAULT_PARAMS["size"] (30)
            "hasMore": True,  # Но hasMore=True
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client._fetch_via_api(max_pages=1)

            assert len(result) == 1


@pytest.mark.asyncio
class TestKufarAPIClientFetchPage:
    """Тесты метода fetch_listing_page."""

    async def test_fetch_listing_page_success(self):
        """Проверка получения одной страницы."""
        client = KufarAPIClient(use_scraper=False)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "listing": [{"id": 1}, {"id": 2}],
            "hasMore": True,
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            listings, has_more = await client.fetch_listing_page(page=2)

            assert len(listings) == 2
            assert has_more is True
            mock_client.get.assert_called_once()

    async def test_fetch_listing_page_no_more(self):
        """Проверка получения последней страницы."""
        client = KufarAPIClient(use_scraper=False)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "listing": [{"id": 1}],
            "hasMore": False,
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            listings, has_more = await client.fetch_listing_page(page=1)

            assert len(listings) == 1
            assert has_more is False

    async def test_fetch_listing_page_different_formats(self):
        """Проверка обработки разных форматов ответа."""
        client = KufarAPIClient(use_scraper=False)

        test_cases = [
            {"ads": [{"id": 1}], "has_more": True},
            {"items": [{"id": 2}], "hasMore": False},
        ]

        for i, data in enumerate(test_cases):
            mock_response = MagicMock()
            mock_response.json.return_value = data
            mock_response.raise_for_status = MagicMock()

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get.return_value = mock_response
                mock_client.__aenter__.return_value = mock_client
                mock_client_class.return_value = mock_client

                listings, has_more = await client.fetch_listing_page(page=1)

                assert len(listings) == 1
                assert listings[0]["id"] == i + 1


class TestKufarClientConstants:
    """Тесты констант клиента."""

    def test_base_url(self):
        """Проверка BASE_URL."""
        assert BASE_URL == "https://search-api-service.kufar.by/v2/search/rendered-paginated"

    def test_default_params(self):
        """Проверка параметров по умолчанию."""
        assert DEFAULT_PARAMS["category"] == "1010"
        assert DEFAULT_PARAMS["cur"] == "USD"
        assert DEFAULT_PARAMS["lang"] == "ru"
        assert DEFAULT_PARAMS["size"] == 30
        assert DEFAULT_PARAMS["sort"] == "lst.d"

    def test_headers(self):
        """Проверка заголовков."""
        assert "User-Agent" in HEADERS
        assert "Accept" in HEADERS
        assert HEADERS["Accept"] == "application/json"

    def test_search_urls(self):
        """Проверка URL для поиска."""
        assert "buy_apartments" in SEARCH_URLS
        assert "buy_houses" in SEARCH_URLS
        assert "rent_apartments" in SEARCH_URLS
        assert "rent_apartments_mogilev" in SEARCH_URLS
        assert SEARCH_URLS["buy_apartments"] == "https://re.kufar.by/l/belarus/kupit/kvartiru"
