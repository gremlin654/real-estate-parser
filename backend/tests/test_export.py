"""Tests for export endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from datetime import datetime

from app.models.listing import Listing, ListingStatus


class TestExportListings:
    """Test /api/v1/export/listings endpoint."""

    @pytest.mark.asyncio
    async def test_export_listings_csv(self, client: AsyncClient, test_listings: list[Listing]):
        """Test CSV export of listings."""
        response = await client.get("/api/v1/export/listings?format=csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "attachment" in response.headers["content-disposition"]
        assert "kufar_listings_" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]
        
        # Check CSV content
        content = response.text
        assert "id,kufar_id,title,price_byn,price_usd" in content
        
    @pytest.mark.asyncio
    async def test_export_listings_xlsx(self, client: AsyncClient, test_listings: list[Listing]):
        """Test XLSX export of listings."""
        response = await client.get("/api/v1/export/listings?format=xlsx")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in response.headers["content-disposition"]
        assert ".xlsx" in response.headers["content-disposition"]
        
        # Check file is not empty
        assert len(response.content) > 0
        
    @pytest.mark.asyncio
    async def test_export_listings_json(self, client: AsyncClient, test_listings: list[Listing]):
        """Test JSON export of listings."""
        response = await client.get("/api/v1/export/listings?format=json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Check JSON content
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "kufar_id" in data[0]
        assert "title" in data[0]
        
    @pytest.mark.asyncio
    async def test_export_listings_filter_by_city(self, client: AsyncClient, test_listings: list[Listing]):
        """Test export with city filter."""
        response = await client.get("/api/v1/export/listings?format=csv&city=minsk")
        
        assert response.status_code == 200
        content = response.text
        
        # Should only contain Minsk listings
        lines = content.strip().split("\n")
        assert len(lines) > 1  # Header + at least one row
        
    @pytest.mark.asyncio
    async def test_export_listings_filter_by_status(self, client: AsyncClient, test_listings: list[Listing]):
        """Test export with status filter."""
        response = await client.get("/api/v1/export/listings?format=csv&status=active")
        
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_export_listings_filter_by_price(self, client: AsyncClient, test_listings: list[Listing]):
        """Test export with price filter."""
        response = await client.get("/api/v1/export/listings?format=csv&price_from=50000&price_to=150000")
        
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_export_listings_filter_by_rooms(self, client: AsyncClient, test_listings: list[Listing]):
        """Test export with rooms filter."""
        response = await client.get("/api/v1/export/listings?format=csv&rooms=1&rooms=2")
        
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_export_listings_no_results(self, client: AsyncClient):
        """Test export when no listings match filters."""
        response = await client.get("/api/v1/export/listings?format=csv&city=vitebsk&price_from=9999999")
        
        assert response.status_code == 404
        assert "No listings found" in response.text


class TestExportSummary:
    """Test /api/v1/export/summary endpoint."""

    @pytest.mark.asyncio
    async def test_export_summary_csv(self, client: AsyncClient, test_listings: list[Listing]):
        """Test CSV export of summary."""
        response = await client.get("/api/v1/export/summary?format=csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "attachment" in response.headers["content-disposition"]
        
        # Check CSV content
        content = response.text
        assert "city,total_listings,new,active,updated" in content
        
    @pytest.mark.asyncio
    async def test_export_summary_xlsx(self, client: AsyncClient, test_listings: list[Listing]):
        """Test XLSX export of summary."""
        response = await client.get("/api/v1/export/summary?format=xlsx")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
    @pytest.mark.asyncio
    async def test_export_summary_json(self, client: AsyncClient, test_listings: list[Listing]):
        """Test JSON export of summary."""
        response = await client.get("/api/v1/export/summary?format=json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Check JSON content
        data = response.json()
        assert isinstance(data, list)
        assert "city" in data[0]
        assert "total_listings" in data[0]
