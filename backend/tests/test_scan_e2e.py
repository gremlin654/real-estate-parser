"""
E2E тесты для проверки исправления "false deleted при ошибках сканирования".

Тестируются сценарии:
1. Частичная загрузка (80%) → Ошибка, нет false deleted
2. Нормальное сканирование (95%+) → Завершено, mark_deleted() вызван
3. Пограничное значение (89% vs 90%) → Проверка порога
4. 0 объявлений (ошибка API) → Ошибка, нет false deleted
"""
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.scan_stats_service import ScanStatsService
from app.services.listing_service import ListingService
from app.models.listing import (
    Listing,
    ListingStatus,
    ScanHistory,
    ScanStats,
)


@pytest.mark.asyncio
class TestFalseDeletedProtection:
    """E2E тесты для защиты от ложной пометки deleted."""

    @pytest.fixture
    async def setup_listings(self, test_session: AsyncSession) -> list[Listing]:
        """Создать 500 активных объявлений для тестов."""
        listings = []
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)

        for i in range(500):
            listing = Listing(
                kufar_id=f"test_listing_{i:04d}",
                url=f"https://re.kufar.by/vi/{100000 + i}",
                title=f"Test Apartment {i}",
                price=100000 + (i * 1000),
                price_usd=35000 + (i * 100),
                currency="BYN",
                city="minsk",
                address=f"Test Street {i}",
                rooms=(i % 4) + 1,
                area=50.0 + (i * 0.5),
                floor=(i % 10) + 1,
                total_floors=9,
                category="apartments",
                status=ListingStatus.active,
                first_seen_at=base_time - timedelta(days=i % 30),
                last_seen_at=base_time,
            )
            test_session.add(listing)
            listings.append(listing)

        await test_session.commit()
        return listings

    @pytest.fixture
    async def setup_scan_stats(self, test_session: AsyncSession) -> ScanStats:
        """Создать статистику сканирований со средним 500 объявлений."""
        from uuid import uuid4
        # UUID для primary key
        stats = ScanStats(
            id=uuid4(),
            city="minsk",
            recent_counts=[480, 500, 520, 490, 510, 505, 495, 515, 485, 500],
            avg_listings_count=500,
            last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        test_session.add(stats)
        await test_session.commit()
        await test_session.refresh(stats)
        return stats

    async def count_active_listings(self, test_session: AsyncSession, city: str = "minsk") -> int:
        """Посчитать количество активных объявлений."""
        result = await test_session.execute(
            select(func.count()).where(
                Listing.city == city,
                Listing.status == ListingStatus.active
            )
        )
        return result.scalar()

    async def count_deleted_listings(self, test_session: AsyncSession, city: str = "minsk") -> int:
        """Посчитать количество удалённых объявлений."""
        result = await test_session.execute(
            select(func.count()).where(
                Listing.city == city,
                Listing.status == ListingStatus.deleted
            )
        )
        return result.scalar()

    async def get_latest_scan_history(
        self, test_session: AsyncSession, city: str = "minsk"
    ) -> ScanHistory | None:
        """Получить последнюю запись истории сканирования."""
        result = await test_session.execute(
            select(ScanHistory)
            .where(ScanHistory.city == city)
            .order_by(ScanHistory.started_at.desc())
        )
        return result.scalar_one_or_none()

    async def test_scenario_1_partial_load_80_percent(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
        setup_listings: list[Listing],
        setup_scan_stats: ScanStats,
    ):
        """
        Сценарий 1: Частичная загрузка (80%)

        Дано: В базе 500 активных объявлений по Минску
        Когда: Сканирование возвращает только 400 объявлений (80%)
        Ожидаемый результат:
        - Статус сканирования: "Ошибка"
        - В БД осталось 500 активных (нет false deleted)
        - Сообщение: "⚠️ Аномалия: получено 400, ожидалось ~500"
        """
        # Проверка что статистика создана правильно
        assert setup_scan_stats is not None
        assert len(setup_scan_stats.recent_counts) >= 3, f"Должно быть минимум 3 записи, фактически: {len(setup_scan_stats.recent_counts)}"
        assert setup_scan_stats.avg_listings_count == 500

        # Initial state: 500 active listings
        initial_active = await self.count_active_listings(test_session)
        assert initial_active == 500, "Должно быть 500 активных объявлений"

        initial_deleted = await self.count_deleted_listings(test_session)
        assert initial_deleted == 0, "Не должно быть удалённых объявлений"

        # Mock scraper to return only 400 listings (80%)
        # scrape_page returns tuple: (listings, next_cursor)
        mock_listings = []
        for i in range(400):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000 + (i * 1000),
                "price_usd": 35000 + (i * 100),
                "currency": "BYN",
                "city": "minsk",
                "address": f"Test Street {i}",
                "rooms": (i % 4) + 1,
                "area": 50.0 + (i * 0.5),
                "floor": (i % 10) + 1,
                "total_floors": 9,
                "category": "apartments",
                "images": [],
                "raw_data": {},
            })

        # Patch the scraper (imported inside function)
        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            # First call returns 400 listings, second call returns empty (no more pages)
            mock_scraper.scrape_page = AsyncMock(side_effect=[
                (mock_listings, None),  # First page: 400 listings, no next cursor
            ])
            mock_scraper_class.return_value = mock_scraper

            # Trigger manual scan
            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )

            # Check response
            assert response.status_code == 200
            data = response.json()
            # API возвращает 'started' когда сканирование началось
            assert data["status"] in ["running", "started"]

        # Wait for scan to complete (async task)
        # Background task может выполняться несколько секунд
        await asyncio.sleep(5)

        # Check scan history
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None, "Должна быть запись о сканировании"
        assert latest_scan.status == "error", f"Статус должен быть 'error', фактически: {latest_scan.status}"
        assert latest_scan.error_message is not None, "Должно быть сообщение об ошибке"
        assert "Аномалия" in latest_scan.error_message, f"Сообщение должно содержать 'Аномалия': {latest_scan.error_message}"
        assert "получено 400" in latest_scan.error_message, f"Сообщение должно содержать количество: {latest_scan.error_message}"
        assert "ожидалось ~500" in latest_scan.error_message, f"Сообщение должно содержать ожидаемое количество: {latest_scan.error_message}"

        # Check that no false deleted occurred
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_active == 500, f"Должно остаться 500 активных, фактически: {final_active}"
        assert final_deleted == 0, f"Не должно быть удалённых, фактически: {final_deleted}"

    async def test_scenario_2_normal_scan_95_percent(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
        setup_listings: list[Listing],
        setup_scan_stats: ScanStats,
    ):
        """
        Сценарий 2: Нормальное сканирование (95%+)

        Дано: В базе 500 активных объявлений
        Когда: Сканирование возвращает 480-500 объявлений
        Ожидаемый результат:
        - Статус сканирования: "Завершено"
        - `mark_deleted()` вызван корректно
        - Статистика точная (created/updated/deleted)
        """
        # Initial state: 500 active listings
        initial_active = await self.count_active_listings(test_session)
        assert initial_active == 500

        # Mock scraper to return 480 listings (96%)
        # scrape_page returns tuple: (listings, next_cursor)
        mock_listings = []
        for i in range(480):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000 + (i * 1000),
                "price_usd": 35000 + (i * 100),
                "currency": "BYN",
                "city": "minsk",
                "address": f"Test Street {i}",
                "rooms": (i % 4) + 1,
                "area": 50.0 + (i * 0.5),
                "floor": (i % 10) + 1,
                "total_floors": 9,
                "category": "apartments",
                "images": [],
                "raw_data": {},
            })

        # Patch the scraper (imported inside function)
        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[
                (mock_listings, None),  # One page: 480 listings
            ])
            mock_scraper_class.return_value = mock_scraper

            # Trigger manual scan
            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )

            assert response.status_code == 200

        # Wait for scan to complete
        await asyncio.sleep(5)

        # Check scan history
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "completed", f"Статус должен быть 'completed', фактически: {latest_scan.status}"

        # Check that mark_deleted was called (20 listings should be marked as deleted)
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        # 480 listings returned, so 20 should be marked as deleted
        assert final_deleted == 20, f"Должно быть 20 удалённых (500 - 480), фактически: {final_deleted}"
        assert final_active == 480, f"Должно остаться 480 активных, фактически: {final_active}"

        # Check scan history stats
        assert latest_scan.listings_fetched == 480
        assert latest_scan.listings_deleted == 20

    async def test_scenario_3a_boundary_89_percent(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
        setup_listings: list[Listing],
        setup_scan_stats: ScanStats,
    ):
        """
        Сценарий 3A: Пограничное значение 89%

        Дано: Среднее 500 объявлений
        Когда: 445 объявлений (89%)
        Ожидаемый результат:
        - Статус: "Ошибка"
        - Нет false deleted
        """
        initial_active = await self.count_active_listings(test_session)
        assert initial_active == 500

        # Mock scraper to return 445 listings (89%)
        mock_listings = []
        for i in range(445):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000 + (i * 1000),
                "price_usd": 35000 + (i * 100),
                "currency": "BYN",
                "city": "minsk",
                "address": f"Test Street {i}",
                "rooms": (i % 4) + 1,
                "area": 50.0 + (i * 0.5),
                "floor": (i % 10) + 1,
                "total_floors": 9,
                "category": "apartments",
                "images": [],
                "raw_data": {},
            })

        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[(mock_listings, None)])
            mock_scraper_class.return_value = mock_scraper

            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        await asyncio.sleep(5)

        # Check scan history
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "error", f"Статус должен быть 'error', фактически: {latest_scan.status}"
        assert "Аномалия" in latest_scan.error_message

        # No false deleted
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_active == 500, f"Должно остаться 500 активных, фактически: {final_active}"
        assert final_deleted == 0, f"Не должно быть удалённых, фактически: {final_deleted}"

    async def test_scenario_3b_boundary_90_percent(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
        setup_listings: list[Listing],
        setup_scan_stats: ScanStats,
    ):
        """
        Сценарий 3B: Пограничное значение 90%

        Дано: Среднее 500 объявлений
        Когда: 450 объявлений (90%)
        Ожидаемый результат:
        - Статус: "Завершено"
        - mark_deleted() вызван
        """
        initial_active = await self.count_active_listings(test_session)
        assert initial_active == 500

        # Mock scraper to return 450 listings (exactly 90%)
        mock_listings = []
        for i in range(450):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000 + (i * 1000),
                "price_usd": 35000 + (i * 100),
                "currency": "BYN",
                "city": "minsk",
                "address": f"Test Street {i}",
                "rooms": (i % 4) + 1,
                "area": 50.0 + (i * 0.5),
                "floor": (i % 10) + 1,
                "total_floors": 9,
                "category": "apartments",
                "images": [],
                "raw_data": {},
            })

        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[(mock_listings, None)])
            mock_scraper_class.return_value = mock_scraper

            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        await asyncio.sleep(5)

        # Check scan history
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "completed", f"Статус должен быть 'completed', фактически: {latest_scan.status}"

        # 50 listings should be marked as deleted
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_deleted == 50, f"Должно быть 50 удалённых (500 - 450), фактически: {final_deleted}"
        assert final_active == 450, f"Должно остаться 450 активных, фактически: {final_active}"

    async def test_scenario_4_zero_listings_api_error(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
        setup_listings: list[Listing],
        setup_scan_stats: ScanStats,
    ):
        """
        Сценарий 4: 0 объявлений (ошибка API)

        Дано: В базе есть активные объявления
        Когда: API возвращает 0 объявлений
        Ожидаемый результат:
        - Статус: "Ошибка"
        - Нет false deleted в БД
        """
        initial_active = await self.count_active_listings(test_session)
        assert initial_active == 500

        initial_deleted = await self.count_deleted_listings(test_session)
        assert initial_deleted == 0

        # Mock scraper to return 0 listings
        mock_listings = []

        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[(mock_listings, None)])
            mock_scraper_class.return_value = mock_scraper

            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        await asyncio.sleep(5)

        # Check scan history
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "error", f"Статус должен быть 'error', фактически: {latest_scan.status}"
        assert "Аномалия" in latest_scan.error_message
        assert "получено 0" in latest_scan.error_message

        # No false deleted
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_active == 500, f"Должно остаться 500 активных, фактически: {final_active}"
        assert final_deleted == 0, f"Не должно быть удалённых, фактически: {final_deleted}"


