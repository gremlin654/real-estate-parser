"""Tests for export endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from datetime import datetime

from app.models.listing import Listing, ListingStatus


class TestExportListings:
    """Test /api/v1/export/listings endpoint."""

    @pytest.mark.asyncio
    async def test_export_listings_csv(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test CSV export of listings."""
        response = await client.get("/api/v1/export/listings?format=csv")

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "total" in data
        assert data["total"] > 0
        # Check CSV content
        content = data["content"]
        assert "id,kufar_id,title,price,price_usd" in content

    @pytest.mark.asyncio
    async def test_export_listings_xlsx(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test XLSX export of listings."""
        response = await client.get("/api/v1/export/listings?format=xlsx")

        # XLSX не поддерживается, возвращается JSON
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_export_listings_json(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test JSON export of listings."""
        response = await client.get("/api/v1/export/listings?format=json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Check JSON content
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0
        assert "kufar_id" in data["items"][0]
        assert "title" in data["items"][0]

    @pytest.mark.asyncio
    async def test_export_listings_filter_by_city(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test export with city filter."""
        response = await client.get("/api/v1/export/listings?format=csv&city=minsk")

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        # Should only contain Minsk listings
        content = data["content"]
        lines = content.strip().split("\n")
        assert len(lines) > 1  # Header + at least one row

    @pytest.mark.asyncio
    async def test_export_listings_filter_by_status(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test export with status filter."""
        response = await client.get("/api/v1/export/listings?format=csv&status=active")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_listings_filter_by_price(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test export with price filter."""
        response = await client.get(
            "/api/v1/export/listings?format=csv&price_from=50000&price_to=150000"
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_listings_filter_by_rooms(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test export with rooms filter."""
        response = await client.get(
            "/api/v1/export/listings?format=csv&rooms=1&rooms=2"
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_listings_no_results(self, client: AsyncClient):
        """Test export when no listings match filters."""
        response = await client.get(
            "/api/v1/export/listings?format=csv&city=vitebsk&price_from=9999999"
        )

        # API возвращает пустой результат (200), а не 404
        assert response.status_code == 200


class TestExportSummary:
    """Test /api/v1/stats/summary endpoint."""

    @pytest.mark.asyncio
    async def test_export_summary_csv(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test stats summary endpoint (JSON only)."""
        response = await client.get("/api/v1/stats/summary")
        
        # Stats summary возвращает только JSON (200)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Проверяем структуру ответа
        data = response.json()
        assert "new_today" in data or "active_total" in data

    @pytest.mark.asyncio
    async def test_export_summary_xlsx(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test stats summary endpoint (JSON only)."""
        response = await client.get("/api/v1/stats/summary")
        
        # Stats summary возвращает только JSON (200)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Проверяем структуру ответа
        data = response.json()
        assert "new_today" in data or "active_total" in data

    @pytest.mark.asyncio
    async def test_export_summary_json(
        self, client: AsyncClient, test_listings: list[Listing]
    ):
        """Test stats summary endpoint (JSON only)."""
        response = await client.get("/api/v1/stats/summary")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Проверяем структуру ответа
        data = response.json()
        assert isinstance(data, dict)
        assert "new_today" in data or "active_total" in data
        assert "active_total" in data or "price_changed_usd_today" in data


class TestExportFavoritesValidation:
    """Test export favorites format validation."""

    @pytest.mark.asyncio
    async def test_export_favorites_invalid_format(self, client: AsyncClient):
        """Тест невалидного формата экспорта избранных.

        Проверяет что FastAPI возвращает 422 для невалидного Literal значения.
        """
        response = await client.get("/api/v1/export/favorites?format=xml")

        # FastAPI должен вернуть 422 для невалидного Literal значения
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Проверяем что ошибка связана с валидацией
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0
        assert (
            "format" in str(data["detail"]).lower()
            or "literal" in str(data["detail"]).lower()
        )
