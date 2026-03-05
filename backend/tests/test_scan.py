import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_cities(client):
    response = await client.get("/api/v1/scan/cities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_schedule(client):
    response = await client.get("/api/v1/scan/schedule")
    assert response.status_code == 200
    data = response.json()
    assert "scan_interval_minutes" in data
    assert "enabled" in data
