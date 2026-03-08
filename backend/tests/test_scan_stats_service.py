"""
Тесты для ScanStatsService - валидация аномалий сканирования
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from app.services.scan_stats_service import ScanStatsService
from app.models.listing import ScanStats


@pytest.mark.asyncio
class TestScanStatsService:
    """Тесты для ScanStatsService."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def scan_stats_service(self, db_mock):
        """Создание сервиса статистики."""
        return ScanStatsService(db_mock)

    async def test_get_city_stats_found(self, scan_stats_service, db_mock):
        """Проверка получения статистики по городу."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 520, 510]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        result = await scan_stats_service.get_city_stats("minsk")

        assert result == mock_stats
        assert result.city == "minsk"
        assert result.avg_listings_count == 500

    async def test_get_city_stats_not_found(self, scan_stats_service, db_mock):
        """Проверка получения несуществующей статистики."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        result = await scan_stats_service.get_city_stats("minsk")

        assert result is None

    async def test_get_or_create_stats_exists(self, scan_stats_service, db_mock):
        """Проверка получения существующей статистики."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_stats, None]
        db_mock.execute.return_value = mock_result

        result = await scan_stats_service.get_or_create_stats("minsk")

        assert result == mock_stats
        db_mock.add.assert_not_called()

    async def test_get_or_create_stats_creates_new(self, scan_stats_service, db_mock):
        """Проверка создания новой статистики."""
        # Первый вызов - не найдено, второй - создано
        mock_new_stats = MagicMock(spec=ScanStats)
        mock_new_stats.city = "minsk"
        mock_new_stats.avg_listings_count = 0
        mock_new_stats.recent_counts = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [None, mock_new_stats]
        db_mock.execute.return_value = mock_result

        result = await scan_stats_service.get_or_create_stats("minsk")

        assert db_mock.add.called
        assert result.city == "minsk"

    async def test_update_stats(self, scan_stats_service, db_mock):
        """Проверка обновления статистики."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 520, 510]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        result = await scan_stats_service.update_stats("minsk", 550)

        assert db_mock.commit.called
        assert db_mock.refresh.called
        # Проверка что 550 добавлено в recent_counts
        assert 550 in mock_stats.recent_counts

    async def test_update_stats_with_db_session(self, scan_stats_service, db_mock):
        """Проверка обновления статистики (db_session параметр удалён)."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 520, 510]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # db_session параметр удалён - используется self.db
        result = await scan_stats_service.update_stats("minsk", 550)

        db_mock.commit.assert_called()
        db_mock.refresh.assert_called()
        assert 550 in mock_stats.recent_counts

    async def test_update_stats_keeps_last_10(self, scan_stats_service, db_mock):
        """Проверка что хранятся только последние 10 значений."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [400, 420, 440, 460, 480, 500, 520, 540, 560, 580]  # 10 значений

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        await scan_stats_service.update_stats("minsk", 600)

        # Должно быть 10 значений (последние 9 + новое)
        assert len(mock_stats.recent_counts) == 10
        assert 600 in mock_stats.recent_counts
        assert 400 not in mock_stats.recent_counts  # Первое значение удалено

    async def test_update_stats_no_commit_does_not_commit(self, scan_stats_service, db_mock):
        """Проверка что update_stats_no_commit() не делает commit()."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 520, 510]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Создаём отдельный mock для db_session
        db_session_mock = MagicMock()
        db_session_mock.execute = AsyncMock()
        db_session_mock.add = MagicMock()
        db_session_mock.commit = AsyncMock()
        db_session_mock.refresh = AsyncMock()

        mock_result_session = MagicMock()
        mock_result_session.scalar_one_or_none.return_value = mock_stats
        db_session_mock.execute.return_value = mock_result_session

        result = await scan_stats_service.update_stats_no_commit("minsk", 550, db_session_mock)

        # Проверяем что commit() НЕ вызван на переданной сессии
        db_session_mock.commit.assert_not_called()
        # Проверяем что add() был вызван (если запись существует, add не вызывается)
        # В данном случае запись существует, поэтому add не должен вызываться
        db_session_mock.add.assert_not_called()
        assert 550 in mock_stats.recent_counts

    async def test_update_stats_no_commit_creates_new(self, db_mock):
        """Проверка что update_stats_no_commit() создаёт новую запись если не найдена."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        # Создаём отдельный mock для db_session
        db_session_mock = MagicMock()
        db_session_mock.execute = AsyncMock()
        db_session_mock.add = MagicMock()
        db_session_mock.commit = AsyncMock()

        # Возвращаем None - запись не найдена
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_session_mock.execute.return_value = mock_result

        result = await service.update_stats_no_commit("minsk", 550, db_session_mock)

        # Проверяем что add() был вызван для создания новой записи
        db_session_mock.add.assert_called_once()
        # Проверяем что commit() НЕ вызван
        db_session_mock.commit.assert_not_called()
        assert result.city == "minsk"
        assert result.avg_listings_count == 550

    async def test_get_or_create_stats_no_commit_does_not_commit(self, db_mock):
        """Проверка что _get_or_create_stats_no_commit() не делает commit()."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        # Создаём отдельный mock для db_session
        db_session_mock = MagicMock()
        db_session_mock.execute = AsyncMock()
        db_session_mock.add = MagicMock()
        db_session_mock.commit = AsyncMock()

        # Возвращаем None - запись не найдена
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_session_mock.execute.return_value = mock_result

        result = await service._get_or_create_stats_no_commit("minsk", db_session_mock)

        # Проверяем что add() был вызван для создания новой записи
        db_session_mock.add.assert_called_once()
        # Проверяем что commit() НЕ вызван
        db_session_mock.commit.assert_not_called()
        assert result.city == "minsk"
        assert result.recent_counts == []

    async def test_get_or_create_stats_no_commit_exists(self, db_mock):
        """Проверка что _get_or_create_stats_no_commit() возвращает существующую запись."""
        from app.services.scan_stats_service import ScanStatsService
        from app.models.listing import ScanStats

        service = ScanStatsService(db_mock)

        # Создаём отдельный mock для db_session
        db_session_mock = MagicMock()
        db_session_mock.execute = AsyncMock()
        db_session_mock.add = MagicMock()
        db_session_mock.commit = AsyncMock()

        # Возвращаем существующую запись
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_session_mock.execute.return_value = mock_result

        result = await service._get_or_create_stats_no_commit("minsk", db_session_mock)

        # Проверяем что add() НЕ вызван (запись существует)
        db_session_mock.add.assert_not_called()
        # Проверяем что commit() НЕ вызван
        db_session_mock.commit.assert_not_called()
        assert result == mock_stats

    async def test_validate_listings_count_insufficient_data(
        self, scan_stats_service, db_mock
    ):
        """Проверка валидации при недостатке данных."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 0  # Нет среднего
        mock_stats.recent_counts = [500]  # Только 1 запись (нужно минимум 3)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "minsk", 450
        )

        assert is_valid is True
        assert "Первое сканирование" in message

    async def test_validate_listings_count_no_stats(self, scan_stats_service, db_mock):
        """Проверка валидации при отсутствии статистики."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "minsk", 100
        )

        assert is_valid is True
        assert "Первое сканирование" in message

    async def test_validate_listings_count_first_scan_zero_anomaly(
        self, scan_stats_service, db_mock
    ):
        """Проверка: первое сканирование с 0 объявлений → аномалия."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "minsk", 0
        )

        assert is_valid is False
        assert "⚠️ Первое сканирование: 0 объявлений" in message
        assert "возможна ошибка API" in message

    async def test_validate_listings_count_anomaly_detected(
        self, scan_stats_service, db_mock
    ):
        """Проверка обнаружения аномалии (получено < 90% от ожидаемого)."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]  # Среднее 500

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Получено 400 объявлений (80% от 500) - аномалия
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "minsk", 400
        )

        assert is_valid is False
        assert "Аномалия" in message
        assert "менее 90%" in message
        assert expected == 500

    async def test_validate_listings_count_passed(self, scan_stats_service, db_mock):
        """Проверка успешной валидации (получено >= 90% от ожидаемого)."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Получено 460 объявлений (92% от 500) - норма
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "minsk", 460
        )

        assert is_valid is True
        assert message == "OK"

    async def test_validate_listings_count_boundary_90_percent(
        self, scan_stats_service, db_mock
    ):
        """Проверка граничного случая (ровно 90%)."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Получено 450 объявлений (ровно 90%) - норма (граница)
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "minsk", 450
        )

        assert is_valid is True

    async def test_validate_listings_count_below_90_percent(
        self, scan_stats_service, db_mock
    ):
        """Проверка случая ниже 90% (449 из 500)."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Получено 449 объявлений (89.8%) - аномалия
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "minsk", 449
        )

        assert is_valid is False
        assert "Аномалия" in message
        assert "менее 90%" in message

    async def test_reset_stats(self, scan_stats_service, db_mock):
        """Проверка сброса статистики."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        await scan_stats_service.reset_stats("minsk")

        assert mock_stats.recent_counts == []
        assert mock_stats.avg_listings_count == 0
        db_mock.commit.called

    async def test_validate_listings_count_with_for_update_called(
        self, scan_stats_service, db_mock
    ):
        """Проверка что with_for_update() вызывается для блокировки строки."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # use_lock=True по умолчанию
        is_valid, message, expected = await scan_stats_service.validate_listings_count("minsk", 460)

        assert is_valid is True
        # Проверка что execute был вызван
        assert db_mock.execute.called


