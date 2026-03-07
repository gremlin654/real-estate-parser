"""
Тесты для поддержки параллельных сканирований городов.

Проверяет:
1. Запуск сканирования для города который уже сканируется → 409
2. Параллельное сканирование для разных городов → 200
3. Очистка scanning_cities после успешного завершения
4. Очистка scanning_cities после ошибки
5. WebSocket отправляет список scanning_cities
6. GET /scan/status возвращает правильный формат
7. Race conditions при параллельном запуске
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.scraper.scheduler import ScraperScheduler
from app.api.v1.scan import trigger_scan, _run_manual_scan
from app.api.v1.ws import ConnectionManager
from app.config import CITY_NAMES


class TestScraperSchedulerParallelScans:
    """Тесты для ScraperScheduler с поддержкой параллельных сканирований."""

    @pytest.fixture
    def scheduler(self):
        """Создать новый scheduler для каждого теста."""
        return ScraperScheduler()

    @pytest.fixture
    def ws_manager(self):
        """Создать менеджер WebSocket подключений."""
        return ConnectionManager()

    def test_is_city_scanning_empty(self, scheduler):
        """Проверка: когда нет активных сканирований."""
        assert not scheduler._is_city_scanning("minsk")
        assert not scheduler._is_city_scanning("mogilev")
        assert len(scheduler._get_scanning_cities()) == 0

    @pytest.mark.asyncio
    async def test_add_scanning_city(self, scheduler):
        """Добавление города в сканирование."""
        await scheduler._add_scanning_city("minsk", "manual", "scan-123")

        assert scheduler._is_city_scanning("minsk")
        assert not scheduler._is_city_scanning("mogilev")
        assert scheduler.is_running  # Обратная совместимость

        cities = scheduler._get_scanning_cities()
        assert len(cities) == 1
        assert cities[0]["city"] == "minsk"
        assert cities[0]["trigger_type"] == "manual"
        # scan_id хранится в данных сканирования, а не в response
        assert "started_at" in cities[0]
        # Progress теперь хранится напрямую в объекте сканирования
        assert cities[0]["stage"] == "starting"
        assert cities[0]["city"] == "minsk"

    @pytest.mark.asyncio
    async def test_remove_scanning_city(self, scheduler):
        """Удаление города из сканирования."""
        await scheduler._add_scanning_city("minsk", "manual", "scan-123")
        await scheduler._add_scanning_city("mogilev", "scheduled", "scan-456")

        assert scheduler._is_city_scanning("minsk")
        assert scheduler._is_city_scanning("mogilev")

        await scheduler._remove_scanning_city("minsk")

        assert not scheduler._is_city_scanning("minsk")
        assert scheduler._is_city_scanning("mogilev")
        assert scheduler.is_running  # Ещё есть активные сканирования

        await scheduler._remove_scanning_city("mogilev")
        assert not scheduler.is_running  # Нет активных

    @pytest.mark.asyncio
    async def test_multiple_cities_parallel(self, scheduler):
        """Параллельное сканирование нескольких городов."""
        cities_to_scan = ["minsk", "mogilev", "grodno"]

        for city in cities_to_scan:
            await scheduler._add_scanning_city(city, "manual", f"scan-{city}")

        for city in cities_to_scan:
            assert scheduler._is_city_scanning(city)

        cities = scheduler._get_scanning_cities()
        assert len(cities) == 3

        city_names = [c["city"] for c in cities]
        for city in cities_to_scan:
            assert city in city_names

    @pytest.mark.asyncio
    async def test_update_city_progress(self, scheduler):
        """Обновление прогресса для конкретного города."""
        await scheduler._add_scanning_city("minsk", "manual", "scan-123")

        new_progress = {
            "is_scanning": True,
            "city": "minsk",
            "city_name": "Минск",
            "stage": "fetching",
            "pages_scraped": 10,
            "listings_fetched": 300,
            "listings_processed": 0,
            "elapsed_seconds": 60,
            "is_stable": False,
        }

        await scheduler._update_city_progress("minsk", new_progress)

        cities = scheduler._get_scanning_cities()
        # Progress теперь хранится напрямую в объекте сканирования
        assert cities[0]["stage"] == "fetching"
        assert cities[0]["pages_scraped"] == 10
        assert cities[0]["listings_fetched"] == 300

    @pytest.mark.asyncio
    async def test_remove_nonexistent_city(self, scheduler):
        """Удаление несуществующего города не вызывает ошибок."""
        await scheduler._remove_scanning_city("minsk")  # Не должно вызвать ошибку
        assert not scheduler._is_city_scanning("minsk")


class TestScanEndpointParallel:
    """Тесты для API endpoint /api/v1/scan/trigger."""

    @pytest.mark.asyncio
    async def test_trigger_scan_city_already_scanning(self):
        """Попытка запустить сканирование для уже сканируемого города → 409."""
        from fastapi import HTTPException
        from unittest.mock import MagicMock, patch

        # Создать mock scheduler
        mock_scheduler = MagicMock()
        mock_scheduler._is_city_scanning = MagicMock(return_value=True)

        request = MagicMock()
        request.city = "minsk"
        background_tasks = MagicMock()

        with patch('app.api.v1.scan.get_scheduler', return_value=mock_scheduler):
            with pytest.raises(HTTPException) as exc_info:
                await trigger_scan(request, background_tasks)

        assert exc_info.value.status_code == 409
        assert "Scanning already in progress for minsk" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_trigger_scan_different_cities_allowed(self):
        """Запуск сканирования для разных городов разрешён."""
        from unittest.mock import AsyncMock, MagicMock, patch
        from app.api.v1.scan import ScanTriggerRequest

        # Создать mock scheduler - город не сканируется
        mock_scheduler = MagicMock()
        mock_scheduler._is_city_scanning = MagicMock(return_value=False)

        # Mock для scan_record
        mock_scan_record = MagicMock()
        mock_scan_record.id = "scan-123"

        # Mock для scan_history_service
        mock_scan_history_service = MagicMock()
        mock_scan_history_service.create_scan_record = AsyncMock(return_value=mock_scan_record)

        request = ScanTriggerRequest(city="mogilev")
        background_tasks = MagicMock()

        with patch('app.api.v1.scan.get_scheduler', return_value=mock_scheduler):
            with patch('app.api.v1.scan.async_session_maker'):
                with patch('app.api.v1.scan.ScanHistoryService', return_value=mock_scan_history_service):
                    with patch('app.api.v1.scan._run_manual_scan'):
                        response = await trigger_scan(request, background_tasks)

        assert response.status == "started"
        assert response.city == "mogilev"


class TestWebSocketParallelScans:
    """Тесты для WebSocket с поддержкой параллельных сканирований."""

    @pytest.fixture
    def ws_manager(self):
        """Создать менеджер WebSocket подключений."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_update_scanning_cities(self, ws_manager):
        """Обновление списка сканируемых городов."""
        scanning_cities = [
            {
                "city": "minsk",
                "city_name": "Минск",
                "trigger_type": "manual",
                "started_at": "2025-03-07T14:32:15",
                "progress": {"stage": "fetching", "pages_scraped": 10}
            },
            {
                "city": "mogilev",
                "city_name": "Могилёв",
                "trigger_type": "scheduled",
                "started_at": "2025-03-07T14:30:00",
                "progress": {"stage": "upserting", "pages_scraped": 50}
            }
        ]

        await ws_manager.update_scanning_cities(scanning_cities)

        assert len(ws_manager.scanning_cities) == 2
        assert ws_manager.scanning_cities[0]["city"] == "minsk"
        assert ws_manager.scanning_cities[1]["city"] == "mogilev"

    @pytest.mark.asyncio
    async def test_broadcast_message_format(self, ws_manager):
        """Формат сообщения при broadcast."""
        scanning_cities = [
            {
                "city": "minsk",
                "city_name": "Минск",
                "trigger_type": "manual",
                "started_at": "2025-03-07T14:32:15",
                "progress": {"stage": "fetching"}
            }
        ]

        await ws_manager.update_scanning_cities(scanning_cities)

        message = ws_manager._get_current_message()

        assert "scanning_cities" in message
        assert len(message["scanning_cities"]) == 1
        assert message["scanning_cities"][0]["city"] == "minsk"


