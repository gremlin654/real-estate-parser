import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator, Generator
import os

from app.main import app
from app.config import settings
from app.models.listing import Base, ScanHistory, Listing, ListingStatus
from app.db.database import async_session_maker


@pytest.fixture(scope="function")
async def client():
    """Create async client for testing API endpoints (no DB operations)."""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def test_db_url():
    """Получение URL тестовой БД.

    Для локального запуска тестов используем localhost:5433.
    Для запуска в Docker используем db_test.
    """
    # Проверяем, запущены ли в Docker (есть ли контейнер с именем db_test)
    if os.getenv("PYTEST_RUNNING_IN_DOCKER"):
        return settings.TEST_DATABASE_URL

    # Локальный запуск - используем localhost
    return "postgresql+asyncpg://postgres:secret@localhost:5433/kufar_monitor_test"


@pytest.fixture(scope="function")
async def test_session(test_db_url) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for testing with fresh DB schema."""
    # Создаем engine для каждого теста, чтобы избежать проблем с event loop
    engine = create_async_engine(
        test_db_url,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def create_test_listing(test_session) -> Listing:
    """Create a single test listing."""
    listing = Listing(
        kufar_id="test_listing_123",
        url="https://re.kufar.by/vi/123456",
        title="Test Apartment",
        price=100000,
        price_usd=35000,
        currency="BYN",
        city="minsk",
        address="Test Street 1",
        rooms=2,
        area=55.0,
        floor=3,
        total_floors=9,
        category="apartments",
        status=ListingStatus.active,
        first_seen_at=datetime.now(timezone.utc).replace(tzinfo=None),
        last_seen_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    test_session.add(listing)
    await test_session.commit()
    await test_session.refresh(listing)
    return listing


@pytest.fixture
async def test_listings(test_session) -> list[Listing]:
    """Create multiple test listings for export tests."""
    listings = []
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)

    # Создаём 5 тестовых объявлений
    for i in range(5):
        city = "minsk" if i % 2 == 0 else "mogilev"
        status = ListingStatus.active if i % 3 != 0 else ListingStatus.new

        listing = Listing(
            kufar_id=f"test_listing_{i}",
            url=f"https://re.kufar.by/vi/{100000 + i}",
            title=f"Test Apartment {i}",
            price=100000 + (i * 10000),
            price_usd=35000 + (i * 3000),
            currency="BYN",
            city=city,
            address=f"Test Street {i}",
            rooms=(i % 4) + 1,  # 1-4 комнаты
            area=50.0 + (i * 5),
            floor=(i % 10) + 1,
            total_floors=9,
            category="apartments",
            status=status,
            first_seen_at=base_time - timedelta(days=i),
            last_seen_at=base_time,
        )
        test_session.add(listing)
        listings.append(listing)

    await test_session.commit()

    for listing in listings:
        await test_session.refresh(listing)

    return listings


@pytest.fixture
async def create_test_scan_history(test_session) -> ScanHistory:
    """Create a single test scan history record."""
    scan = ScanHistory(
        city="minsk",
        city_name="Минск",
        trigger_type="manual",
        status="running",
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    test_session.add(scan)
    await test_session.commit()
    await test_session.refresh(scan)
    return scan


@pytest.fixture
async def create_multiple_scan_histories(test_session) -> list[ScanHistory]:
    """
    Create multiple test scan history records.

    Creates 5 records:
    - 3 for minsk (indices 0, 2, 4)
    - 2 for mogilev (indices 1, 3)
    - 3 completed (indices 1, 2, 4 - where i % 3 != 0)
    - 2 error (indices 0, 3 - where i % 3 == 0)
    """
    scans = []
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)

    for i in range(5):
        city = "minsk" if i % 2 == 0 else "mogilev"
        status = "completed" if i % 3 != 0 else "error"  # Исправлено: error вместо failed

        scan = ScanHistory(
            city=city,
            city_name="Минск" if city == "minsk" else "Могилёв",
            trigger_type="manual" if i % 2 == 0 else "scheduled",
            status=status,
            started_at=base_time - timedelta(hours=i),
            listings_fetched=100 + (i * 10),
            listings_created=10 + i,
            listings_updated=5 + i,
            listings_deleted=2 + i,
            pages_scraped=3 + i,
        )

        if status == "error":  # Исправлено: error вместо failed
            scan.error_message = f"Test error {i}"
            scan.completed_at = base_time - timedelta(hours=i-0.5)

        test_session.add(scan)
        scans.append(scan)

    await test_session.commit()

    for scan in scans:
        await test_session.refresh(scan)

    return scans
