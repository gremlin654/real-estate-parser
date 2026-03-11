"""
Integration тесты для Deal Finder API endpoint.

Тестируют:
- GET /api/v1/deals
- GET /api/v1/deals/stats
- Валидацию параметров
- Пагинацию
- Фильтрацию
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.models.listing import Listing, ListingStatus


@pytest.mark.asyncio
class TestDealsEndpoint:
    """Тесты endpoint /api/v1/deals."""
    
    async def test_get_deals_basic(self, client, test_session):
        """Тест: базовый запрос deals."""
        # Создаём тестовые объявления с разной ценой за м²
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Объявление с выгодной ценой (800 за м²)
        listing1 = Listing(
            kufar_id="deal_test_1",
            url="https://re.kufar.by/vi/1001",
            title="Cheap Apartment",
            price=44000,
            price_usd=16000,
            currency="BYN",
            city="minsk",
            rooms=2,
            area=55.0,
            floor=3,
            total_floors=9,
            status=ListingStatus.active,
            first_seen_at=base_time,
            last_seen_at=base_time,
            price_per_m2_byn=Decimal("800.00"),
            price_per_m2_usd=Decimal("290.91"),
        )
        
        # Объявление со средней ценой (1000 за м²)
        listing2 = Listing(
            kufar_id="deal_test_2",
            url="https://re.kufar.by/vi/1002",
            title="Normal Apartment",
            price=55000,
            price_usd=20000,
            currency="BYN",
            city="minsk",
            rooms=2,
            area=55.0,
            floor=5,
            total_floors=9,
            status=ListingStatus.active,
            first_seen_at=base_time,
            last_seen_at=base_time,
            price_per_m2_byn=Decimal("1000.00"),
            price_per_m2_usd=Decimal("363.64"),
        )
        
        test_session.add_all([listing1, listing2])
        await test_session.commit()
        
        # Запрос deals с discount 10%
        response = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "rooms": 2, "discount_percent": 10, "currency": "usd"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "avg_price_per_m2" in data
        assert "currency" in data
        assert data["currency"] == "usd"
    
    async def test_get_deals_with_pagination(self, client, test_session):
        """Тест: пагинация deals."""
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Создаём 25 объявлений с выгодной ценой
        for i in range(25):
            listing = Listing(
                kufar_id=f"deal_page_test_{i}",
                url=f"https://re.kufar.by/vi/{2000 + i}",
                title=f"Apartment {i}",
                price=44000 + (i * 1000),
                price_usd=16000 + (i * 300),
                currency="BYN",
                city="minsk",
                rooms=2,
                area=55.0,
                floor=3,
                total_floors=9,
                status=ListingStatus.active,
                first_seen_at=base_time,
                last_seen_at=base_time,
                price_per_m2_byn=Decimal("800.00"),
                price_per_m2_usd=Decimal("290.91"),
            )
            test_session.add(listing)
        
        await test_session.commit()
        
        # Первая страница (limit=10)
        response1 = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "rooms": 2, "limit": 10, "offset": 0}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["limit"] == 10
        assert data1["offset"] == 0
        assert len(data1["items"]) <= 10
        
        # Вторая страница (offset=10)
        response2 = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "rooms": 2, "limit": 10, "offset": 10}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["offset"] == 10
    
    async def test_get_deals_filter_by_rooms(self, client, test_session):
        """Тест: фильтр по комнатам."""
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Объявления с разным количеством комнат
        for rooms in [1, 2, 3]:
            listing = Listing(
                kufar_id=f"deal_rooms_test_{rooms}",
                url=f"https://re.kufar.by/vi/{3000 + rooms}",
                title=f"{rooms}-room Apartment",
                price=40000 * rooms,
                price_usd=15000 * rooms,
                currency="BYN",
                city="minsk",
                rooms=rooms,
                area=50.0 * rooms,
                floor=3,
                total_floors=9,
                status=ListingStatus.active,
                first_seen_at=base_time,
                last_seen_at=base_time,
                price_per_m2_byn=Decimal("800.00"),
                price_per_m2_usd=Decimal("300.00"),
            )
            test_session.add(listing)
        
        await test_session.commit()
        
        # Запрос для 2-комнатных
        response = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "rooms": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Все объявления должны быть 2-комнатными
        for item in data["items"]:
            assert item["rooms"] == 2
    
    async def test_get_deals_invalid_city(self, client):
        """Тест: некорректный город."""
        response = await client.get(
            "/api/v1/deals",
            params={"city": "invalid_city"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    async def test_get_deals_invalid_discount_percent(self, client):
        """Тест: некорректный discount_percent."""
        response = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "discount_percent": 60}
        )
        
        assert response.status_code == 422
    
    async def test_get_deals_invalid_currency(self, client):
        """Тест: некорректная валюта."""
        response = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "currency": "eur"}
        )
        
        assert response.status_code == 422
    
    async def test_get_deals_invalid_limit(self, client):
        """Тест: некорректный limit."""
        response = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "limit": 150}
        )
        
        assert response.status_code == 422
    
    async def test_get_deals_response_structure(self, client, test_session):
        """Тест: структура ответа."""
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        listing = Listing(
            kufar_id="deal_structure_test",
            url="https://re.kufar.by/vi/4000",
            title="Test Apartment",
            price=44000,
            price_usd=16000,
            currency="BYN",
            city="minsk",
            rooms=2,
            area=55.0,
            floor=3,
            total_floors=9,
            status=ListingStatus.active,
            first_seen_at=base_time,
            last_seen_at=base_time,
            price_per_m2_byn=Decimal("800.00"),
            price_per_m2_usd=Decimal("290.91"),
        )
        
        test_session.add(listing)
        await test_session.commit()
        
        response = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "rooms": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем структуру
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "avg_price_per_m2" in data
        assert "currency" in data
        
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "kufar_id" in item
            assert "url" in item
            assert "title" in item
            assert "price" in item
            assert "price_usd" in item
            assert "deal_percent" in item
            assert "avg_price_per_m2" in item
            assert "rooms" in item
            assert "area" in item


@pytest.mark.asyncio
class TestDealsStatsEndpoint:
    """Тесты endpoint /api/v1/deals/stats."""
    
    async def test_get_deals_stats_basic(self, client, test_session):
        """Тест: базовый запрос stats."""
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Создаём несколько объявлений
        for i in range(10):
            listing = Listing(
                kufar_id=f"stats_test_{i}",
                url=f"https://re.kufar.by/vi/{5000 + i}",
                title=f"Apartment {i}",
                price=44000 + (i * 1000),
                price_usd=16000 + (i * 300),
                currency="BYN",
                city="minsk",
                rooms=2,
                area=55.0,
                floor=3,
                total_floors=9,
                status=ListingStatus.active,
                first_seen_at=base_time,
                last_seen_at=base_time,
                price_per_m2_byn=Decimal("800.00"),
                price_per_m2_usd=Decimal("290.91"),
            )
            test_session.add(listing)
        
        await test_session.commit()
        
        response = await client.get(
            "/api/v1/deals/stats",
            params={"city": "minsk", "rooms": 2, "currency": "usd"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "city" in data
        assert "rooms" in data
        assert "currency" in data
        assert "avg_price_per_m2" in data
        assert "total_listings" in data
        assert "potential_deals" in data
        assert "deal_threshold" in data
        assert data["city"] == "minsk"
    
    async def test_get_deals_stats_no_data(self, client):
        """Тест: stats без данных."""
        response = await client.get(
            "/api/v1/deals/stats",
            params={"city": "minsk", "rooms": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["avg_price_per_m2"] is None
        assert data["total_listings"] == 0
        assert data["potential_deals"] == 0
    
    async def test_get_deals_stats_invalid_city(self, client):
        """Тест: некорректный город в stats."""
        response = await client.get(
            "/api/v1/deals/stats",
            params={"city": "invalid_city"}
        )
        
        assert response.status_code == 422


@pytest.mark.asyncio
class TestDealsEndpointEdgeCases:
    """Тесты граничных случаев для deals endpoint."""
    
    async def test_get_deals_no_listings(self, client):
        """Тест: нет объявлений."""
        response = await client.get(
            "/api/v1/deals",
            params={"city": "minsk", "rooms": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["total"] == 0
        assert data["avg_price_per_m2"] == 0.0
    
    async def test_get_deals_city_case_insensitive(self, client, test_session):
        """Тест: город регистронезависимый."""
        base_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        listing = Listing(
            kufar_id="deal_case_test",
            url="https://re.kufar.by/vi/6000",
            title="Test Apartment",
            price=44000,
            price_usd=16000,
            currency="BYN",
            city="minsk",
            rooms=2,
            area=55.0,
            floor=3,
            total_floors=9,
            status=ListingStatus.active,
            first_seen_at=base_time,
            last_seen_at=base_time,
            price_per_m2_byn=Decimal("800.00"),
            price_per_m2_usd=Decimal("290.91"),
        )
        
        test_session.add(listing)
        await test_session.commit()
        
        # Запрос с разным регистром
        for city in ["MINSK", "Minsk", "minsk"]:
            response = await client.get(
                "/api/v1/deals",
                params={"city": city, "rooms": 2}
            )
            
            assert response.status_code == 200
    
    async def test_get_deals_all_valid_cities(self, client):
        """Тест: все валидные города."""
        valid_cities = ["minsk", "mogilev", "grodno", "brest", "gomel", "vitebsk"]
        
        for city in valid_cities:
            response = await client.get(
                "/api/v1/deals",
                params={"city": city}
            )
            
            # Должен вернуть 200 (даже если нет данных)
            assert response.status_code == 200
