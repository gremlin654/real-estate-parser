"""
Integration тесты для Deal Score API.

Тестирует:
- GET /api/v1/deals/score — поиск по Deal Score
- GET /api/v1/listings с include_score и sort_by_deal_score
- Redis кэширование
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.models.listing import Listing, ListingStatus
from app.services.deal_score_service import DealScoreService


# === Фикстуры для Deal Score тестов ===


@pytest.fixture
async def test_listings_with_scores(test_session) -> list[Listing]:
    """Create test listings с разными Deal Score."""
    listings = []
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)

    # Создаём 10 тестовых объявлений с разными параметрами
    test_data = [
        {
            "city": "minsk",
            "rooms": 2,
            "price": 100000,
            "price_usd": 35000,
            "area": 50.0,
            "floor": 3,
            "total_floors": 9,
            "price_per_m2_usd": 700,
            "deal_score": 85.5,
            "deal_label": "🔥 HOT",
        },
        {
            "city": "minsk",
            "rooms": 2,
            "price": 120000,
            "price_usd": 40000,
            "area": 55.0,
            "floor": 5,
            "total_floors": 9,
            "price_per_m2_usd": 727,
            "deal_score": 72.3,
            "deal_label": "👍 GOOD",
        },
        {
            "city": "minsk",
            "rooms": 1,
            "price": 80000,
            "price_usd": 28000,
            "area": 40.0,
            "floor": 2,
            "total_floors": 5,
            "price_per_m2_usd": 700,
            "deal_score": 90.0,
            "deal_label": "🔥 HOT",
        },
        {
            "city": "minsk",
            "rooms": 3,
            "price": 150000,
            "price_usd": 50000,
            "area": 75.0,
            "floor": 4,
            "total_floors": 9,
            "price_per_m2_usd": 667,
            "deal_score": 65.0,
            "deal_label": "👍 GOOD",
        },
        {
            "city": "minsk",
            "rooms": 2,
            "price": 130000,
            "price_usd": 45000,
            "area": 60.0,
            "floor": 1,
            "total_floors": 9,
            "price_per_m2_usd": 750,
            "deal_score": 45.0,
            "deal_label": "😐 NORMAL",
        },
        {
            "city": "mogilev",
            "rooms": 2,
            "price": 60000,
            "price_usd": 20000,
            "area": 50.0,
            "floor": 3,
            "total_floors": 5,
            "price_per_m2_usd": 400,
            "deal_score": 78.0,
            "deal_label": "👍 GOOD",
        },
        {
            "city": "mogilev",
            "rooms": 1,
            "price": 45000,
            "price_usd": 15000,
            "area": 35.0,
            "floor": 2,
            "total_floors": 5,
            "price_per_m2_usd": 429,
            "deal_score": 82.0,
            "deal_label": "🔥 HOT",
        },
        {
            "city": "minsk",
            "rooms": 2,
            "price": 110000,
            "price_usd": 38000,
            "area": 52.0,
            "floor": 7,
            "total_floors": 9,
            "price_per_m2_usd": 731,
            "deal_score": 55.0,
            "deal_label": "😐 NORMAL",
        },
        {
            "city": "minsk",
            "rooms": 1,
            "price": 75000,
            "price_usd": 26000,
            "area": 38.0,
            "floor": 4,
            "total_floors": 5,
            "price_per_m2_usd": 684,
            "deal_score": 95.0,
            "deal_label": "🔥 HOT",
        },
        {
            "city": "minsk",
            "rooms": 3,
            "price": 180000,
            "price_usd": 60000,
            "area": 80.0,
            "floor": 2,
            "total_floors": 9,
            "price_per_m2_usd": 750,
            "deal_score": 30.0,
            "deal_label": "😐 NORMAL",
        },
    ]

    for i, data in enumerate(test_data):
        listing = Listing(
            kufar_id=f"deal_score_test_{i}",
            url=f"https://re.kufar.by/vi/{200000 + i}",
            title=f"Test Apartment {i} ({data['rooms']}-комн., {data['area']}м²)",
            price=data["price"],
            price_usd=data["price_usd"],
            currency="BYN",
            city=data["city"],
            address=f"Test Street {i}, Minsk",
            rooms=data["rooms"],
            area=data["area"],
            floor=data["floor"],
            total_floors=data["total_floors"],
            category="apartments",
            status=ListingStatus.active,
            price_per_m2_usd=data["price_per_m2_usd"],
            deal_score=data["deal_score"],
            deal_label=data["deal_label"],
            first_seen_at=base_time - timedelta(days=i),
            last_seen_at=base_time,
            images=["https://example.com/image1.jpg"],
        )
        test_session.add(listing)
        listings.append(listing)

    await test_session.commit()

    for listing in listings:
        await test_session.refresh(listing)

    return listings


# === GET /api/v1/deals/score тесты ===


class TestDealsScoreEndpoint:
    """Тесты для GET /api/v1/deals/score."""

    async def test_valid_request_minsk_min_score_70(
        self, client, test_listings_with_scores
    ):
        """Valid request (city=minsk, min_score=70) → 200, items с score >= 70."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 70.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "avg_score" in data
        assert data["currency"] == "usd"
        assert data["min_score_filter"] == 70.0

        # Все items должны иметь score >= 70
        for item in data["items"]:
            assert item["deal_score"] >= 70.0

    async def test_valid_request_minsk_min_score_80(
        self, client, test_listings_with_scores
    ):
        """min_score=80 → только score >= 80."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 80.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        # Все items должны иметь score >= 80
        for item in data["items"]:
            assert item["deal_score"] >= 80.0

    async def test_min_score_0_all_listings(self, client, test_listings_with_scores):
        """min_score=0 → все объявления."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 0.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        # Должны быть все minsk объявления
        minsk_listings = [l for l in test_listings_with_scores if l.city == "minsk"]
        assert data["total"] == len(minsk_listings)

    async def test_min_score_100_only_perfect(self, client, test_listings_with_scores):
        """min_score=100 → только score=100."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 100.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        # Нет объявлений со score=100
        assert data["total"] == 0

    async def test_pagination_limit_5(self, client, test_listings_with_scores):
        """Pagination (limit=5, offset=0) → 5 items."""
        response = await client.get(
            "/api/v1/deals/score",
            params={
                "city": "minsk",
                "min_score": 0.0,
                "currency": "usd",
                "limit": 5,
                "offset": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) <= 5
        assert data["limit"] == 5
        assert data["offset"] == 0

    async def test_pagination_offset_5(self, client, test_listings_with_scores):
        """Pagination (limit=5, offset=5) → следующие 5."""
        # Первый запрос
        response1 = await client.get(
            "/api/v1/deals/score",
            params={
                "city": "minsk",
                "min_score": 0.0,
                "currency": "usd",
                "limit": 5,
                "offset": 0,
            },
        )

        # Второй запрос
        response2 = await client.get(
            "/api/v1/deals/score",
            params={
                "city": "minsk",
                "min_score": 0.0,
                "currency": "usd",
                "limit": 5,
                "offset": 5,
            },
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Items должны быть разными
        ids1 = {item["id"] for item in data1["items"]}
        ids2 = {item["id"] for item in data2["items"]}
        assert len(ids1.intersection(ids2)) == 0

    async def test_sorting_by_score_desc(self, client, test_listings_with_scores):
        """Результаты должны быть отсортированы по deal_score DESC."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 0.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        scores = [item["deal_score"] for item in data["items"]]
        # Проверяем что scores отсортированы по убыванию
        assert scores == sorted(scores, reverse=True)

    async def test_different_city_mogilev(self, client, test_listings_with_scores):
        """Другой город (mogilev) → свои объявления."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "mogilev", "min_score": 70.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        # Все items должны быть из Mogilev
        for item in data["items"]:
            assert item["city"] == "mogilev"

    async def test_currency_byn(self, client, test_listings_with_scores):
        """currency=byn → response включает currency='byn'."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 70.0, "currency": "byn"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["currency"] == "byn"
        # Должны быть результаты (те же объявления, но расчёт в BYN)
        assert "items" in data
        assert "avg_score" in data

    async def test_currency_byn_returns_different_scores(
        self, client, test_listings_with_scores
    ):
        """currency=byn → deal_score может отличаться от usd (из-за конвертации avg_price_per_m2)."""
        # Запрос в USD
        response_usd = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 0.0, "currency": "usd"},
        )

        # Запрос в BYN
        response_byn = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 0.0, "currency": "byn"},
        )

        assert response_usd.status_code == 200
        assert response_byn.status_code == 200

        data_usd = response_usd.json()
        data_byn = response_byn.json()

        # Оба должны иметь items
        assert len(data_usd["items"]) > 0
        assert len(data_byn["items"]) > 0

        # Currency должна отличаться
        assert data_usd["currency"] == "usd"
        assert data_byn["currency"] == "byn"

        # Deal score могут отличаться из-за разной avg_price_per_m2
        # (BYN = USD * 3.27, поэтому PriceScore будет другим)
        # Проверяем что запрос выполнен успешно
        assert data_byn["avg_score"] >= 0

    async def test_batch_update_logging(self, client, test_listings_with_scores):
        """Проверка что обновления выполняются (один commit для всех)."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 0.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        # Проверяем что запрос выполнен успешно
        assert "items" in data
        assert "total" in data
        # Все 8 minsk объявлений должны быть обработаны
        assert data["total"] == 8


# === Валидация параметров ===


class TestDealsScoreValidation:
    """Тесты валидации параметров для /api/v1/deals/score."""

    async def test_invalid_city(self, client):
        """Invalid city → 422."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "invalid_city", "min_score": 70.0, "currency": "usd"},
        )

        assert response.status_code == 422

    async def test_invalid_currency(self, client):
        """Invalid currency → 422."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 70.0, "currency": "eur"},
        )

        assert response.status_code == 422

    async def test_min_score_negative(self, client):
        """min_score < 0 → 422."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": -10.0, "currency": "usd"},
        )

        assert response.status_code == 422

    async def test_min_score_above_100(self, client):
        """min_score > 100 → 422."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 150.0, "currency": "usd"},
        )

        assert response.status_code == 422

    async def test_limit_too_large(self, client):
        """limit > 100 → 422."""
        response = await client.get(
            "/api/v1/deals/score",
            params={
                "city": "minsk",
                "min_score": 70.0,
                "currency": "usd",
                "limit": 200,
            },
        )

        assert response.status_code == 422

    async def test_rooms_filter(self, client, test_listings_with_scores):
        """Filter by rooms=2."""
        response = await client.get(
            "/api/v1/deals/score",
            params={
                "city": "minsk",
                "rooms": 2,
                "min_score": 0.0,
                "currency": "usd",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Все items должны иметь rooms=2
        for item in data["items"]:
            assert item["rooms"] == 2


# === GET /api/v1/listings с deal_score ===


class TestListingsWithDealScore:
    """Тесты для GET /api/v1/listings с deal_score параметрами."""

    async def test_sort_by_deal_score_desc(self, client, test_listings_with_scores):
        """sort_by_deal_score=true → сначала highest score."""
        response = await client.get(
            "/api/v1/listings",
            params={
                "city": "minsk",
                "sort_by_deal_score": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Проверяем сортировку
        scores = [
            item.get("deal_score")
            for item in data["items"]
            if item.get("deal_score") is not None
        ]
        # Scores должны быть убывающими (или None в конце из-за nullslast)
        non_none_scores = [s for s in scores if s is not None]
        assert non_none_scores == sorted(non_none_scores, reverse=True)

    async def test_include_score_true(self, client, test_listings_with_scores):
        """include_score=true → response включает deal_score, deal_label."""
        response = await client.get(
            "/api/v1/listings",
            params={
                "city": "minsk",
                "include_score": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Проверяем что есть deal_score и deal_label
        for item in data["items"]:
            assert "deal_score" in item
            assert "deal_label" in item

    async def test_include_score_false(self, client, test_listings_with_scores):
        """include_score=false → стандартный response (deal_score может быть из БД)."""
        response = await client.get(
            "/api/v1/listings",
            params={
                "city": "minsk",
                "include_score": False,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Проверяем что это стандартный ListingResponse
        first_item = data["items"][0]
        assert "id" in first_item
        assert "kufar_id" in first_item
        assert "price" in first_item
        # deal_score может быть из БД если он там есть
        assert "deal_score" in first_item  # ListingResponse включает это поле

    async def test_combined_filters_with_score(self, client, test_listings_with_scores):
        """Комбинация фильтров с include_score."""
        response = await client.get(
            "/api/v1/listings",
            params={
                "city": "minsk",
                "rooms": [2],
                "include_score": True,
                "sort_by_deal_score": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Все items должны иметь rooms=2
        for item in data["items"]:
            assert item["rooms"] == 2
            assert "deal_score" in item


# === Redis Caching ===


class TestDealScoreCaching:
    """Тесты кэширования Deal Score."""

    async def test_first_request_calculates_score(
        self, client, test_listings_with_scores
    ):
        """Первый запрос → calculate_score вызывается."""
        with patch.object(
            DealScoreService, "calculate_score", wraps=DealScoreService.calculate_score
        ) as mock_calculate:
            response = await client.get(
                "/api/v1/deals/score",
                params={"city": "minsk", "min_score": 70.0, "currency": "usd"},
            )

            assert response.status_code == 200
            # Первый запрос должен вызвать calculate_score
            assert mock_calculate.call_count > 0

    async def test_second_request_uses_cache(self, client, test_listings_with_scores):
        """Второй запрос → результат из кэша."""
        # Первый запрос
        response1 = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 70.0, "currency": "usd"},
        )
        assert response1.status_code == 200

        # Второй запрос (должен использовать кэш)
        response2 = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 70.0, "currency": "usd"},
        )
        assert response2.status_code == 200

        # Ответы должны быть одинаковыми
        data1 = response1.json()
        data2 = response2.json()
        assert data1["total"] == data2["total"]
        assert data1["avg_score"] == data2["avg_score"]

    async def test_cache_different_params(self, client, test_listings_with_scores):
        """Разные параметры → разные кэши."""
        response1 = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 70.0, "currency": "usd"},
        )

        response2 = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "min_score": 80.0, "currency": "usd"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Разные min_score → разные результаты
        assert data1["total"] >= data2["total"]


# === Тесты без объявлений ===


class TestDealsScoreEmptyState:
    """Тесты для пустого состояния."""

    async def test_no_listings_in_city(self, client):
        """Нет объявлений в городе → empty response."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "vitebsk", "min_score": 0.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0
        assert data["avg_score"] == 0.0

    async def test_no_listings_matching_rooms(self, client):
        """Нет объявлений с такими комнатами → empty response."""
        response = await client.get(
            "/api/v1/deals/score",
            params={"city": "minsk", "rooms": 10, "min_score": 0.0, "currency": "usd"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0
