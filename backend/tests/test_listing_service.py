"""
Тесты для ListingService
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.services.listing_service import ListingService
from app.models.listing import Listing, ListingStatus, EventType, ListingHistory


@pytest.mark.asyncio
class TestListingService:
    """Тесты для ListingService."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def listing_service(self, db_mock):
        """Создание сервиса listings."""
        return ListingService(db_mock)

    async def test_get_by_kufar_id_found(self, listing_service, db_mock):
        """Проверка получения объявления по kufar_id."""
        mock_listing = MagicMock(spec=Listing)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_listing
        db_mock.execute.return_value = mock_result

        result = await listing_service.get_by_kufar_id("123456")

        assert result == mock_listing
        db_mock.execute.assert_called_once()

    async def test_get_by_kufar_id_not_found(self, listing_service, db_mock):
        """Проверка получения несуществующего объявления."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        result = await listing_service.get_by_kufar_id("nonexistent")

        assert result is None

    async def test_create_history_event(self, listing_service, db_mock):
        """Проверка создания события истории."""
        listing_id = uuid4()
        event_type = EventType.price_changed
        price_before = 100000
        price_after = 120000
        snapshot = {"price": 120000}

        await listing_service._create_history_event(
            listing_id=listing_id,
            event_type=event_type,
            price_before=price_before,
            price_after=price_after,
            snapshot=snapshot,
        )

        assert db_mock.add.called
        added_event = db_mock.add.call_args[0][0]
        assert isinstance(added_event, ListingHistory)
        assert added_event.listing_id == listing_id
        assert added_event.event_type == event_type
        assert added_event.price_before == price_before
        assert added_event.price_after == price_after
        assert added_event.snapshot == snapshot

    async def test_create_history_event_minimal(self, listing_service, db_mock):
        """Проверка создания события истории с минимальными данными."""
        listing_id = uuid4()
        event_type = EventType.created

        await listing_service._create_history_event(
            listing_id=listing_id,
            event_type=event_type,
        )

        assert db_mock.add.called
        added_event = db_mock.add.call_args[0][0]
        assert added_event.listing_id == listing_id
        assert added_event.event_type == event_type
        assert added_event.price_before is None
        assert added_event.price_after is None
        assert added_event.changed_fields is None
        assert added_event.snapshot is None


@pytest.mark.asyncio
class TestListingServiceUpsert:
    """Тесты для upsert с использованием мок базы данных."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    async def test_create_new_listing(self, db_mock):
        """Проверка создания нового объявления."""
        service = ListingService(db_mock)

        listing_data = {
            "kufar_id": "test_new_123",
            "url": "https://re.kufar.by/vi/123456",
            "title": "New Test Apartment",
            "price": 150000,
            "price_usd": 50000,
            "currency": "BYN",
            "city": "minsk",
            "address": "Test Street 1",
            "rooms": 2,
            "area": 55.0,
            "floor": 3,
            "total_floors": 9,
            "category": "apartments",
        }

        # Mock для get_by_kufar_id - возвращаем None (объявление не существует)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        # Mock для commit/refresh
        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        result, action = await service.upsert(listing_data)

        assert result is not None
        assert action == 'created'
        db_mock.add.assert_called()

    async def test_update_listing_price_usd(self, db_mock):
        """Проверка обновления объявления при изменении цены USD."""
        service = ListingService(db_mock)

        # Существующее объявление
        existing = MagicMock(spec=Listing)
        existing.price_usd = 35000
        existing.price = 100000
        existing.status = ListingStatus.active
        existing.id = uuid4()
        existing.kufar_id = "test_123"

        # Mock для get_by_kufar_id - возвращаем существующее объявление
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db_mock.execute.return_value = mock_result

        updated_data = {
            "kufar_id": "test_123",
            "url": "https://re.kufar.by/vi/123456",
            "title": "Test Apartment",
            "price": 100000,
            "price_usd": 40000,  # Changed from 35000
            "currency": "BYN",
            "city": "minsk",
            "address": "Test Street 1",
            "rooms": 2,
            "area": 55.0,
            "floor": 3,
            "total_floors": 9,
            "category": "apartments",
        }

        async def mock_refresh(obj):
            pass

        db_mock.refresh.side_effect = mock_refresh

        result, action = await service.upsert(updated_data)

        assert result is not None
        assert action == 'updated'
        assert existing.status == ListingStatus.updated

    async def test_update_listing_price_byn_only(self, db_mock):
        """Проверка обновления объявления при изменении только цены BYN."""
        service = ListingService(db_mock)

        # Существующее объявление
        existing = MagicMock(spec=Listing)
        existing.price_usd = 35000
        existing.price = 100000
        existing.status = ListingStatus.active
        existing.id = uuid4()
        existing.kufar_id = "test_123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db_mock.execute.return_value = mock_result

        updated_data = {
            "kufar_id": "test_123",
            "url": "https://re.kufar.by/vi/123456",
            "title": "Test Apartment",
            "price": 110000,  # Changed from 100000
            "price_usd": 35000,  # Same
            "currency": "BYN",
            "city": "minsk",
            "address": "Test Street 1",
            "rooms": 2,
            "area": 55.0,
            "floor": 3,
            "total_floors": 9,
            "category": "apartments",
        }

        async def mock_refresh(obj):
            pass

        db_mock.refresh.side_effect = mock_refresh

        result, action = await service.upsert(updated_data)

        assert result is not None
        assert action == 'changed_byn'
        assert existing.status == ListingStatus.price_changed_byn

    async def test_update_listing_no_changes(self, db_mock):
        """Проверка обновления без изменений."""
        service = ListingService(db_mock)

        # Существующее объявление
        existing = MagicMock(spec=Listing)
        existing.price_usd = 35000
        existing.price = 100000
        existing.status = ListingStatus.active
        existing.id = uuid4()
        existing.kufar_id = "test_123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db_mock.execute.return_value = mock_result

        updated_data = {
            "kufar_id": "test_123",
            "url": "https://re.kufar.by/vi/123456",
            "title": "Test Apartment",
            "price": 100000,
            "price_usd": 35000,
            "currency": "BYN",
            "city": "minsk",
            "address": "Test Street 1",
            "rooms": 2,
            "area": 55.0,
            "floor": 3,
            "total_floors": 9,
            "category": "apartments",
        }

        async def mock_refresh(obj):
            pass

        db_mock.refresh.side_effect = mock_refresh

        result, action = await service.upsert(updated_data)

        assert result is not None
        assert action == 'unchanged'
        assert existing.status == ListingStatus.active

    async def test_restore_deleted_listing(self, db_mock):
        """Проверка восстановления удалённого объявления."""
        service = ListingService(db_mock)

        # Существующее удалённое объявление
        existing = MagicMock(spec=Listing)
        existing.price_usd = 35000
        existing.price = 100000
        existing.status = ListingStatus.deleted
        existing.deleted_at = datetime.now()
        existing.id = uuid4()
        existing.kufar_id = "test_123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db_mock.execute.return_value = mock_result

        updated_data = {
            "kufar_id": "test_123",
            "url": "https://re.kufar.by/vi/123456",
            "title": "Test Apartment",
            "price": 100000,
            "price_usd": 35000,
            "currency": "BYN",
            "city": "minsk",
            "address": "Test Street 1",
            "rooms": 2,
            "area": 55.0,
            "floor": 3,
            "total_floors": 9,
            "category": "apartments",
        }

        async def mock_refresh(obj):
            pass

        db_mock.refresh.side_effect = mock_refresh

        result, action = await service.upsert(updated_data)

        assert result is not None
        assert action == 'restored'
        assert existing.status == ListingStatus.active
        assert existing.deleted_at is None

    async def test_preserve_updated_status_on_subsequent_scan(self, db_mock):
        """Проверка сохранения статуса updated при последующем сканировании без изменений цены.
        
        Сценарий:
        1. Объявление имеет статус updated (цена USD изменилась в предыдущем сканировании)
        2. Следующее сканирование: цена не изменилась
        3. Ожидаем: статус остаётся updated, а не сбрасывается на active
        """
        service = ListingService(db_mock)

        # Существующее объявление со статусом updated
        existing = MagicMock(spec=Listing)
        existing.price_usd = 40000  # Цена после изменения
        existing.price = 120000
        existing.status = ListingStatus.updated  # Статус из предыдущего сканирования
        existing.id = uuid4()
        existing.kufar_id = "test_123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db_mock.execute.return_value = mock_result

        # Данные текущего сканирования (цена не изменилась)
        scan_data = {
            "kufar_id": "test_123",
            "url": "https://re.kufar.by/vi/123456",
            "title": "Test Apartment",
            "price": 120000,  # Same
            "price_usd": 40000,  # Same
            "currency": "BYN",
            "city": "minsk",
            "address": "Test Street 1",
            "rooms": 2,
            "area": 55.0,
            "floor": 3,
            "total_floors": 9,
            "category": "apartments",
        }

        async def mock_refresh(obj):
            pass

        db_mock.refresh.side_effect = mock_refresh

        result, action = await service.upsert(scan_data)

        assert result is not None
        assert action == 'unchanged'
        assert existing.status == ListingStatus.updated  # Статус сохранён!

    async def test_preserve_price_changed_byn_status_on_subsequent_scan(self, db_mock):
        """Проверка сохранения статуса price_changed_byn при последующем сканировании.
        
        Сценарий:
        1. Объявление имеет статус price_changed_byn
        2. Следующее сканирование: цена не изменилась
        3. Ожидаем: статус остаётся price_changed_byn
        """
        service = ListingService(db_mock)

        # Существующее объявление со статусом price_changed_byn
        existing = MagicMock(spec=Listing)
        existing.price_usd = 35000
        existing.price = 110000
        existing.status = ListingStatus.price_changed_byn
        existing.id = uuid4()
        existing.kufar_id = "test_456"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db_mock.execute.return_value = mock_result

        scan_data = {
            "kufar_id": "test_456",
            "url": "https://re.kufar.by/vi/456789",
            "title": "Test Apartment 2",
            "price": 110000,  # Same
            "price_usd": 35000,  # Same
            "currency": "BYN",
            "city": "minsk",
            "address": "Test Street 2",
            "rooms": 3,
            "area": 65.0,
            "floor": 5,
            "total_floors": 12,
            "category": "apartments",
        }

        async def mock_refresh(obj):
            pass

        db_mock.refresh.side_effect = mock_refresh

        result, action = await service.upsert(scan_data)

        assert result is not None
        assert action == 'unchanged'
        assert existing.status == ListingStatus.price_changed_byn  # Статус сохранён!

    async def test_reset_new_status_to_active_on_subsequent_scan(self, db_mock):
        """Проверка сброса статуса new на active при последующем сканировании.
        
        Сценарий:
        1. Объявление имеет статус new (только что создано)
        2. Следующее сканирование: цена не изменилась
        3. Ожидаем: статус сбрасывается на active
        """
        service = ListingService(db_mock)

        # Существующее объявление со статусом new
        existing = MagicMock(spec=Listing)
        existing.price_usd = 35000
        existing.price = 100000
        existing.status = ListingStatus.new
        existing.id = uuid4()
        existing.kufar_id = "test_789"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db_mock.execute.return_value = mock_result

        scan_data = {
            "kufar_id": "test_789",
            "url": "https://re.kufar.by/vi/789012",
            "title": "Test Apartment 3",
            "price": 100000,  # Same
            "price_usd": 35000,  # Same
            "currency": "BYN",
            "city": "minsk",
            "address": "Test Street 3",
            "rooms": 1,
            "area": 40.0,
            "floor": 2,
            "total_floors": 5,
            "category": "apartments",
        }

        async def mock_refresh(obj):
            pass

        db_mock.refresh.side_effect = mock_refresh

        result, action = await service.upsert(scan_data)

        assert result is not None
        assert action == 'unchanged'
        assert existing.status == ListingStatus.active  # Статус сброшен на active!


