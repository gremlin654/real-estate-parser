"""
Тесты для KufarAPIClient
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.scraper.kufar_client import KufarAPIClient


@pytest.mark.asyncio
class TestKufarAPIClientInit:
    """Тесты инициализации KufarAPIClient."""

    def test_init_default(self):
        """Проверка инициализации с параметрами по умолчанию."""
        client = KufarAPIClient()

        assert client.timeout == 30.0

    def test_init_custom_timeout(self):
        """Проверка инициализации с кастомным timeout."""
        client = KufarAPIClient(timeout=60.0)

        assert client.timeout == 60.0


@pytest.mark.asyncio
class TestKufarAPIClientFetchListings:
    """Тесты метода fetch_listings."""

    async def test_fetch_listings_success(self):
        """Проверка успешного получения списка."""
        client = KufarAPIClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "listing": [{"id": 1, "title": "Listing 1"}, {"id": 2, "title": "Listing 2"}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client.fetch_listings(city="minsk", page=1)

            assert result is not None
            assert len(result["listing"]) == 2
            mock_client.get.assert_called_once()

    async def test_fetch_listings_http_error(self):
        """Проверка обработки HTTP ошибки."""
        client = KufarAPIClient()

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=MagicMock()
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client.fetch_listings(city="minsk", page=1)

            assert result is None

    async def test_fetch_listings_general_error(self):
        """Проверка обработки общей ошибки."""
        client = KufarAPIClient()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network error")
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            result = await client.fetch_listings(city="minsk", page=1)

            assert result is None

    async def test_fetch_listings_default_city(self):
        """Проверка города по умолчанию (mogilev)."""
        client = KufarAPIClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"listing": []}
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            await client.fetch_listings()

            # Проверка что city по умолчанию mogilev
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["region"] == "mogilev"

    async def test_fetch_listings_custom_city(self):
        """Проверка кастомного города."""
        client = KufarAPIClient()

        mock_response = MagicMock()
        mock_response.json.return_value = {"listing": []}
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client_class.return_value = mock_client

            await client.fetch_listings(city="brest", page=2)

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["region"] == "brest"
            assert call_args[1]["params"]["page"] == "2"


class TestKufarAPIClientConstants:
    """Тесты констант клиента."""

    def test_default_headers(self):
        """Проверка заголовков по умолчанию."""
        client = KufarAPIClient()

        assert "User-Agent" in client.headers
        assert "Accept" in client.headers
        assert client.headers["Accept"] == "application/json, text/plain, */*"
        assert "ru" in client.headers["Accept-Language"]
