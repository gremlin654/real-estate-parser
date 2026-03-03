import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_summary(client: AsyncClient):
    response = await client.get("/api/v1/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert "new_today" in data or "active_total" in data
