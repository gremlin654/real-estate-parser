import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_listings_empty(client: AsyncClient):
    response = await client.get("/api/v1/listings")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.anyio
async def test_get_listings_pagination(client: AsyncClient):
    response = await client.get("/api/v1/listings?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 10
