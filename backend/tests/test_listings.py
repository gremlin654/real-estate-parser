import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires DB fixture - API tested manually via curl")
async def test_get_listings_empty(client):
    response = await client.get("/api/v1/listings")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires DB fixture - API tested manually via curl")
async def test_get_listings_pagination(client):
    response = await client.get("/api/v1/listings?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 10
