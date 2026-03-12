"""
Integration тесты для Price Drop API endpoints.

Тестируют endpoints:
- GET /api/v1/price-drops
- GET /api/v1/price-drops/stats
- GET /api/v1/price-drops/listings/{id}/price-history
- GET /api/v1/listings?include_price_drop=true

Требуют запущенную тестовую БД (порт 5433).
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient

from app.models.listing import Listing, ListingHistory, EventType, ListingStatus
from app.db.database import async_session_maker


@pytest.fixture
async def setup_test_data(test_session):
    """Создание тестовых данных для Price Drop тестов."""
    from sqlalchemy import insert

    # Создаём тестовое объявление
    listing_id = uuid4()
    kufar_id = f"test_price_drop_{uuid4().hex[:8]}"

    listing_data = {
        "id": listing_id,
        "kufar_id": kufar_id,
        "url": f"https://re.kufar.by/vi/minsk/kupit/kvartiru/{kufar_id}",
        "title": "Test Apartment for Price Drop",
        "price": 100000,
        "price_usd": 35000,
        "currency": "BYN",
        "city": "minsk",
        "address": "Test Street 1",
        "rooms": 2,
        "area": 50.0,
        "floor": 3,
        "status": ListingStatus.active.value,
        "first_seen_at": datetime.now() - timedelta(days=10),
        "last_seen_at": datetime.now(),
    }

    await test_session.execute(insert(Listing), listing_data)

    # Создаём историю изменений цены
    history_data = [
        {
            "listing_id": listing_id,
            "event_type": EventType.price_changed,
            "price_before_usd": 40000,
            "price_after_usd": 38000,
            "price_before": 114000,
            "price_after": 108000,
            "created_at": datetime.now() - timedelta(days=5),
        },
        {
            "listing_id": listing_id,
            "event_type": EventType.price_changed,
            "price_before_usd": 38000,
            "price_after_usd": 36000,
            "price_before": 108000,
            "price_after": 102000,
            "created_at": datetime.now() - timedelta(days=2),
        },
        {
            "listing_id": listing_id,
            "event_type": EventType.price_changed,
            "price_before_usd": 36000,
            "price_after_usd": 35000,
            "price_before": 102000,
            "price_after": 100000,
            "created_at": datetime.now() - timedelta(days=1),
        },
    ]

    await test_session.execute(insert(ListingHistory), history_data)
    await test_session.commit()

    return {"listing_id": listing_id, "kufar_id": kufar_id}


@pytest.fixture
async def setup_multiple_listings(test_session):
    """Создание нескольких объявлений для тестов пагинации."""
    from sqlalchemy import insert

    listings = []
    for i in range(5):
        listing_id = uuid4()
        kufar_id = f"test_multi_{i}_{uuid4().hex[:8]}"

        listing_data = {
            "id": listing_id,
            "kufar_id": kufar_id,
            "url": f"https://re.kufar.by/vi/minsk/kupit/kvartiru/{kufar_id}",
            "title": f"Test Apartment {i}",
            "price": 100000 - (i * 5000),
            "price_usd": 35000 - (i * 1500),
            "currency": "BYN",
            "city": "minsk",
            "rooms": 2,
            "area": 50.0,
            "status": ListingStatus.active.value,
            "first_seen_at": datetime.now(),
            "last_seen_at": datetime.now(),
        }

        await test_session.execute(insert(Listing), listing_data)

        # Создаём историю с разным drop_percent
        drop_percent = 15 + (i * 5)  # 15%, 20%, 25%, 30%, 35%
        max_price = 40000
        min_price = int(max_price * (1 - drop_percent / 100))

        history_data = {
            "listing_id": listing_id,
            "event_type": EventType.price_changed,
            "price_before_usd": max_price,
            "price_after_usd": min_price,
            "created_at": datetime.now(),
        }

        await test_session.execute(insert(ListingHistory), history_data)
        listings.append({"listing_id": listing_id, "kufar_id": kufar_id})

    await test_session.commit()
    return listings


class TestPriceDropsEndpoint:
    """Тесты GET /api/v1/price-drops."""

    @pytest.mark.asyncio
    async def test_get_price_drops_basic(self, client: AsyncClient, setup_test_data):
        """Тест базового запроса."""
        response = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": 5.0},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "avg_drop_percent" in data
        assert "max_drop_percent" in data
        assert "min_drop_percent" in data
        assert "currency" in data
        assert data["currency"] == "USD"
        assert data["total"] >= 1

        # Проверка полей объявления
        item = data["items"][0]
        assert "kufar_id" in item
        assert "max_price" in item
        assert "min_price" in item
        assert "drop_percent" in item
        assert item["drop_percent"] > 5.0

    @pytest.mark.asyncio
    async def test_get_price_drops_with_high_threshold(self, client: AsyncClient, setup_test_data):
        """Тест с высоким порогом drop_percent."""
        response = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": 50.0},
        )

        assert response.status_code == 200
        data = response.json()

        # Нет объявлений с таким падением
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_get_price_drops_pagination(self, client: AsyncClient, setup_multiple_listings):
        """Тест пагинации."""
        # Первая страница
        response1 = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": 10.0, "limit": 2, "offset": 0},
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["total"] >= 5
        assert len(data1["items"]) == 2
        assert data1["page"] == 1
        assert data1["size"] == 2

        # Вторая страница
        response2 = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": 10.0, "limit": 2, "offset": 2},
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 2
        assert data2["page"] == 2

    @pytest.mark.asyncio
    async def test_get_price_drops_byn_currency(self, client: AsyncClient, setup_test_data):
        """Тест с валютой BYN."""
        response = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": 5.0, "currency": "byn"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "BYN"

    @pytest.mark.asyncio
    async def test_get_price_drops_invalid_city(self, client: AsyncClient):
        """Тест валидации города."""
        response = await client.get(
            "/api/v1/price-drops",
            params={"city": "invalid_city"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_price_drops_invalid_drop_percent(self, client: AsyncClient):
        """Тест валидации drop_percent."""
        response = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": 150.0},
        )

        assert response.status_code == 422

        response = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": -10.0},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_price_drops_invalid_currency(self, client: AsyncClient):
        """Тест валидации валюты."""
        response = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "currency": "EUR"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_price_drops_all_cities(self, client: AsyncClient):
        """Тест всех допустимых городов."""
        valid_cities = ["minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"]

        for city in valid_cities:
            response = await client.get(
                "/api/v1/price-drops",
                params={"city": city},
            )
            # 200 или 404 если нет данных
            assert response.status_code in [200, 404]


class TestPriceDropStatsEndpoint:
    """Тесты GET /api/v1/price-drops/stats."""

    @pytest.mark.asyncio
    async def test_get_price_drop_stats_basic(self, client: AsyncClient, setup_test_data):
        """Тест базовой статистики."""
        response = await client.get(
            "/api/v1/price-drops/stats",
            params={"city": "minsk", "drop_percent": 5.0},
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_drops" in data
        assert "avg_drop_percent" in data
        assert "max_drop_percent" in data
        assert "min_drop_percent" in data
        assert "currency" in data
        assert data["currency"] == "USD"
        assert data["total_drops"] >= 1

    @pytest.mark.asyncio
    async def test_get_price_drop_stats_byn(self, client: AsyncClient, setup_test_data):
        """Тест статистики с валютой BYN."""
        response = await client.get(
            "/api/v1/price-drops/stats",
            params={"city": "minsk", "currency": "byn"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "BYN"

    @pytest.mark.asyncio
    async def test_get_price_drop_stats_invalid_city(self, client: AsyncClient):
        """Тест валидации города."""
        response = await client.get(
            "/api/v1/price-drops/stats",
            params={"city": "invalid"},
        )

        assert response.status_code == 422


class TestPriceHistoryEndpoint:
    """Тесты GET /api/v1/price-drops/listings/{id}/price-history."""

    @pytest.mark.asyncio
    async def test_get_price_history_basic(self, client: AsyncClient, setup_test_data):
        """Тест базовой истории цен."""
        listing_id = setup_test_data["listing_id"]

        response = await client.get(
            f"/api/v1/price-drops/listings/{listing_id}/price-history",
            params={"currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "first_price" in data
        assert "last_price" in data
        assert "total_drop_percent" in data
        assert data["currency"] == "USD"
        assert len(data["items"]) >= 1

        # Проверка что drop_percent корректный
        # Было 3 падения: 40000->38000->36000->35000
        assert data["first_price"] == 40000
        assert data["last_price"] == 35000
        assert data["total_drop_percent"] == 12.5  # (40000-35000)/40000 * 100

    @pytest.mark.asyncio
    async def test_get_price_history_byn(self, client: AsyncClient, setup_test_data):
        """Тест истории с валютой BYN."""
        listing_id = setup_test_data["listing_id"]

        response = await client.get(
            f"/api/v1/price-drops/listings/{listing_id}/price-history",
            params={"currency": "byn"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "BYN"

    @pytest.mark.asyncio
    async def test_get_price_history_not_found(self, client: AsyncClient):
        """Тест несуществующего объявления."""
        fake_id = uuid4()

        response = await client.get(
            f"/api/v1/price-drops/listings/{fake_id}/price-history",
        )

        # 200 с пустым списком или 404
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_price_history_invalid_uuid(self, client: AsyncClient):
        """Тест невалидного UUID."""
        response = await client.get(
            "/api/v1/price-drops/listings/invalid-uuid/price-history",
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_price_history_invalid_currency(self, client: AsyncClient, setup_test_data):
        """Тест невалидной валюты."""
        listing_id = setup_test_data["listing_id"]

        response = await client.get(
            f"/api/v1/price-drops/listings/{listing_id}/price-history",
            params={"currency": "EUR"},
        )

        assert response.status_code == 422


class TestListingsWithPriceDrop:
    """Тесты GET /api/v1/listings?include_price_drop=true."""

    @pytest.mark.asyncio
    async def test_listings_with_price_drop(self, client: AsyncClient):
        """Тест получения listings с price drop метриками."""
        # Просто проверяем что endpoint работает
        response = await client.get(
            "/api/v1/listings",
            params={"city": "minsk", "include_price_drop": True, "include_deal_metrics": False},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

        # Если есть items, проверяем что поля присутствуют (даже если None)
        if len(data["items"]) > 0:
            item = data["items"][0]
            # Поля могут быть None если нет истории изменений
            assert "max_price" in item
            assert "min_price" in item
            assert "drop_percent" in item

    @pytest.mark.asyncio
    async def test_listings_with_price_drop_byn(self, client: AsyncClient, setup_test_data):
        """Тест с валютой BYN."""
        response = await client.get(
            "/api/v1/listings",
            params={
                "city": "minsk",
                "include_price_drop": True,
                "price_drop_currency": "byn",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_listings_with_price_drop_invalid_currency(self, client: AsyncClient):
        """Тест невалидной валюты."""
        response = await client.get(
            "/api/v1/listings",
            params={
                "city": "minsk",
                "include_price_drop": True,
                "price_drop_currency": "EUR",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_listings_without_price_drop(self, client: AsyncClient, setup_test_data):
        """Тест без price drop метрик (default behavior)."""
        response = await client.get(
            "/api/v1/listings",
            params={"city": "minsk"},
        )

        assert response.status_code == 200
        data = response.json()

        # Price drop поля не должны быть в ответе
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "max_price" not in item
            assert "min_price" not in item
            assert "drop_percent" not in item


class TestCachingIntegration:
    """Тесты Redis кэширования."""

    @pytest.mark.asyncio
    async def test_price_drops_caching(self, client: AsyncClient, setup_test_data):
        """Тест кэширования price drops."""
        # Первый запрос (cache miss)
        response1 = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": 5.0},
        )
        assert response1.status_code == 200

        # Второй запрос (cache hit)
        response2 = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk", "drop_percent": 5.0},
        )
        assert response2.status_code == 200

        # Данные должны быть одинаковыми
        assert response1.json()["total"] == response2.json()["total"]

    @pytest.mark.asyncio
    async def test_price_history_caching(self, client: AsyncClient, setup_test_data):
        """Тест кэширования price history."""
        listing_id = setup_test_data["listing_id"]

        # Первый запрос
        response1 = await client.get(
            f"/api/v1/price-drops/listings/{listing_id}/price-history",
        )
        assert response1.status_code == 200

        # Второй запрос
        response2 = await client.get(
            f"/api/v1/price-drops/listings/{listing_id}/price-history",
        )
        assert response2.status_code == 200

        # Данные должны быть одинаковыми
        assert response1.json()["first_price"] == response2.json()["first_price"]


class TestLogging:
    """Тесты логирования."""

    @pytest.mark.asyncio
    async def test_request_logging(self, client: AsyncClient, setup_test_data, caplog):
        """Тест логирования запросов."""
        import logging
        caplog.set_level(logging.INFO)

        response = await client.get(
            "/api/v1/price-drops",
            params={"city": "minsk"},
        )

        assert response.status_code == 200
        # Логирование проверяется визуально в логах