@pytest.mark.asyncio
class TestListingServiceUpsertListings:
    """Тесты для upsert_listings."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    async def test_upsert_listings_multiple(self, db_mock):
        """Проверка массового обновления объявлений."""
        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 1",
                "rooms": 2,
                "area": 50.0,
                "floor": 3,
                "category": "apartments",
            },
            {
                "kufar_id": "test_2",
                "url": "https://re.kufar.by/vi/2",
                "title": "Test 2",
                "price": 120000,
                "price_usd": 40000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 2",
                "rooms": 3,
                "area": 60.0,
                "floor": 5,
                "category": "apartments",
            },
        ]

        # Mock для get_by_kufar_id - все новые
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        # Mock для mark_deleted
        async def mock_mark_deleted(kufar_ids, city):
            return 0

        service.mark_deleted = mock_mark_deleted

        stats = await service.upsert_listings(listings_data, "minsk")

        assert stats["processed"] == 2
        assert stats["created"] == 2
        assert stats["updated"] == 0
        assert stats["deleted"] == 0

    async def test_upsert_listings_with_deletions(self, db_mock):
        """Проверка массового обновления с маркировкой удалённых."""
        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 1",
                "rooms": 2,
                "area": 50.0,
                "floor": 3,
                "category": "apartments",
            },
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        # Mock для mark_deleted - возвращаем 1 удалённое
        async def mock_mark_deleted(kufar_ids, city):
            return 1

        service.mark_deleted = mock_mark_deleted

        stats = await service.upsert_listings(listings_data, "minsk")

        assert stats["processed"] == 1
        assert stats["deleted"] == 1


@pytest.mark.asyncio
class TestListingServiceMarkDeleted:
    """Тесты для mark_deleted."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    async def test_mark_deleted(self, db_mock):
        """Проверка маркировки объявлений как удалённых."""
        service = ListingService(db_mock)

        # Mock для select - возвращаем список объявлений для удаления
        mock_listing = MagicMock(spec=Listing)
        mock_listing.status = ListingStatus.active
        mock_listing.deleted_at = None
        mock_listing.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_listing]
        db_mock.execute.return_value = mock_result

        active_ids = {"active_1", "active_2"}
        count = await service.mark_deleted(active_ids, "minsk")

        assert count == 1
        assert mock_listing.status == ListingStatus.deleted
        assert mock_listing.deleted_at is not None

    async def test_mark_deleted_no_listings(self, db_mock):
        """Проверка маркировки когда нет объявлений для удаления."""
        service = ListingService(db_mock)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db_mock.execute.return_value = mock_result

        active_ids = {"active_1"}
        count = await service.mark_deleted(active_ids, "minsk")

        assert count == 0


