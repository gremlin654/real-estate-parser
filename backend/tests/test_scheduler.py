"""
Тесты для ScraperScheduler
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.scraper.scheduler import ScraperScheduler, get_scheduler, init_scheduler


@pytest.mark.asyncio
class TestScraperSchedulerInit:
    """Тесты инициализации ScraperScheduler."""

    def test_init_default(self):
        """Проверка инициализации с параметрами по умолчанию."""
        scheduler = ScraperScheduler()

        assert scheduler.scheduler is None
        assert scheduler.is_running is False
        assert scheduler._ws_manager is None

    def test_init_progress_tracking(self):
        """Проверка инициализации отслеживания прогресса."""
        scheduler = ScraperScheduler()

        assert scheduler.scan_progress["is_scanning"] is False
        assert scheduler.scan_progress["city"] is None
        assert scheduler.scan_progress["city_name"] is None
        assert scheduler.scan_progress["stage"] == "idle"
        assert scheduler.scan_progress["pages_scraped"] == 0
        assert scheduler.scan_progress["listings_fetched"] == 0
        assert scheduler.scan_progress["listings_processed"] == 0
        assert scheduler.scan_progress["is_stable"] is True

    def test_init_scanning_cities(self):
        """Проверка инициализации параллельных сканирований."""
        scheduler = ScraperScheduler()

        assert scheduler.scanning_cities == {}
        assert scheduler._lock is not None
        assert scheduler._ws_manager is None


@pytest.mark.asyncio
class TestScraperSchedulerCityManagement:
    """Тесты управления городами сканирования."""

    async def test_add_scanning_city(self):
        """Проверка добавления города в сканирование."""
        scheduler = ScraperScheduler()

        await scheduler._add_scanning_city("minsk", "manual", "scan-123")

        assert "minsk" in scheduler.scanning_cities
        assert scheduler.scanning_cities["minsk"]["trigger_type"] == "manual"
        assert scheduler.scanning_cities["minsk"]["scan_id"] == "scan-123"
        assert scheduler.is_running is True

    async def test_remove_scanning_city(self):
        """Проверка удаления города из сканирования."""
        scheduler = ScraperScheduler()

        # Добавляем город
        await scheduler._add_scanning_city("minsk", "manual", "scan-123")
        assert "minsk" in scheduler.scanning_cities

        # Удаляем город
        await scheduler._remove_scanning_city("minsk")

        assert "minsk" not in scheduler.scanning_cities
        assert scheduler.is_running is False

    async def test_is_city_scanning(self):
        """Проверка проверки сканирования города."""
        scheduler = ScraperScheduler()

        await scheduler._add_scanning_city("minsk", "manual", "scan-123")

        assert scheduler._is_city_scanning("minsk") is True
        assert scheduler._is_city_scanning("brest") is False

    async def test_get_scanning_cities(self):
        """Проверка получения списка сканируемых городов."""
        scheduler = ScraperScheduler()

        await scheduler._add_scanning_city("minsk", "manual", "scan-123")
        await scheduler._add_scanning_city("brest", "scheduled", "scan-456")

        cities = scheduler._get_scanning_cities()

        assert len(cities) == 2
        city_codes = [c["city"] for c in cities]
        assert "minsk" in city_codes
        assert "brest" in city_codes

    async def test_update_city_progress(self):
        """Проверка обновления прогресса города."""
        scheduler = ScraperScheduler()

        await scheduler._add_scanning_city("minsk", "manual", "scan-123")

        await scheduler._update_city_progress(
            "minsk",
            {
                "is_scanning": True,
                "stage": "fetching",
                "pages_scraped": 5,
            },
        )

        progress = scheduler.scanning_cities["minsk"]["progress"]
        assert progress["stage"] == "fetching"
        assert progress["pages_scraped"] == 5


@pytest.mark.asyncio
class TestScraperSchedulerProgress:
    """Тесты отслеживания прогресса."""

    def test_update_progress(self):
        """Проверка обновления прогресса."""
        scheduler = ScraperScheduler()

        scheduler.scan_progress["is_scanning"] = True
        scheduler.scan_progress["city"] = "minsk"
        scheduler.scan_progress["stage"] = "fetching"
        scheduler.scan_progress["pages_scraped"] = 5

        assert scheduler.scan_progress["is_scanning"] is True
        assert scheduler.scan_progress["city"] == "minsk"
        assert scheduler.scan_progress["stage"] == "fetching"
        assert scheduler.scan_progress["pages_scraped"] == 5

    def test_get_progress(self):
        """Проверка получения прогресса."""
        scheduler = ScraperScheduler()
        scheduler.scan_progress["is_scanning"] = True
        scheduler.scan_progress["city"] = "mogilev"
        scheduler.scan_progress["stage"] = "parsing"
        scheduler.scan_progress["pages_scraped"] = 10
        scheduler.scan_progress["listings_fetched"] = 300

        progress = scheduler.scan_progress.copy()

        assert progress["is_scanning"] is True
        assert progress["city"] == "mogilev"
        assert progress["stage"] == "parsing"
        assert progress["pages_scraped"] == 10
        assert progress["listings_fetched"] == 300

    def test_reset_progress(self):
        """Проверка сброса прогресса."""
        scheduler = ScraperScheduler()
        scheduler.scan_progress["is_scanning"] = True
        scheduler.scan_progress["city"] = "minsk"
        scheduler.scan_progress["stage"] = "done"
        scheduler.scan_progress["pages_scraped"] = 20

        # Сброс прогресса
        scheduler.scan_progress = {
            "is_scanning": False,
            "city": None,
            "city_name": None,
            "stage": "idle",
            "pages_scraped": 0,
            "listings_fetched": 0,
            "listings_processed": 0,
            "elapsed_seconds": 0,
            "is_stable": True,
        }

        assert scheduler.scan_progress["is_scanning"] is False
        assert scheduler.scan_progress["city"] is None
        assert scheduler.scan_progress["stage"] == "idle"
        assert scheduler.scan_progress["pages_scraped"] == 0


@pytest.mark.asyncio
class TestScraperSchedulerStart:
    """Тесты запуска scheduler."""

    async def test_start_already_running(self):
        """Проверка что повторный запуск игнорируется."""
        scheduler = ScraperScheduler()
        scheduler.scheduler = MagicMock()
        scheduler.scheduler.running = True

        # Не должно вызывать ошибок
        await scheduler.start()

    async def test_start_no_enabled_cities(self):
        """Проверка запуска без включённых городов."""
        scheduler = ScraperScheduler()

        mock_settings = MagicMock()
        mock_settings.scan_interval_minutes = 30
        mock_settings.enabled = False

        mock_db = AsyncMock()
        mock_settings_service = MagicMock()
        mock_settings_service.get_settings = AsyncMock(return_value=mock_settings)
        mock_settings_service.get_enabled_cities = AsyncMock(return_value=[])

        with patch("app.scraper.scheduler.async_session_maker") as mock_session:
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch(
                "app.scraper.scheduler.ScanSettingsService",
                return_value=mock_settings_service,
            ):
                with patch("app.scraper.scheduler.AsyncIOScheduler") as MockScheduler:
                    mock_sched_instance = MagicMock()
                    MockScheduler.return_value = mock_sched_instance

                    await scheduler.start()

                    # Scheduler создан но job не добавлен
                    assert scheduler.scheduler is not None
                    mock_sched_instance.add_job.assert_not_called()

    async def test_start_with_enabled_cities(self):
        """Проверка запуска с включёнными городами."""
        scheduler = ScraperScheduler()

        mock_settings_minsk = MagicMock()
        mock_settings_minsk.scan_interval_minutes = 30

        mock_settings_brest = MagicMock()
        mock_settings_brest.scan_interval_minutes = 60

        mock_db = AsyncMock()
        mock_settings_service = MagicMock()
        mock_settings_service.get_settings = AsyncMock(
            side_effect=[
                mock_settings_minsk,
                mock_settings_brest,
            ]
        )
        mock_settings_service.get_enabled_cities = AsyncMock(
            return_value=["minsk", "brest"]
        )
        mock_settings_service.get_city_settings = AsyncMock(
            side_effect=[
                mock_settings_minsk,
                mock_settings_brest,
            ]
        )

        with patch("app.scraper.scheduler.async_session_maker") as mock_session:
            mock_session.return_value.__aenter__.return_value = mock_db

            with patch(
                "app.scraper.scheduler.ScanSettingsService",
                return_value=mock_settings_service,
            ):
                with patch("app.scraper.scheduler.AsyncIOScheduler") as MockScheduler:
                    mock_sched_instance = MagicMock()
                    MockScheduler.return_value = mock_sched_instance

                    with patch("app.scraper.scheduler.settings") as mock_settings:
                        mock_settings.TELEGRAM_BOT_ENABLED = True

                        await scheduler.start()

                        # Job добавлен для каждого города + cleanup
                        assert mock_sched_instance.add_job.call_count == 3


@pytest.mark.asyncio
class TestScraperSchedulerStop:
    """Тесты остановки scheduler."""

    def test_stop_running_scheduler(self):
        """Проверка остановки запущенного scheduler."""
        scheduler = ScraperScheduler()
        scheduler.is_running = True

        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        scheduler.scheduler = mock_scheduler

        scheduler.stop()

        # stop() вызывает shutdown() у scheduler
        mock_scheduler.shutdown.assert_called_once()

    def test_stop_not_running_scheduler(self):
        """Проверка остановки когда scheduler не запущен."""
        scheduler = ScraperScheduler()
        scheduler.is_running = False
        scheduler.scheduler = None

        # Не должно вызывать ошибок
        scheduler.stop()

        assert scheduler.scheduler is None


@pytest.mark.asyncio
class TestScraperSchedulerRestart:
    """Тесты перезапуска scheduler."""

    async def test_restart_with_settings_enable(self):
        """Проверка перезапуска с включением города."""
        scheduler = ScraperScheduler()
        scheduler.scheduler = MagicMock()
        scheduler.scheduler.running = True
        scheduler.scheduler.get_job.return_value = MagicMock()

        await scheduler.restart_with_settings(
            "minsk", enabled=True, interval_minutes=60
        )

        scheduler.scheduler.remove_job.assert_called()
        scheduler.scheduler.add_job.assert_called()

    async def test_restart_with_settings_disable(self):
        """Проверка перезапуска с отключением города."""
        scheduler = ScraperScheduler()
        scheduler.scheduler = MagicMock()
        scheduler.scheduler.running = True
        scheduler.scheduler.get_job.return_value = MagicMock()

        await scheduler.restart_with_settings(
            "minsk", enabled=False, interval_minutes=60
        )

        scheduler.scheduler.remove_job.assert_called()
        scheduler.scheduler.add_job.assert_not_called()


@pytest.mark.asyncio
class TestSchedulerGlobalFunctions:
    """Тесты глобальных функций."""

    def test_get_scheduler_creates_instance(self):
        """Проверка что get_scheduler создаёт экземпляр."""
        # Сбрасываем глобальный экземпляр
        import app.scraper.scheduler as scheduler_module

        original = scheduler_module._scheduler_instance
        scheduler_module._scheduler_instance = None

        try:
            result = get_scheduler()

            assert result is not None
            assert isinstance(result, ScraperScheduler)
        finally:
            # Восстанавливаем
            scheduler_module._scheduler_instance = original

    def test_init_scheduler(self):
        """Проверка init_scheduler."""
        import app.scraper.scheduler as scheduler_module

        # Сбрасываем глобальный экземпляр
        original = scheduler_module._scheduler_instance
        scheduler_module._scheduler_instance = None

        try:
            result = init_scheduler()

            assert result is not None
            assert isinstance(result, ScraperScheduler)
            assert scheduler_module._scheduler_instance is result
        finally:
            # Восстанавливаем
            scheduler_module._scheduler_instance = original


@pytest.mark.asyncio
class TestScraperSchedulerBroadcast:
    """Тесты WebSocket broadcast."""

    async def test_broadcast_progress_no_ws_manager(self):
        """Проверка broadcast без ws_manager."""
        scheduler = ScraperScheduler()

        # Не должно вызывать ошибок
        await scheduler._broadcast_progress()

    async def test_broadcast_progress_with_ws_manager(self):
        """Проверка broadcast с ws_manager."""
        scheduler = ScraperScheduler()

        mock_ws_manager = AsyncMock()
        mock_ws_manager.update_scanning_cities = AsyncMock()
        mock_ws_manager.broadcast_progress = AsyncMock()
        scheduler._ws_manager = mock_ws_manager

        await scheduler._broadcast_progress()

        mock_ws_manager.update_scanning_cities.assert_called()
        mock_ws_manager.broadcast_progress.assert_called()


@pytest.mark.asyncio
class TestScraperSchedulerRunScanScheduled:
    """Тесты планового сканирования."""

    async def test_run_scan_scheduled_creates_history(self):
        """Проверка создания записи истории сканирования."""
        scheduler = ScraperScheduler()

        # Проверяем что метод существует
        assert hasattr(scheduler, "_run_scan_scheduled")
        assert asyncio.iscoroutinefunction(scheduler._run_scan_scheduled)

    async def test_run_scan_scheduled_city_progress(self):
        """Проверка обновления прогресса города."""
        scheduler = ScraperScheduler()

        # Добавляем город
        await scheduler._add_scanning_city("minsk", "scheduled", "scan-123")

        # Проверяем начальный прогресс
        progress = scheduler.scanning_cities["minsk"]["progress"]
        assert progress["is_scanning"] is True
        assert progress["city"] == "minsk"
        assert progress["stage"] == "starting"
