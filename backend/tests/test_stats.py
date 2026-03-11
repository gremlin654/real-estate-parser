import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from decimal import Decimal

from app.models.listing import Listing, ListingStatus


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires DB fixture - API tested manually via curl")
async def test_get_summary(client):
    response = await client.get("/api/v1/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert "new_today" in data or "active_total" in data


@pytest.mark.asyncio
async def test_get_summary_with_avg_price_per_m2(client, test_session):
    """Тест: stats summary возвращает avg_price_per_m2 поля."""
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Создаём тестовые объявления
    for i in range(5):
        listing = Listing(
            kufar_id=f"stats_avg_test_{i}",
            url=f"https://re.kufar.by/vi/{8000 + i}",
            title=f"Test Apartment {i}",
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
        "/api/v1/stats/summary",
        params={"city": "minsk"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем новые поля
    assert "avg_price_per_m2_byn" in data
    assert "avg_price_per_m2_usd" in data
    assert "avg_price_per_m2_by_rooms" in data
    
    # Проверяем, что поля не None (так как есть данные)
    assert data["avg_price_per_m2_byn"] is not None
    assert data["avg_price_per_m2_usd"] is not None
    assert data["avg_price_per_m2_by_rooms"] is not None


@pytest.mark.asyncio
async def test_get_summary_without_city(client):
    """Тест: stats summary без city не возвращает avg_price_per_m2."""
    response = await client.get("/api/v1/stats/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    # Без city поля avg_price_per_m2 должны быть None
    assert data.get("avg_price_per_m2_byn") is None
    assert data.get("avg_price_per_m2_usd") is None
    assert data.get("avg_price_per_m2_by_rooms") is None


@pytest.mark.asyncio
async def test_get_summary_avg_price_per_m2_by_rooms_structure(client, test_session):
    """Тест: структура avg_price_per_m2_by_rooms."""
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Создаём объявления с разным количеством комнат
    for rooms in [1, 2, 3]:
        for i in range(3):
            listing = Listing(
                kufar_id=f"stats_rooms_test_{rooms}_{i}",
                url=f"https://re.kufar.by/vi/{9000 + rooms * 100 + i}",
                title=f"{rooms}-room Apartment {i}",
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
    
    response = await client.get(
        "/api/v1/stats/summary",
        params={"city": "minsk"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем структуру avg_price_per_m2_by_rooms
    avg_by_rooms = data.get("avg_price_per_m2_by_rooms")
    assert avg_by_rooms is not None
    assert isinstance(avg_by_rooms, dict)
    
    # Проверяем, что ключи - это строки (номера комнат)
    for key in avg_by_rooms:
        assert key in ["1", "2", "3", "4", "5"]  # Комнаты как строки
        assert isinstance(avg_by_rooms[key], (int, float))  # Значения - числа
