"""
E2E тесты для проверки исправления "false deleted при ошибках сканирования".

Эти тесты проверяют интеграцию между компонентами:
1. Валидация количества объявлений
2. Транзакционность upsert
3. Вызов mark_deleted только после успешной валидации

Тесты используют реальную тестовую БД (порт 5433).
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
class TestFalseDeletedProtectionE2E:
    """
    E2E тесты для защиты от ложной пометки deleted.
    
    Тестируются сценарии:
    1. Частичная загрузка (80%) → Ошибка, нет false deleted
    2. Нормальное сканирование (95%+) → Завершено, mark_deleted() вызван
    3. Пограничное значение (89% vs 90%) → Проверка порога
    4. 0 объявлений (ошибка API) → Ошибка, нет false deleted
    """

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
    ):
        """
        Сценарий 1: Частичная загрузка (80%)

        Дано: В базе 500 активных объявлений по Минску + статистика со средним 500
        Когда: Сканирование возвращает только 400 объявлений (80%)
        Ожидаемый результат:
        - Статус сканирования: "Ошибка"
        - В БД осталось 500 активных (нет false deleted)
        - Сообщение: "⚠️ Аномалия: получено 400, ожидалось ~500"
        """
        # Setup: 500 active listings
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(500):
            listing = Listing(
                kufar_id=f"test_listing_{i:04d}",
                url=f"https://re.kufar.by/vi/{100000 + i}",
                title=f"Test Apartment {i}",
                price=100000,
                price_usd=35000,
                currency="BYN",
                city="minsk",
                status=ListingStatus.active,
                first_seen_at=base_time,
                last_seen_at=base_time,
            )
            test_session.add(listing)

        # Setup: Scan stats with average 500
        stats = ScanStats(
            city="minsk",
            recent_counts=[480, 500, 520, 490, 510],
            avg_listings_count=500,
            last_updated=base_time,
        )
        test_session.add(stats)
        await test_session.commit()

        # Initial state verification
        initial_active = await self.count_active_listings(test_session)
        assert initial_active == 500

        initial_deleted = await self.count_deleted_listings(test_session)
        assert initial_deleted == 0

        # Mock scraper to return only 400 listings (80%)
        mock_listings = []
        for i in range(400):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "status": "active",
                "images": [],
                "raw_data": {},
            })

        # Execute scan with mock
        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[
                (mock_listings, None),
            ])
            mock_scraper_class.return_value = mock_scraper

            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        # Wait for async scan to complete
        await asyncio.sleep(2)

        # Verify scan history
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "error", f"Expected 'error', got: {latest_scan.status}"
        assert latest_scan.error_message is not None
        assert "Аномалия" in latest_scan.error_message
        assert "получено 400" in latest_scan.error_message
        assert "ожидалось ~500" in latest_scan.error_message or "менее 90%" in latest_scan.error_message

        # Verify NO false deleted occurred
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_active == 500, f"Expected 500 active, got: {final_active}"
        assert final_deleted == 0, f"Expected 0 deleted, got: {final_deleted}"

    async def test_scenario_2_normal_scan_96_percent(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
    ):
        """
        Сценарий 2: Нормальное сканирование (96%)

        Дано: В базе 500 активных объявлений + статистика со средним 500
        Когда: Сканирование возвращает 480 объявлений (96%)
        Ожидаемый результат:
        - Статус сканирования: "Завершено"
        - 20 объявлений помечены как deleted (500 - 480)
        """
        # Setup: 500 active listings
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(500):
            listing = Listing(
                kufar_id=f"test_listing_{i:04d}",
                url=f"https://re.kufar.by/vi/{100000 + i}",
                title=f"Test Apartment {i}",
                price=100000,
                price_usd=35000,
                currency="BYN",
                city="minsk",
                status=ListingStatus.active,
                first_seen_at=base_time,
                last_seen_at=base_time,
            )
            test_session.add(listing)

        # Setup: Scan stats with average 500
        stats = ScanStats(
            city="minsk",
            recent_counts=[480, 500, 520, 490, 510],
            avg_listings_count=500,
            last_updated=base_time,
        )
        test_session.add(stats)
        await test_session.commit()

        # Mock scraper to return 480 listings (96%)
        mock_listings = []
        for i in range(480):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "status": "active",
                "images": [],
                "raw_data": {},
            })

        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[
                (mock_listings, None),
            ])
            mock_scraper_class.return_value = mock_scraper

            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        await asyncio.sleep(2)

        # Verify scan completed successfully
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "completed"

        # Verify mark_deleted was called (20 listings should be deleted)
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_deleted == 20, f"Expected 20 deleted, got: {final_deleted}"
        assert final_active == 480, f"Expected 480 active, got: {final_active}"

    async def test_scenario_3a_boundary_89_percent(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
    ):
        """
        Сценарий 3A: Пограничное значение 89%

        Дано: Среднее 500 объявлений
        Когда: 445 объявлений (89%)
        Ожидаемый результат:
        - Статус: "Ошибка"
        - Нет false deleted
        """
        # Setup: 500 active listings
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(500):
            listing = Listing(
                kufar_id=f"test_listing_{i:04d}",
                url=f"https://re.kufar.by/vi/{100000 + i}",
                title=f"Test Apartment {i}",
                price=100000,
                price_usd=35000,
                currency="BYN",
                city="minsk",
                status=ListingStatus.active,
                first_seen_at=base_time,
                last_seen_at=base_time,
            )
            test_session.add(listing)

        # Setup: Scan stats with average 500
        stats = ScanStats(
            city="minsk",
            recent_counts=[480, 500, 520],
            avg_listings_count=500,
            last_updated=base_time,
        )
        test_session.add(stats)
        await test_session.commit()

        # Mock scraper to return 445 listings (89%)
        mock_listings = []
        for i in range(445):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "status": "active",
                "images": [],
                "raw_data": {},
            })

        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[
                (mock_listings, None),
            ])
            mock_scraper_class.return_value = mock_scraper

            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        await asyncio.sleep(2)

        # Verify scan failed
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "error"
        assert "Аномалия" in latest_scan.error_message

        # Verify NO false deleted
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_active == 500
        assert final_deleted == 0

    async def test_scenario_3b_boundary_90_percent(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
    ):
        """
        Сценарий 3B: Пограничное значение 90%

        Дано: Среднее 500 объявлений
        Когда: 450 объявлений (90%)
        Ожидаемый результат:
        - Статус: "Завершено"
        - 50 объявлений помечены как deleted
        """
        # Setup: 500 active listings
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(500):
            listing = Listing(
                kufar_id=f"test_listing_{i:04d}",
                url=f"https://re.kufar.by/vi/{100000 + i}",
                title=f"Test Apartment {i}",
                price=100000,
                price_usd=35000,
                currency="BYN",
                city="minsk",
                status=ListingStatus.active,
                first_seen_at=base_time,
                last_seen_at=base_time,
            )
            test_session.add(listing)

        # Setup: Scan stats with average 500
        stats = ScanStats(
            city="minsk",
            recent_counts=[480, 500, 520],
            avg_listings_count=500,
            last_updated=base_time,
        )
        test_session.add(stats)
        await test_session.commit()

        # Mock scraper to return 450 listings (exactly 90%)
        mock_listings = []
        for i in range(450):
            mock_listings.append({
                "kufar_id": f"test_listing_{i:04d}",
                "url": f"https://re.kufar.by/vi/{100000 + i}",
                "title": f"Test Apartment {i}",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "status": "active",
                "images": [],
                "raw_data": {},
            })

        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[
                (mock_listings, None),
            ])
            mock_scraper_class.return_value = mock_scraper

            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        await asyncio.sleep(2)

        # Verify scan completed
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "completed"

        # Verify 50 listings deleted
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_deleted == 50, f"Expected 50 deleted, got: {final_deleted}"
        assert final_active == 450, f"Expected 450 active, got: {final_active}"

    async def test_scenario_4_zero_listings_api_error(
        self,
        client: AsyncClient,
        test_session: AsyncSession,
    ):
        """
        Сценарий 4: 0 объявлений (ошибка API)

        Дано: В базе 500 активных объявлений + статистика
        Когда: API возвращает 0 объявлений
        Ожидаемый результат:
        - Статус: "Ошибка"
        - Нет false deleted в БД
        """
        # Setup: 500 active listings
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(500):
            listing = Listing(
                kufar_id=f"test_listing_{i:04d}",
                url=f"https://re.kufar.by/vi/{100000 + i}",
                title=f"Test Apartment {i}",
                price=100000,
                price_usd=35000,
                currency="BYN",
                city="minsk",
                status=ListingStatus.active,
                first_seen_at=base_time,
                last_seen_at=base_time,
            )
            test_session.add(listing)

        # Setup: Scan stats with average 500
        stats = ScanStats(
            city="minsk",
            recent_counts=[480, 500, 520],
            avg_listings_count=500,
            last_updated=base_time,
        )
        test_session.add(stats)
        await test_session.commit()

        # Mock scraper to return 0 listings
        mock_listings = []

        with patch('app.scraper.kufar_scraper.KufarScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.scrape_page = AsyncMock(side_effect=[
                (mock_listings, None),
            ])
            mock_scraper_class.return_value = mock_scraper

            response = await client.post(
                "/api/v1/scan/trigger",
                json={"city": "minsk"},
            )
            assert response.status_code == 200

        await asyncio.sleep(2)

        # Verify scan failed
        latest_scan = await self.get_latest_scan_history(test_session)
        assert latest_scan is not None
        assert latest_scan.status == "error"
        assert "Аномалия" in latest_scan.error_message
        assert "получено 0" in latest_scan.error_message

        # Verify NO false deleted
        final_active = await self.count_active_listings(test_session)
        final_deleted = await self.count_deleted_listings(test_session)

        assert final_active == 500
        assert final_deleted == 0