@pytest.mark.asyncio
class TestListingServiceUpsertListingsNoMarkDeleted:
    """Тесты для upsert_listings_no_mark_deleted."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.rollback = AsyncMock()
        return db

    async def test_upsert_listings_no_mark_deleted_multiple(self, db_mock):
        """Проверка массового обновления без mark_deleted."""
        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 1",
                "rooms": 2,
                "area": 50.0,
                "floor": 3,
                "category": "apartments",
            },
            {
                "kufar_id": "test_2",
                "url": "https://re.kufar.by/vi/2",
                "title": "Test 2",
                "price": 120000,
                "price_usd": 40000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 2",
                "rooms": 3,
                "area": 60.0,
                "floor": 5,
                "category": "apartments",
            },
        ]

        # Mock для get_by_kufar_id - все новые
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        stats = await service.upsert_listings_no_mark_deleted(listings_data, "minsk")

        assert stats["processed"] == 2
        assert stats["created"] == 2
        assert stats["deleted"] == 0  # mark_deleted не вызывался

    async def test_upsert_listings_no_mark_deleted_raises_on_error(self, db_mock):
        """Проверка что ошибка пробрасывается вверх."""
        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
            },
        ]

        # Mock для upsert - выбрасывает ошибку
        async def mock_upsert_error(data):
            raise Exception("Database error")

        service.upsert = mock_upsert_error

        with pytest.raises(Exception, match="Database error"):
            await service.upsert_listings_no_mark_deleted(listings_data, "minsk")


@pytest.mark.asyncio
class TestListingServiceUpsertListingsTransaction:
    """Тесты для upsert_listings_transaction."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.rollback = AsyncMock()
        return db

    async def test_upsert_listings_transaction_success(self, db_mock):
        """Проверка успешной транзакции."""
        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 1",
                "rooms": 2,
                "area": 50.0,
                "floor": 3,
                "category": "apartments",
            },
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        stats = await service.upsert_listings_transaction(listings_data, "minsk")

        assert stats["success"] is True
        assert stats["processed"] == 1
        assert stats["created"] == 1
        assert "kufar_ids" in stats
        assert len(stats["kufar_ids"]) == 1

    async def test_upsert_listings_transaction_rollback_on_error(self, db_mock):
        """Проверка отката транзакции при ошибке."""
        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
            },
            {
                "kufar_id": "test_2",
                "url": "https://re.kufar.by/vi/2",
                "title": "Test 2",
                "price": 120000,
                "price_usd": 40000,
                "currency": "BYN",
                "city": "minsk",
            },
        ]

        call_count = 0

        async def mock_upsert_side_effect(data):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Первое объявление успешно
                mock_listing = MagicMock(spec=Listing)
                mock_listing.kufar_id = data["kufar_id"]
                return mock_listing, "created"
            else:
                # Второе объявление - ошибка
                raise SQLAlchemyError("Database constraint violation")

        service.upsert = mock_upsert_side_effect

        with pytest.raises(SQLAlchemyError, match="Database constraint violation"):
            await service.upsert_listings_transaction(listings_data, "minsk")

        # Проверка что rollback был вызван
        db_mock.rollback.assert_called_once()

    async def test_upsert_listings_transaction_empty_data(self, db_mock):
        """Проверка транзакции с пустыми данными."""
        service = ListingService(db_mock)

        stats = await service.upsert_listings_transaction([], "minsk")

        assert stats["success"] is True
        assert stats["processed"] == 0
        assert stats["created"] == 0


