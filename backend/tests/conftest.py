import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.config import settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_db_url():
    return settings.TEST_DATABASE_URL