@pytest.mark.asyncio
class TestScanStatsServiceScenarios:
    """Сценарные тесты для ScanStatsService."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def scan_stats_service(self, db_mock):
        """Создание сервиса статистики."""
        return ScanStatsService(db_mock)

    async def test_scenario_partial_load_150_of_500(self, db_mock):
        """Сценарий: частичная загрузка 150 из 500 → аномалия."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        # Настраиваем статистику: среднее 500 объявлений
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520, 490, 510]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Получено только 150 объявлений (30%)
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 150
        )

        assert is_valid is False, "Должна быть обнаружена аномалия"
        assert "Аномалия" in message
        assert "получено 150" in message
        assert "ожидалось ~500" in message
        assert "менее 90%" in message

    async def test_scenario_zero_listings(self, db_mock):
        """Сценарий: 0 объявлений → аномалия."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 0
        )

        assert is_valid is False
        assert "Аномалия" in message
        assert "получено 0" in message
        assert "менее 90%" in message

    async def test_scenario_normal_scan(self, db_mock):
        """Сценарий: нормальное сканирование 480 из 500 → валидно."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 480
        )

        assert is_valid is True
        assert message == "OK"

    async def test_scenario_boundary_89_percent(self, db_mock):
        """Сценарий: 89% (445 из 500) → аномалия."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # 445 из 500 = 89%
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 445
        )

        assert is_valid is False
        assert "Аномалия" in message
        assert "менее 90%" in message

    async def test_scenario_boundary_90_percent(self, db_mock):
        """Сценарий: 90% (450 из 500) → валидно (граница)."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # 450 из 500 = 90% (ровно граница)
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 450
        )

        assert is_valid is True
        assert message == "OK"

    async def test_scenario_boundary_91_percent(self, db_mock):
        """Сценарий: 91% (455 из 500) → валидно."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # 455 из 500 = 91%
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 455
        )

        assert is_valid is True
        assert message == "OK"

    async def test_scenario_boundary_80_percent(self, db_mock):
        """Сценарий: 80% (400 из 500) → аномалия (теперь детектируется)."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # 400 из 500 = 80% (раньше пропускалось, теперь аномалия)
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 400
        )

        assert is_valid is False
        assert "Аномалия" in message
        assert "менее 90%" in message

    async def test_scenario_first_scan_with_listings(self, db_mock):
        """Сценарий: первое сканирование с > 0 объявлений → валидно."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        # Первое сканирование, получено 500 объявлений
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 500
        )

        assert is_valid is True
        assert "Первое сканирование" in message
        assert "валидация отключена" in message

    async def test_scenario_first_scan_zero_listings_anomaly(self, db_mock):
        """Сценарий: первое сканирование с 0 объявлений → аномалия."""
        from app.services.scan_stats_service import ScanStatsService

        service = ScanStatsService(db_mock)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        # Первое сканирование, получено 0 объявлений - аномалия!
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 0
        )

        assert is_valid is False
        assert "⚠️ Первое сканирование: 0 объявлений" in message
        assert "возможна ошибка API" in message

    async def test_scenario_first_scan_9_listings_anomaly(self, db_mock):
        """Сценарий: первое сканирование с 9 объявлениями → аномалия (меньше порога 10)."""
        from app.services.scan_stats_service import ScanStatsService, MIN_FIRST_SCAN_LISTINGS

        service = ScanStatsService(db_mock)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        # Первое сканирование, получено 9 объявлений (меньше MIN_FIRST_SCAN_LISTINGS=10)
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 9
        )

        assert is_valid is False, "9 объявлений должно быть аномалией (порог 10)"
        assert "⚠️ Первое сканирование: 9 < 10" in message
        assert "минимальный порог" in message

    async def test_scenario_first_scan_10_listings_valid_boundary(self, db_mock):
        """Сценарий: первое сканирование с 10 объявлениями → валидно (граница порога)."""
        from app.services.scan_stats_service import ScanStatsService, MIN_FIRST_SCAN_LISTINGS

        service = ScanStatsService(db_mock)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        # Первое сканирование, получено 10 объявлений (ровно граница MIN_FIRST_SCAN_LISTINGS=10)
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 10
        )

        assert is_valid is True, "10 объявлений должно быть валидно (граница порога)"
        assert "Первое сканирование" in message
        assert "валидация отключена" in message

    async def test_scenario_first_scan_11_listings_valid(self, db_mock):
        """Сценарий: первое сканирование с 11 объявлениями → валидно (выше порога)."""
        from app.services.scan_stats_service import ScanStatsService, MIN_FIRST_SCAN_LISTINGS

        service = ScanStatsService(db_mock)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        # Первое сканирование, получено 11 объявлений (выше MIN_FIRST_SCAN_LISTINGS=10)
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 11
        )

        assert is_valid is True, "11 объявлений должно быть валидно (выше порога)"
        assert "Первое сканирование" in message
        assert "валидация отключена" in message

    async def test_validate_listings_count_with_lock_skip_locked(self, db_mock):
        """Проверка что with_for_update(skip_locked=True) используется для предотвращения deadlock."""
        from app.services.scan_stats_service import ScanStatsService
        from app.models.listing import ScanStats

        service = ScanStatsService(db_mock)

        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 500
        mock_stats.recent_counts = [480, 500, 520]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Вызываем с use_lock=True
        is_valid, message, expected = await service.validate_listings_count(
            "minsk", 460, use_lock=True
        )

        assert is_valid is True
        # Проверка что execute был вызван (query с with_for_update(skip_locked=True) выполнен)
        assert db_mock.execute.called

    async def test_validate_insufficient_history_with_avg_anomaly(
        self, scan_stats_service, db_mock
    ):
        """Проверка: недостаточно истории (< 3) но есть среднее → аномалия (150 из 438)."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "grodno"
        mock_stats.avg_listings_count = 438  # Среднее есть
        mock_stats.recent_counts = [727]  # Но только 1 запись в истории

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Получено 150 объявлений (34% от 438) - аномалия
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "grodno", 150
        )

        assert is_valid is False, "Должна быть обнаружена аномалия"
        assert "Аномалия" in message
        assert "получено 150" in message
        assert "ожидалось ~438" in message
        assert "менее 90%" in message
        assert expected == 438

    async def test_validate_insufficient_history_with_avg_valid(
        self, scan_stats_service, db_mock
    ):
        """Проверка: недостаточно истории (< 3) но есть среднее → валидно (400 из 438)."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "grodno"
        mock_stats.avg_listings_count = 438  # Среднее есть
        mock_stats.recent_counts = [727]  # Но только 1 запись в истории

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Получено 400 объявлений (91% от 438) - валидно
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "grodno", 400
        )

        assert is_valid is True, "Должно быть валидно"
        assert "Валидация пройдена (по среднему)" in message
        assert expected == 438

    async def test_validate_insufficient_history_zero_avg_first_scan(
        self, scan_stats_service, db_mock
    ):
        """Проверка: недостаточно истории и avg_listings_count = 0 → первое сканирование."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "minsk"
        mock_stats.avg_listings_count = 0  # Нет среднего
        mock_stats.recent_counts = []  # Пустая история

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # Первое сканирование с нормальным количеством
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "minsk", 500
        )

        assert is_valid is True
        assert "Первое сканирование — валидация отключена" in message
        assert expected == 0

    async def test_validate_insufficient_history_boundary_90_percent(
        self, scan_stats_service, db_mock
    ):
        """Проверка: недостаточно истории, среднее 438, получено 395 (>= 90%) → валидно."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "grodno"
        mock_stats.avg_listings_count = 438
        mock_stats.recent_counts = [727]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # 438 * 0.9 = 394.2, 395 >= 394.2 (выше границы 90%)
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "grodno", 395
        )

        assert is_valid is True
        assert "Валидация пройдена (по среднему)" in message

    async def test_validate_insufficient_history_below_90_percent(
        self, scan_stats_service, db_mock
    ):
        """Проверка: недостаточно истории, среднее 438, получено 393 (89.7%) → аномалия."""
        mock_stats = MagicMock(spec=ScanStats)
        mock_stats.city = "grodno"
        mock_stats.avg_listings_count = 438
        mock_stats.recent_counts = [727]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        db_mock.execute.return_value = mock_result

        # 393 < 438 * 0.9 = 394.2 (ниже границы 90%)
        is_valid, message, expected = await scan_stats_service.validate_listings_count(
            "grodno", 393
        )

        assert is_valid is False
        assert "Аномалия" in message
