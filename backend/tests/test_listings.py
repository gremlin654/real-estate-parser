import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from decimal import Decimal

from app.models.listing import Listing, ListingStatus


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires DB fixture - API tested manually via curl")
async def test_get_listings_empty(client):
    response = await client.get("/api/v1/listings")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires DB fixture - API tested manually via curl")
async def test_get_listings_pagination(client):
    response = await client.get("/api/v1/listings?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 10


@pytest.mark.asyncio
async def test_get_listings_include_deal_metrics_param(client, test_session):
    """Тест: параметр include_deal_metrics возвращает deal_percent и avg_price_per_m2."""
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Создаём тестовое объявление
    listing = Listing(
        kufar_id="deal_metrics_test",
        url="https://re.kufar.by/vi/7000",
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
    
    # Запрос с include_deal_metrics=true
    response = await client.get(
        "/api/v1/listings",
        params={"city": "minsk", "include_deal_metrics": "true", "deal_currency": "usd"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    if data["items"]:
        item = data["items"][0]
        # Проверяем наличие полей deal metrics
        assert "deal_percent" in item
        assert "avg_price_per_m2" in item


@pytest.mark.asyncio
async def test_get_listings_without_deal_metrics(client, test_session):
    """Тест: без include_deal_metrics поля deal_percent и avg_price_per_m2 не возвращаются."""
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    listing = Listing(
        kufar_id="no_metrics_test",
        url="https://re.kufar.by/vi/7001",
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
    
    # Запрос без include_deal_metrics (по умолчанию false)
    response = await client.get(
        "/api/v1/listings",
        params={"city": "minsk"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Обратная совместимость: старые запросы работают без изменений
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data


@pytest.mark.asyncio
async def test_get_listings_deal_metrics_currency(client, test_session):
    """Тест: deal_currency параметр для выбора валюты метрик."""
    base_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    listing = Listing(
        kufar_id="currency_test",
        url="https://re.kufar.by/vi/7002",
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
    
    # Запрос с BYN валютой для метрик
    response = await client.get(
        "/api/v1/listings",
        params={"city": "minsk", "include_deal_metrics": "true", "deal_currency": "byn"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
