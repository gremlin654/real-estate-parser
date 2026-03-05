import pytest
from httpx import AsyncClient
from app.main import app
from app.config import settings


@pytest.fixture(scope="function")
async def client():
    """Create async client for testing API endpoints (no DB operations)."""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_db_url():
    return settings.TEST_DATABASE_URL