class TestScanStatusEndpoint:
    """Тесты для GET /api/v1/scan/status."""

    @pytest.fixture
    def mock_scheduler(self):
        """Создать mock scheduler."""
        scheduler = MagicMock()
        scheduler.is_running = False
        scheduler.scheduler = MagicMock()
        scheduler.scheduler.running = True
        scheduler._get_scanning_cities = MagicMock(return_value=[])
        return scheduler

    def test_status_no_scanning(self, mock_scheduler):
        """Статус когда нет активных сканирований."""
        from app.api.v1.scan import get_status
        from unittest.mock import patch

        with patch('app.api.v1.scan.get_scheduler', return_value=mock_scheduler):
            result = asyncio.get_event_loop().run_until_complete(get_status())

        assert result["scanning_cities"] == []
        assert result["scheduler_running"] is True
        assert result["is_running"] is False

    def test_status_with_scanning(self, mock_scheduler):
        """Статус с активными сканированиями."""
        from app.api.v1.scan import get_status
        from unittest.mock import patch

        mock_scheduler._get_scanning_cities = MagicMock(return_value=[
            {"city": "minsk", "city_name": "Минск", "trigger_type": "manual"}
        ])
        mock_scheduler.is_running = True

        with patch('app.api.v1.scan.get_scheduler', return_value=mock_scheduler):
            result = asyncio.get_event_loop().run_until_complete(get_status())

        assert len(result["scanning_cities"]) == 1
        assert result["scanning_cities"][0]["city"] == "minsk"
        assert result["is_running"] is True