@pytest.mark.asyncio
class TestListingServiceScenarios:
    """Сценарные тесты для ListingService."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.rollback = AsyncMock()
        return db

    async def test_scenario_partial_load_no_false_deleted(self, db_mock):
        """
        Сценарий: частичная загрузка (150 из 500) → нет false deleted.
        
        Проверяем что upsert_listings_no_mark_deleted не вызывает mark_deleted.
        """
        service = ListingService(db_mock)

        # Создаём 150 объявлений
        listings_data = [
            {
                "kufar_id": f"test_{i}",
                "url": f"https://re.kufar.by/vi/{i}",
                "title": f"Test {i}",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "address": f"Street {i}",
                "rooms": 2,
                "area": 50.0,
                "floor": 3,
                "category": "apartments",
            }
            for i in range(150)
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        stats = await service.upsert_listings_no_mark_deleted(listings_data, "minsk")

        assert stats["processed"] == 150
        assert stats["created"] == 150
        assert stats["deleted"] == 0  # mark_deleted не вызывался

    async def test_scenario_upsert_error_rollback(self, db_mock):
        """
        Сценарий: ошибка во время upsert → откат.
        
        Проверяем что при ошибке вызывается rollback.
        """
        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
            },
        ]

        async def mock_upsert_error(data):
            raise SQLAlchemyError("Constraint violation")

        service.upsert = mock_upsert_error

        with pytest.raises(SQLAlchemyError):
            await service.upsert_listings_transaction(listings_data, "minsk")

        # Проверка что rollback был вызван
        db_mock.rollback.assert_called_once()

    async def test_scenario_zero_listings_no_mark_deleted(self, db_mock):
        """
        Сценарий: 0 объявлений → нет mark_deleted().
        
        Проверяем что при пустом списке mark_deleted не вызывается.
        """
        service = ListingService(db_mock)

        stats = await service.upsert_listings([], "minsk", mark_deleted_externally=False)

        assert stats["processed"] == 0
        # mark_deleted не должен вызываться при пустом списке

    async def test_scenario_normal_scan_works(self, db_mock):
        """
        Сценарий: нормальное сканирование → работает корректно.
        
        Проверяем полный цикл: upsert + kufar_ids возвращаются.
        """
        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 1",
                "rooms": 2,
                "area": 50.0,
                "floor": 3,
                "category": "apartments",
            },
        ]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        stats = await service.upsert_listings_transaction(listings_data, "minsk")

        assert stats["success"] is True
        assert stats["processed"] == 1
        assert "kufar_ids" in stats
        assert len(stats["kufar_ids"]) == 1


@pytest.mark.asyncio
class TestListingServiceNoCommit:
    """Тесты для _no_commit версий методов."""

    @pytest.fixture
    def db_mock(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        db.rollback = AsyncMock()
        return db

    async def test_upsert_listings_no_commit_does_not_commit(self, db_mock):
        """Проверка что upsert_listings_no_commit() не делает commit."""
        from app.services.listing_service import ListingService

        service = ListingService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 1",
                "rooms": 2,
                "area": 50.0,
                "floor": 3,
                "category": "apartments",
            },
        ]

        # Mock для get_by_kufar_id - новые объявления
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        # Вызываем _no_commit версию
        stats = await service.upsert_listings_no_commit(listings_data, "minsk", db_mock)

        assert stats["processed"] == 1
        assert stats["created"] == 1
        # Проверка что commit НЕ был вызван внутри метода
        db_mock.commit.assert_not_called()

    async def test_mark_deleted_no_commit_does_not_commit(self, db_mock):
        """Проверка что mark_deleted_no_commit() не делает commit."""
        from app.services.listing_service import ListingService
        from app.models.listing import ListingStatus

        service = ListingService(db_mock)

        # Mock для select - возвращаем список объявлений для удаления
        mock_listing = MagicMock()
        mock_listing.status = ListingStatus.active
        mock_listing.deleted_at = None
        mock_listing.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_listing]
        db_mock.execute.return_value = mock_result

        active_ids = {"active_1", "active_2"}
        
        # Вызываем _no_commit версию
        count = await service.mark_deleted_no_commit(active_ids, "minsk", db_mock)

        assert count == 1
        assert mock_listing.status == ListingStatus.deleted  # Статус изменён на deleted
        # Проверка что commit НЕ был вызван внутри метода
        db_mock.commit.assert_not_called()

    async def test_update_stats_no_commit_does_not_commit(self, db_mock):
        """Проверка что update_stats_no_commit() не делает commit."""
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

        # Вызываем _no_commit версию
        result = await service.update_stats_no_commit("minsk", 550, db_mock)

        assert result is not None
        # Проверка что commit НЕ был вызван внутри метода
        db_mock.commit.assert_not_called()

    async def test_single_transaction_upsert_mark_deleted_update_stats(self, db_mock):
        """Проверка единой транзакции: ошибка в update_stats → откат upsert и mark_deleted."""
        from app.services.listing_service import ListingService
        from app.services.scan_stats_service import ScanStatsService
        from sqlalchemy.exc import SQLAlchemyError

        listing_service = ListingService(db_mock)
        scan_stats_service = ScanStatsService(db_mock)

        listings_data = [
            {
                "kufar_id": "test_1",
                "url": "https://re.kufar.by/vi/1",
                "title": "Test 1",
                "price": 100000,
                "price_usd": 35000,
                "currency": "BYN",
                "city": "minsk",
                "address": "Street 1",
                "rooms": 2,
                "area": 50.0,
                "floor": 3,
                "category": "apartments",
            },
        ]

        # Mock для get_by_kufar_id - новые объявления
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db_mock.execute.return_value = mock_result

        async def mock_refresh(obj):
            obj.id = uuid4()

        db_mock.refresh.side_effect = mock_refresh

        # Mock для update_stats_no_commit который выбрасывает ошибку
        async def mock_update_stats_error(city, count, session):
            raise SQLAlchemyError("Simulated database error")

        scan_stats_service.update_stats_no_commit = mock_update_stats_error

        # Симуляция единой транзакции
        try:
            # Upsert
            stats = await listing_service.upsert_listings_no_commit(
                listings_data, "minsk", db_mock
            )
            
            # Mark deleted
            kufar_ids = stats.get("kufar_ids", set())
            await listing_service.mark_deleted_no_commit(kufar_ids, "minsk", db_mock)
            
            # Update stats (ошибка здесь)
            await scan_stats_service.update_stats_no_commit("minsk", 1, db_mock)
            
            # Commit (не будет вызван из-за ошибки)
            await db_mock.commit()
        except SQLAlchemyError:
            # Откат при ошибке
            await db_mock.rollback()

        # Проверка что rollback был вызван
        db_mock.rollback.assert_called_once()
        # Проверка что commit НЕ был вызван (из-за ошибки)
        db_mock.commit.assert_not_called()
