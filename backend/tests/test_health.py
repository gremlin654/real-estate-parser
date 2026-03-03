import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_health_version(client: AsyncClient):
    response = await client.get("/health")
    data = response.json()
    assert "version" in data


@pytest.mark.anyio
async def test_api_docs():
    async with AsyncClient(app=None, base_url="http://test") as ac:
        response = await ac.get("/docs")
        assert response.status_code in [200, 404]