class TestProgressEndpoint:
    """Тесты для GET /api/v1/scan/progress."""

    @pytest.fixture
    def mock_scheduler(self):
        """Создать mock scheduler."""
        scheduler = MagicMock()
        scheduler.scan_progress = {"stage": "idle", "is_scanning": False}
        scheduler._get_scanning_cities = MagicMock(return_value=[])
        return scheduler

    def test_progress_no_scanning(self, mock_scheduler):
        """Прогресс когда нет активных сканирований."""
        from app.api.v1.scan import get_progress
        from unittest.mock import patch

        with patch('app.api.v1.scan.get_scheduler', return_value=mock_scheduler):
            result = asyncio.get_event_loop().run_until_complete(get_progress())

        assert result["scanning_cities"] == []
        assert "global_progress" in result

    def test_progress_with_scanning(self, mock_scheduler):
        """Прогресс с активными сканированиями."""
        from app.api.v1.scan import get_progress
        from unittest.mock import patch

        mock_scheduler._get_scanning_cities = MagicMock(return_value=[
            {
                "city": "minsk",
                "city_name": "Минск",
                "progress": {"stage": "fetching", "pages_scraped": 10}
            }
        ])

        with patch('app.api.v1.scan.get_scheduler', return_value=mock_scheduler):
            result = asyncio.get_event_loop().run_until_complete(get_progress())

        assert len(result["scanning_cities"]) == 1
        assert result["global_progress"]["stage"] == "fetching"


class TestRaceConditions:
    """Тесты на race conditions при параллельном запуске."""

    @pytest.mark.asyncio
    async def test_concurrent_add_remove(self):
        """Одновременное добавление/удаление разных городов."""
        from app.scraper.scheduler import ScraperScheduler

        scheduler = ScraperScheduler()

        async def add_city(city: str):
            await scheduler._add_scanning_city(city, "manual", f"scan-{city}")

        async def remove_city(city: str):
            await asyncio.sleep(0.01)  # Небольшая задержка
            await scheduler._remove_scanning_city(city)

        # Запустить 3 сканирования параллельно
        tasks = [
            asyncio.create_task(add_city("minsk")),
            asyncio.create_task(add_city("mogilev")),
            asyncio.create_task(add_city("grodno")),
        ]

        await asyncio.gather(*tasks)

        assert scheduler._is_city_scanning("minsk")
        assert scheduler._is_city_scanning("mogilev")
        assert scheduler._is_city_scanning("grodno")
        assert len(scheduler._get_scanning_cities()) == 3

        # Удалить все сканирования
        await scheduler._remove_scanning_city("minsk")
        await scheduler._remove_scanning_city("mogilev")
        await scheduler._remove_scanning_city("grodno")

        assert len(scheduler._get_scanning_cities()) == 0

    @pytest.mark.asyncio
    async def test_concurrent_same_city(self):
        """Попытка одновременного запуска для одного города."""
        from app.scraper.scheduler import ScraperScheduler

        scheduler = ScraperScheduler()

        # Первое сканирование
        await scheduler._add_scanning_city("minsk", "manual", "scan-1")

        # Проверка должна показать что город уже сканируется
        assert scheduler._is_city_scanning("minsk")

        # Второе сканирование для того же города должно быть заблокировано
        # (это проверяется на уровне API, не в scheduler)


class TestCleanupOnError:
    """Тесты на очистку scanning_cities после ошибок."""

    @pytest.mark.asyncio
    async def test_cleanup_after_exception(self):
        """Очистка scanning_cities после исключения."""
        from app.scraper.scheduler import ScraperScheduler

        scheduler = ScraperScheduler()

        # Имитация добавления и последующей ошибки
        await scheduler._add_scanning_city("minsk", "manual", "scan-123")
        assert scheduler._is_city_scanning("minsk")

        # Имитация очистки (как в finally блоке)
        await scheduler._remove_scanning_city("minsk")

        assert not scheduler._is_city_scanning("minsk")
        assert len(scheduler._get_scanning_cities()) == 0
