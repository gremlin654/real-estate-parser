"""
Тесты для History API endpoints
"""
import pytest
import random
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime

from app.models.listing import Listing, ListingStatus, ListingHistory, EventType


@pytest.mark.asyncio
class TestGetHistory:
    """Тесты для получения истории объявлений."""

    async def test_get_history_empty(self, client: AsyncClient):
        """Проверка получения пустой истории для несуществующего объявления."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/history/{fake_id}")

        # API returns 404 for non-existent listing
        assert response.status_code == 404

    async def test_get_history_with_data(self, client: AsyncClient, test_session, create_test_listing):
        """Проверка получения истории с данными."""
        # Уникальный префикс для этого теста
        prefix = f"hist_{random.randint(1000, 9999)}"

        # Устанавливаем price_usd для тестового объявления
        create_test_listing.price_usd = 42500
        await test_session.commit()

        # Создаём записи истории
        for event_type in [EventType.created, EventType.price_changed, EventType.edited]:
            history = ListingHistory(
                id=uuid4(),
                listing_id=create_test_listing.id,
                event_type=event_type,
                price_before=90000 if event_type == EventType.price_changed else None,
                price_after=100000 if event_type == EventType.price_changed else None,
                price_before_usd=40000 if event_type == EventType.price_changed else None,
                price_after_usd=42500 if event_type == EventType.price_changed else None,
                created_at=datetime.now().replace(tzinfo=None),
            )
            test_session.add(history)

        await test_session.commit()

        listing_id = str(create_test_listing.id)
        response = await client.get(f"/api/v1/history/{listing_id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Проверяем что новые поля USD присутствуют в ответе
        price_changed_entry = next((h for h in data if h['event_type'] == 'price_changed'), None)
        if price_changed_entry:
            assert 'price_before_usd' in price_changed_entry
            assert 'price_after_usd' in price_changed_entry
            assert price_changed_entry['price_before_usd'] == 40000
            assert price_changed_entry['price_after_usd'] == 42500

    async def test_get_history_invalid_uuid(self, client: AsyncClient):
        """Проверка обработки невалидного UUID."""
        response = await client.get("/api/v1/history/invalid-uuid")

        # API returns 400 for invalid UUID format
        assert response.status_code == 400


@pytest.mark.asyncio
class TestListingHistoryModel:
    """Тесты для модели истории объявлений."""

    async def test_create_history_entry(self, test_session, create_test_listing):
        """Проверка создания записи истории."""
        history = ListingHistory(
            id=uuid4(),
            listing_id=create_test_listing.id,
            event_type=EventType.price_changed,
            price_before=90000,
            price_after=100000,
            price_before_usd=40000,
            price_after_usd=42500,
            created_at=datetime.now().replace(tzinfo=None),
        )

        test_session.add(history)
        await test_session.commit()

        assert history.id is not None
        assert history.event_type == EventType.price_changed
        assert history.price_before == 90000
        assert history.price_after == 100000
        assert history.price_before_usd == 40000
        assert history.price_after_usd == 42500

    async def test_history_event_types(self, test_session, create_test_listing):
        """Проверка всех типов событий."""
        event_types = [
            EventType.created,
            EventType.price_changed,
            EventType.edited,
            EventType.deleted,
            EventType.restored,
        ]

        for event_type in event_types:
            history = ListingHistory(
                id=uuid4(),
                listing_id=create_test_listing.id,
                event_type=event_type,
                created_at=datetime.now().replace(tzinfo=None),
            )
            test_session.add(history)

        await test_session.commit()

        # Проверяем, что все события сохранены
        from sqlalchemy import select
        result = await test_session.execute(
            select(ListingHistory).where(ListingHistory.listing_id == create_test_listing.id)
        )
        histories = result.scalars().all()
        assert len(histories) == len(event_types)
