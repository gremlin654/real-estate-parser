"""
Тесты для ListingService
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import select

from app.services.listing_service import ListingService, ListingDiff, get_now, MINSK_OFFSET
from app.models.listing import Listing, ListingStatus, EventType, ListingHistory


@pytest.mark.asyncio
class TestListingDiff:
    """Тесты для класса ListingDiff."""

    def test_listing_diff_default(self):
        """Проверка создания ListingDiff с значениями по умолчанию."""
        diff = ListingDiff()
        
        assert diff.price_changed is False
        assert diff.price_before is None
        assert diff.price_after is None
        assert diff.fields_changed is None

    def test_listing_diff_with_values(self):
        """Проверка создания ListingDiff с значениями."""
        diff = ListingDiff(
            price_changed=True,
            price_before=100000,
            price_after=120000,
            fields_changed={"title": ["Old", "New"]}
        )
        
        assert diff.price_changed is True
        assert diff.price_before == 100000
        assert diff.price_after == 120000
        assert diff.fields_changed == {"title": ["Old", "New"]}


class TestGetNow:
    """Тесты для функции get_now."""

    def test_get_now_returns_datetime(self):
        """Проверка что get_now возвращает datetime."""
        result = get_now()
        
        assert isinstance(result, datetime)
        assert result.tzinfo is None  # Без timezone info для совместимости с БД

    def test_get_now_utc_based(self):
        """Проверка что get_now основано на UTC времени."""
        result = get_now()
        now_utc = datetime.now(timezone.utc)
        
        # Разница должна быть менее 1 секунды
        diff = abs((now_utc.replace(tzinfo=None) - result).total_seconds())
        assert diff < 1


@pytest.mark.asyncio
class TestListingService:
    """Тесты для ListingService."""

    @pytest.fixture
    def mock_db(self):
        """Создание мок базы данных."""
        db = MagicMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def listing_service(self, mock_db):
        """Создание сервиса listings."""
        return ListingService(mock_db)

    async def test_compute_diff_no_changes(self, listing_service):
        """Проверка вычисления diff без изменений."""
        existing = MagicMock()
        existing.price = 100000
        existing.title = "Test"
        existing.address = "Street 1"
        existing.rooms = 2
        existing.area = 50.5
        existing.floor = 3
        existing.category = "apartments"
        existing.description = "Desc"
        existing.district = "Central"
        existing.metro = "Nemiga"
        existing.house_year = 2020
        existing.total_floors = 9

        new_data = {
            "price": 100000,
            "title": "Test",
            "address": "Street 1",
            "rooms": 2,
            "area": 50.5,
            "floor": 3,
            "category": "apartments",
            "description": "Desc",
            "district": "Central",
            "metro": "Nemiga",
            "house_year": 2020,
            "total_floors": 9,
        }

        diff = listing_service._compute_diff(existing, new_data)

        assert diff.price_changed is False
        assert diff.price_before is None
        assert diff.price_after is None
        assert diff.fields_changed is None

    async def test_compute_diff_price_changed(self, listing_service):
        """Проверка вычисления diff при изменении цены."""
        existing = MagicMock()
        existing.price = 100000
        existing.title = "Test"
        existing.address = "Street 1"
        existing.rooms = 2
        existing.area = 50.5
        existing.floor = 3
        existing.category = "apartments"
        existing.description = "Desc"
        existing.district = "Central"
        existing.metro = "Nemiga"
        existing.house_year = 2020
        existing.total_floors = 9

        new_data = {
            "price": 120000,  # Changed
            "title": "Test",
            "address": "Street 1",
            "rooms": 2,
            "area": 50.5,
            "floor": 3,
            "category": "apartments",
            "description": "Desc",
            "district": "Central",
            "metro": "Nemiga",
            "house_year": 2020,
            "total_floors": 9,
        }

        diff = listing_service._compute_diff(existing, new_data)

        assert diff.price_changed is True
        assert diff.price_before == 100000
        assert diff.price_after == 120000
        assert diff.fields_changed is None

    async def test_compute_diff_fields_changed(self, listing_service):
        """Проверка вычисления diff при изменении полей."""
        existing = MagicMock()
        existing.price = 100000
        existing.title = "Old Title"
        existing.address = "Street 1"
        existing.rooms = 2
        existing.area = 50.5
        existing.floor = 3
        existing.category = "apartments"
        existing.description = "Desc"
        existing.district = "Central"
        existing.metro = "Nemiga"
        existing.house_year = 2020
        existing.total_floors = 9

        new_data = {
            "price": 100000,
            "title": "New Title",  # Changed
            "address": "Street 2",  # Changed
            "rooms": 2,
            "area": 50.5,
            "floor": 3,
            "category": "apartments",
            "description": "Desc",
            "district": "Central",
            "metro": "Nemiga",
            "house_year": 2020,
            "total_floors": 9,
        }

        diff = listing_service._compute_diff(existing, new_data)

        assert diff.price_changed is False
        assert diff.fields_changed is not None
        assert "title" in diff.fields_changed
        assert "address" in diff.fields_changed

    async def test_compute_diff_multiple_fields_changed(self, listing_service):
        """Проверка вычисления diff при изменении нескольких полей."""
        existing = MagicMock()
        existing.price = 100000
        existing.title = "Test"
        existing.address = "Street 1"
        existing.rooms = 2
        existing.area = 50.5
        existing.floor = 3
        existing.category = "apartments"
        existing.description = "Old desc"
        existing.district = "Central"
        existing.metro = "Nemiga"
        existing.house_year = 2020
        existing.total_floors = 9

        new_data = {
            "price": 100000,
            "title": "Test",
            "address": "Street 1",
            "rooms": 3,  # Changed
            "area": 60.0,  # Changed
            "floor": 5,  # Changed
            "category": "apartments",
            "description": "New desc",  # Changed
            "district": "South",  # Changed
            "metro": "Petrovka",  # Changed
            "house_year": 2022,  # Changed
            "total_floors": 12,  # Changed
        }

        diff = listing_service._compute_diff(existing, new_data)

        assert diff.price_changed is False
        assert diff.fields_changed is not None
        assert len(diff.fields_changed) == 8  # rooms, area, floor, description, district, metro, house_year, total_floors

    async def test_add_event(self, listing_service, mock_db):
        """Проверка добавления события истории."""
        listing_id = uuid4()
        event_type = EventType.price_changed
        price_before = 100000
        price_after = 120000
        snapshot = {"price": 120000}

        result = await listing_service._add_event(
            listing_id=listing_id,
            event_type=event_type,
            price_before=price_before,
            price_after=price_after,
            snapshot=snapshot,
        )

        assert result is not None
        assert mock_db.add.called
        added_event = mock_db.add.call_args[0][0]
        assert added_event.listing_id == listing_id
        assert added_event.event_type == event_type
        assert added_event.price_before == price_before
        assert added_event.price_after == price_after
        assert added_event.snapshot == snapshot


@pytest.mark.asyncio
class TestListingServiceUpsert:
    """Тесты для upsert_listing с использованием реальной БД."""

    async def test_create_new_listing(self, client, test_session):
        """Проверка создания нового объявления через сервис."""
        from app.services.listing_service import ListingService
        from app.schemas.listing import ListingCreate

        service = ListingService(test_session)

        listing_data = {
            "kufar_id": f"test_new_{uuid4().hex[:8]}",
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

        result = await service.upsert_listing(listing_data)

        assert result is not None
        assert result.kufar_id == listing_data["kufar_id"]
        assert result.title == listing_data["title"]
        assert result.price == listing_data["price"]
        assert result.price_usd == listing_data["price_usd"]
        assert result.status == ListingStatus.new

    async def test_update_listing_price_usd(self, client, test_session, create_test_listing):
        """Проверка обновления объявления при изменении цены USD."""
        from app.services.listing_service import ListingService

        service = ListingService(test_session)
        listing = create_test_listing

        # Обновляем цену USD
        updated_data = {
            "kufar_id": listing.kufar_id,
            "url": listing.url,
            "title": listing.title,
            "price": listing.price,
            "price_usd": 40000,  # Changed from 35000
            "currency": "BYN",
            "city": listing.city,
            "address": listing.address,
            "rooms": listing.rooms,
            "area": listing.area,
            "floor": listing.floor,
            "total_floors": listing.total_floors,
            "category": listing.category,
        }

        result = await service.upsert_listing(updated_data)

        assert result is not None
        assert result.price_usd == 40000
        assert result.status == ListingStatus.updated

    async def test_update_listing_price_byn_only(self, client, test_session, create_test_listing):
        """Проверка обновления объявления при изменении только цены BYN."""
        from app.services.listing_service import ListingService

        service = ListingService(test_session)
        listing = create_test_listing

        # Сбрасываем статус в active
        listing.status = ListingStatus.active
        await test_session.commit()

        # Обновляем только цену BYN
        updated_data = {
            "kufar_id": listing.kufar_id,
            "url": listing.url,
            "title": listing.title,
            "price": 110000,  # Changed from 100000
            "price_usd": listing.price_usd,  # Same
            "currency": "BYN",
            "city": listing.city,
            "address": listing.address,
            "rooms": listing.rooms,
            "area": listing.area,
            "floor": listing.floor,
            "total_floors": listing.total_floors,
            "category": listing.category,
        }

        result = await service.upsert_listing(updated_data)

        assert result is not None
        assert result.price == 110000
        assert result.status == ListingStatus.price_changed_byn

    async def test_update_listing_no_changes(self, client, test_session, create_test_listing):
        """Проверка обновления без изменений."""
        from app.services.listing_service import ListingService

        service = ListingService(test_session)
        listing = create_test_listing

        # Сбрасываем статус в active
        listing.status = ListingStatus.active
        await test_session.commit()

        # Те же данные
        updated_data = {
            "kufar_id": listing.kufar_id,
            "url": listing.url,
            "title": listing.title,
            "price": listing.price,
            "price_usd": listing.price_usd,
            "currency": "BYN",
            "city": listing.city,
            "address": listing.address,
            "rooms": listing.rooms,
            "area": listing.area,
            "floor": listing.floor,
            "total_floors": listing.total_floors,
            "category": listing.category,
        }

        result = await service.upsert_listing(updated_data)

        assert result is not None
        assert result.status == ListingStatus.active  # Status unchanged

    async def test_restore_deleted_listing(self, client, test_session, create_test_listing):
        """Проверка восстановления удалённого объявления."""
        from app.services.listing_service import ListingService

        service = ListingService(test_session)
        listing = create_test_listing

        # Устанавливаем статус deleted
        listing.status = ListingStatus.deleted
        await test_session.commit()

        # Обновляем данные (объявление найдено снова)
        updated_data = {
            "kufar_id": listing.kufar_id,
            "url": listing.url,
            "title": listing.title,
            "price": listing.price,
            "price_usd": listing.price_usd,
            "currency": "BYN",
            "city": listing.city,
            "address": listing.address,
            "rooms": listing.rooms,
            "area": listing.area,
            "floor": listing.floor,
            "total_floors": listing.total_floors,
            "category": listing.category,
        }

        result = await service.upsert_listing(updated_data)

        assert result is not None
        assert result.status == ListingStatus.active


@pytest.mark.asyncio
class TestListingServiceMarkDeleted:
    """Тесты для методов mark_deleted."""

    async def test_mark_deleted(self, client, test_session):
        """Проверка маркировки объявлений как удалённых."""
        from app.services.listing_service import ListingService
        from uuid import uuid4

        service = ListingService(test_session)

        # Создаём активное объявление
        listing = Listing(
            id=uuid4(),
            kufar_id=f"test_del_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Test",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        test_session.add(listing)
        await test_session.commit()

        # Маркируем как удалённое (пустой set = все активные удаляем)
        count = await service.mark_deleted(set())

        assert count == 1
        assert listing.status == ListingStatus.deleted
        assert listing.deleted_at is not None

    async def test_mark_deleted_with_active_ids(self, client, test_session):
        """Проверка маркировки с указанием активных ID."""
        from app.services.listing_service import ListingService
        from uuid import uuid4

        service = ListingService(test_session)

        # Создаём два активных объявления
        listing1 = Listing(
            id=uuid4(),
            kufar_id=f"test_keep_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Test 1",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        listing2 = Listing(
            id=uuid4(),
            kufar_id=f"test_del_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/222",
            title="Test 2",
            price=120000,
            price_usd=40000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        test_session.add(listing1)
        test_session.add(listing2)
        await test_session.commit()

        # Оставляем только listing1
        active_ids = {listing1.kufar_id}
        count = await service.mark_deleted(active_ids)

        assert count == 1
        assert listing1.status == ListingStatus.active  # Осталось
        assert listing2.status == ListingStatus.deleted  # Удалено

    async def test_mark_deleted_for_city(self, client, test_session):
        """Проверка маркировки удалённых для конкретного города."""
        from app.services.listing_service import ListingService
        from uuid import uuid4

        service = ListingService(test_session)

        # Создаём объявления в разных городах
        listing_minsk = Listing(
            id=uuid4(),
            kufar_id=f"test_minsk_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Minsk",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        listing_brest = Listing(
            id=uuid4(),
            kufar_id=f"test_brest_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/222",
            title="Brest",
            price=120000,
            price_usd=40000,
            currency="BYN",
            city="brest",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        test_session.add(listing_minsk)
        test_session.add(listing_brest)
        await test_session.commit()

        # Маркируем удалёнными для Минска (пустой set)
        count = await service.mark_deleted_for_city(set(), "minsk")

        assert count == 1
        assert listing_minsk.status == ListingStatus.deleted
        assert listing_brest.status == ListingStatus.active  # Другой город

    async def test_mark_active_deleted_for_city(self, client, test_session):
        """Проверка маркировки активных и новых для города."""
        from app.services.listing_service import ListingService
        from uuid import uuid4

        service = ListingService(test_session)

        # Создаём объявления с разными статусами
        listing_active = Listing(
            id=uuid4(),
            kufar_id=f"test_act_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Active",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        listing_new = Listing(
            id=uuid4(),
            kufar_id=f"test_new_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/222",
            title="New",
            price=120000,
            price_usd=40000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.new,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        listing_deleted = Listing(
            id=uuid4(),
            kufar_id=f"test_del_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/333",
            title="Deleted",
            price=130000,
            price_usd=42000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.deleted,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        test_session.add(listing_active)
        test_session.add(listing_new)
        test_session.add(listing_deleted)
        await test_session.commit()

        # Маркируем активные и новые как удалённые
        count = await service.mark_active_deleted_for_city("minsk")

        assert count == 2  # active и new
        assert listing_active.status == ListingStatus.deleted
        assert listing_new.status == ListingStatus.deleted
        assert listing_deleted.status == ListingStatus.deleted  # Уже было

    async def test_mark_all_deleted_for_city(self, client, test_session):
        """Проверка маркировки всех активных для города."""
        from app.services.listing_service import ListingService
        from uuid import uuid4

        service = ListingService(test_session)

        # Создаём объявления
        listing = Listing(
            id=uuid4(),
            kufar_id=f"test_all_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Test",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="gomel",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        test_session.add(listing)
        await test_session.commit()

        # Маркируем все как удалённые
        count = await service.mark_all_deleted_for_city("gomel")

        assert count == 1
        assert listing.status == ListingStatus.deleted


@pytest.mark.asyncio
class TestListingServiceGetIds:
    """Тесты для методов получения ID объявлений."""

    async def test_get_active_kufar_ids_by_city(self, test_session):
        """Проверка получения активных ID по городу."""
        from app.services.listing_service import ListingService
        from uuid import uuid4

        service = ListingService(test_session)

        # Создаём объявления
        listing1 = Listing(
            id=uuid4(),
            kufar_id=f"test_act1_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Test 1",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        listing2 = Listing(
            id=uuid4(),
            kufar_id=f"test_act2_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/222",
            title="Test 2",
            price=120000,
            price_usd=40000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        listing3 = Listing(
            id=uuid4(),
            kufar_id=f"test_del_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/333",
            title="Test 3",
            price=130000,
            price_usd=42000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.deleted,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        test_session.add(listing1)
        test_session.add(listing2)
        test_session.add(listing3)
        await test_session.commit()

        # Получаем активные ID для Минска
        ids = await service.get_active_kufar_ids_by_city("minsk")

        assert len(ids) == 2
        assert listing1.kufar_id in ids
        assert listing2.kufar_id in ids
        assert listing3.kufar_id not in ids  # Deleted

    async def test_get_all_kufar_ids_by_city(self, test_session):
        """Проверка получения всех ID по городу."""
        from app.services.listing_service import ListingService
        from uuid import uuid4

        service = ListingService(test_session)

        # Создаём объявления с разными статусами
        listing1 = Listing(
            id=uuid4(),
            kufar_id=f"test_all1_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Test 1",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="brest",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        listing2 = Listing(
            id=uuid4(),
            kufar_id=f"test_all2_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/222",
            title="Test 2",
            price=120000,
            price_usd=40000,
            currency="BYN",
            city="brest",
            status=ListingStatus.deleted,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        test_session.add(listing1)
        test_session.add(listing2)
        await test_session.commit()

        # Получаем все ID для Бреста
        ids = await service.get_all_kufar_ids_by_city("brest")

        assert len(ids) == 2
        assert listing1.kufar_id in ids
        assert listing2.kufar_id in ids

    async def test_get_active_kufar_ids(self, test_session):
        """Проверка получения всех активных ID."""
        from app.services.listing_service import ListingService
        from uuid import uuid4

        service = ListingService(test_session)

        # Создаём объявления в разных городах
        listing1 = Listing(
            id=uuid4(),
            kufar_id=f"test_glob1_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Test 1",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        listing2 = Listing(
            id=uuid4(),
            kufar_id=f"test_glob2_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/222",
            title="Test 2",
            price=120000,
            price_usd=40000,
            currency="BYN",
            city="brest",
            status=ListingStatus.active,
            first_seen_at=datetime.now().replace(tzinfo=None),
            last_seen_at=datetime.now().replace(tzinfo=None),
        )
        test_session.add(listing1)
        test_session.add(listing2)
        await test_session.commit()

        # Получаем все активные ID
        ids = await service.get_active_kufar_ids()

        assert len(ids) == 2
        assert listing1.kufar_id in ids
        assert listing2.kufar_id in ids

    async def test_archive_old_deleted_listings(self, test_session):
        """Проверка архивации старых удаленных объявлений."""
        from app.services.listing_service import ListingService
        from uuid import uuid4
        from datetime import timedelta

        service = ListingService(test_session)

        now = datetime.now().replace(tzinfo=None)

        # Создаём удаленные объявления с разными датами
        listing_recent = Listing(
            id=uuid4(),
            kufar_id=f"test_recent_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/111",
            title="Test Recent",
            price=100000,
            price_usd=35000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.deleted,
            deleted_at=now - timedelta(days=5),  # 5 дней назад - не архивируется
            first_seen_at=now - timedelta(days=10),
            last_seen_at=now,
        )
        listing_old = Listing(
            id=uuid4(),
            kufar_id=f"test_old_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/222",
            title="Test Old",
            price=120000,
            price_usd=40000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.deleted,
            deleted_at=now - timedelta(days=45),  # 45 дней назад - архивируется
            first_seen_at=now - timedelta(days=50),
            last_seen_at=now - timedelta(days=45),
        )
        listing_very_old = Listing(
            id=uuid4(),
            kufar_id=f"test_very_old_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/333",
            title="Test Very Old",
            price=130000,
            price_usd=42000,
            currency="BYN",
            city="brest",
            status=ListingStatus.deleted,
            deleted_at=now - timedelta(days=60),  # 60 дней назад - архивируется
            first_seen_at=now - timedelta(days=70),
            last_seen_at=now - timedelta(days=60),
        )
        # Активное объявление - не должно затронуть
        listing_active = Listing(
            id=uuid4(),
            kufar_id=f"test_active_{uuid4().hex[:8]}",
            url="https://re.kufar.by/vi/444",
            title="Test Active",
            price=140000,
            price_usd=45000,
            currency="BYN",
            city="minsk",
            status=ListingStatus.active,
            first_seen_at=now - timedelta(days=100),
            last_seen_at=now,
        )

        test_session.add(listing_recent)
        test_session.add(listing_old)
        test_session.add(listing_very_old)
        test_session.add(listing_active)
        await test_session.commit()

        # Архивируем объявления старше 30 дней
        archived_count = await service.archive_old_deleted_listings(days_threshold=30)

        assert archived_count == 2  # old и very_old должны быть заархивированы

        # Проверяем статусы
        await test_session.refresh(listing_recent)
        await test_session.refresh(listing_old)
        await test_session.refresh(listing_very_old)
        await test_session.refresh(listing_active)

        assert listing_recent.status == ListingStatus.deleted  # Не архивировано
        assert listing_old.status == ListingStatus.archived  # Архивировано
        assert listing_very_old.status == ListingStatus.archived  # Архивировано
        assert listing_active.status == ListingStatus.active  # Не затронуто

        # Проверяем историю событий
        result = await test_session.execute(
            select(ListingHistory).where(
                ListingHistory.listing_id == listing_old.id,
                ListingHistory.event_type == EventType.edited
            )
        )
        history = result.scalars().first()
        assert history is not None
        assert history.changed_fields is not None
        assert "status" in history.changed_fields
