"""
Тесты для ListingService
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select

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