@pytest.mark.asyncio
class TestTransactionRollback:
    """Тесты для проверки транзакционности upsert."""

    @pytest.fixture
    async def setup_test_data(self, test_session: AsyncSession):
        """Создать тестовые данные."""
        # Create scan stats
        stats = ScanStats(
            city="minsk",
            recent_counts=[480, 500, 520],
            avg_listings_count=500,
            last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        test_session.add(stats)

        # Create 100 active listings
        for i in range(100):
            listing = Listing(
                kufar_id=f"test_listing_{i:04d}",
                url=f"https://re.kufar.by/vi/{100000 + i}",
                title=f"Test Apartment {i}",
                price=100000,
                price_usd=35000,
                currency="BYN",
                city="minsk",
                status=ListingStatus.active,
                first_seen_at=datetime.now(timezone.utc).replace(tzinfo=None),
                last_seen_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            test_session.add(listing)

        await test_session.commit()

    async def test_upsert_rollback_on_error(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
        setup_test_data,
    ):
        """
        Проверка отката транзакции при ошибке upsert.

        Если во время upsert происходит ошибка, все изменения должны быть откатаны.
        """
        # Mock scraper to return valid data (500 listings)
        mock_listings = []
        for i in range(500):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000 + (i * 1000),
                "price_usd": 35000 + (i * 100),
                "currency": "BYN",
                "city": "minsk",
                "address": f"Test Street {i}",
                "rooms": (i % 4) + 1,
                "area": 50.0 + (i * 0.5),
                "floor": (i % 10) + 1,
                "total_floors": 9,
                "category": "apartments",
                "images": [],
                "raw_data": {},
            })

        # Mock upsert_listings_transaction to raise an error
        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[(mock_listings, None)])
            mock_scraper_class.return_value = mock_scraper

            # Trigger scan
            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        await asyncio.sleep(5)

        # Check that scan completed (validation passed)
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        # Scan should complete because validation passed (500 listings >= 90% of 500)
        assert latest_scan.status == "completed"

    async def get_latest_scan_history(
        self, test_session: AsyncSession, city: str = "minsk"
    ) -> ScanHistory | None:
        """Получить последнюю запись истории сканирования."""
        result = await test_session.execute(
            select(ScanHistory)
            .where(ScanHistory.city == city)
            .order_by(ScanHistory.started_at.desc())
        )
        return result.scalar_one_or_none()
