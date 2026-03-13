"""
Integration тесты для Favorites API endpoints.

Тестируют:
- GET /api/v1/favorites
- POST /api/v1/favorites/{listing_id}
- DELETE /api/v1/favorites/{listing_id}
- GET /api/v1/favorites/check/{listing_id}
- Валидацию параметров
- Пагинацию
- Idempotency операций
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.listing import Listing, ListingStatus
from app.models.favorite import Favorite


@pytest.mark.asyncio
class TestFavoritesEndpoints:
    """Тесты endpoints /api/v1/favorites."""

    async def test_get_favorites_empty_list(self, client, test_session):
        """Тест: получение пустого списка избранных."""
        response = await client.get("/api/v1/favorites", params={"page": 1, "size": 20})

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20

    async def test_add_to_favorites_success(self, client, test_session):
        """Тест: успешное добавление в избранное."""
        # Создаём тестовое объявление
        listing = Listing(
            kufar_id="fav_test_1",
            url="https://re.kufar.by/vi/3001",
            title="Test Apartment for Favorites",
            price=50000,
            price_usd=18000,
            currency="BYN",
            city="minsk",
            rooms=2,
            area=55.0,
            floor=3,
            total_floors=9,
            status=ListingStatus.active,
        )
        test_session.add(listing)
        await test_session.commit()
        await test_session.refresh(listing)

        # Добавляем в избранное
        response = await client.post(f"/api/v1/favorites/{listing.id}")

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "user_id" in data
        assert "listing_id" in data
        assert "created_at" in data
        assert "listing" in data
        assert data["listing_id"] == str(listing.id)
        assert data["listing"]["title"] == "Test Apartment for Favorites"

    async def test_add_to_favorites_idempotent(self, client, test_session):
        """Тест: повторное добавление в избранное (idempotent)."""
        # Создаём тестовое объявление
        listing = Listing(
            kufar_id="fav_test_idempotent",
            url="https://re.kufar.by/vi/3002",
            title="Idempotent Test Apartment",
            price=60000,
            price_usd=21000,
            currency="BYN",
            city="minsk",
            rooms=2,
            area=60.0,
            floor=5,
            total_floors=10,
            status=ListingStatus.active,
        )
        test_session.add(listing)
        await test_session.commit()
        await test_session.refresh(listing)

        # Первое добавление
        response1 = await client.post(f"/api/v1/favorites/{listing.id}")
        assert response1.status_code == 200
        data1 = response1.json()

        # Повторное добавление
        response2 = await client.post(f"/api/v1/favorites/{listing.id}")
        assert response2.status_code == 200
        data2 = response2.json()

        # Должны вернуть одну и ту же запись
        assert data1["id"] == data2["id"]
        assert data1["listing_id"] == data2["listing_id"]

    async def test_add_to_favorites_listing_not_found(self, client, test_session):
        """Тест: добавление несуществующего объявления (404)."""
        fake_id = uuid4()
        response = await client.post(f"/api/v1/favorites/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert f"Listing with id {fake_id} not found" in data["detail"]

    async def test_get_favorites_with_one_item(self, client, test_session):
        """Тест: получение списка с одним избранным."""
        # Создаём объявление
        listing = Listing(
            kufar_id="fav_test_get",
            url="https://re.kufar.by/vi/3003",
            title="Get Test Apartment",
            price=55000,
            price_usd=19500,
            currency="BYN",
            city="minsk",
            rooms=2,
            area=58.0,
            floor=4,
            total_floors=9,
            status=ListingStatus.active,
        )
        test_session.add(listing)
        await test_session.commit()
        await test_session.refresh(listing)

        # Добавляем в избранное
        await client.post(f"/api/v1/favorites/{listing.id}")

        # Получаем список
        response = await client.get("/api/v1/favorites", params={"page": 1, "size": 20})

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["listing_id"] == str(listing.id)

    async def test_remove_from_favorites_success(self, client, test_session):
        """Тест: успешное удаление из избранного."""
        # Создаём объявление
        listing = Listing(
            kufar_id="fav_test_remove",
            url="https://re.kufar.by/vi/3004",
            title="Remove Test Apartment",
            price=65000,
            price_usd=23000,
            currency="BYN",
            city="minsk",
            rooms=3,
            area=70.0,
            floor=6,
            total_floors=12,
            status=ListingStatus.active,
        )
        test_session.add(listing)
        await test_session.commit()
        await test_session.refresh(listing)

        # Добавляем в избранное
        await client.post(f"/api/v1/favorites/{listing.id}")

        # Проверяем что добавлено
        check_response = await client.get(f"/api/v1/favorites/check/{listing.id}")
        assert check_response.json()["is_favorite"] is True

        # Удаляем из избранного
        response = await client.delete(f"/api/v1/favorites/{listing.id}")

        assert response.status_code == 204

        # Проверяем что удалено
        check_response2 = await client.get(f"/api/v1/favorites/check/{listing.id}")
        assert check_response2.json()["is_favorite"] is False

    async def test_remove_from_favorites_idempotent(self, client, test_session):
        """Тест: повторное удаление из избранного (idempotent)."""
        # Создаём объявление
        listing = Listing(
            kufar_id="fav_test_remove_idempotent",
            url="https://re.kufar.by/vi/3005",
            title="Idempotent Remove Test",
            price=70000,
            price_usd=25000,
            currency="BYN",
            city="minsk",
            rooms=3,
            area=75.0,
            floor=7,
            total_floors=12,
            status=ListingStatus.active,
        )
        test_session.add(listing)
        await test_session.commit()
        await test_session.refresh(listing)

        # Первое удаление (объявление не в избранном)
        response1 = await client.delete(f"/api/v1/favorites/{listing.id}")
        assert response1.status_code == 204

        # Повторное удаление
        response2 = await client.delete(f"/api/v1/favorites/{listing.id}")
        assert response2.status_code == 204

    async def test_check_favorite_true(self, client, test_session):
        """Тест: проверка избранного (True)."""
        # Создаём объявление
        listing = Listing(
            kufar_id="fav_test_check_true",
            url="https://re.kufar.by/vi/3006",
            title="Check True Test",
            price=48000,
            price_usd=17000,
            currency="BYN",
            city="minsk",
            rooms=1,
            area=40.0,
            floor=2,
            total_floors=5,
            status=ListingStatus.active,
        )
        test_session.add(listing)
        await test_session.commit()
        await test_session.refresh(listing)

        # Добавляем в избранное
        await client.post(f"/api/v1/favorites/{listing.id}")

        # Проверяем статус
        response = await client.get(f"/api/v1/favorites/check/{listing.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] is True

    async def test_check_favorite_false(self, client, test_session):
        """Тест: проверка избранного (False)."""
        # Создаём объявление
        listing = Listing(
            kufar_id="fav_test_check_false",
            url="https://re.kufar.by/vi/3007",
            title="Check False Test",
            price=52000,
            price_usd=18500,
            currency="BYN",
            city="minsk",
            rooms=2,
            area=55.0,
            floor=3,
            total_floors=9,
            status=ListingStatus.active,
        )
        test_session.add(listing)
        await test_session.commit()
        await test_session.refresh(listing)

        # Проверяем статус (не добавлено)
        response = await client.get(f"/api/v1/favorites/check/{listing.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] is False

    async def test_favorites_pagination(self, client, test_session):
        """Тест: пагинация списка избранных."""
        # Создаём 25 объявлений
        listings = []
        for i in range(25):
            listing = Listing(
                kufar_id=f"fav_test_page_{i}",
                url=f"https://re.kufar.by/vi/{4000 + i}",
                title=f"Pagination Test {i}",
                price=50000 + (i * 1000),
                price_usd=18000 + (i * 300),
                currency="BYN",
                city="minsk",
                rooms=2,
                area=55.0 + (i * 0.1),
                floor=3,
                total_floors=9,
                status=ListingStatus.active,
            )
            listings.append(listing)
            test_session.add(listing)

        await test_session.commit()

        # Добавляем все в избранное
        for listing in listings:
            await client.post(f"/api/v1/favorites/{listing.id}")

        # Первая страница (size=10)
        response1 = await client.get(
            "/api/v1/favorites", params={"page": 1, "size": 10}
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["total"] == 25
        assert len(data1["items"]) == 10
        assert data1["page"] == 1
        assert data1["size"] == 10

        # Вторая страница (size=10)
        response2 = await client.get(
            "/api/v1/favorites", params={"page": 2, "size": 10}
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["total"] == 25
        assert len(data2["items"]) == 10
        assert data2["page"] == 2

        # Третья страница (остаток)
        response3 = await client.get(
            "/api/v1/favorites", params={"page": 3, "size": 10}
        )

        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["total"] == 25
        assert len(data3["items"]) == 5  # Остаток
        assert data3["page"] == 3

    async def test_favorites_validation_size_max(self, client, test_session):
        """Тест: валидация size > 100."""
        response = await client.get(
            "/api/v1/favorites", params={"page": 1, "size": 101}
        )

        assert response.status_code == 422  # Validation error

    async def test_favorites_validation_size_min(self, client, test_session):
        """Тест: валидация size < 1."""
        response = await client.get("/api/v1/favorites", params={"page": 1, "size": 0})

        assert response.status_code == 422  # Validation error

    async def test_favorites_validation_page_min(self, client, test_session):
        """Тест: валидация page < 1."""
        response = await client.get("/api/v1/favorites", params={"page": 0, "size": 20})

        assert response.status_code == 422  # Validation error

    async def test_get_favorites_multiple_listings(self, client, test_session):
        """Тест: получение списка с несколькими избранными."""
        # Создаём 3 объявления
        listings = []
        for i in range(3):
            listing = Listing(
                kufar_id=f"fav_test_multi_{i}",
                url=f"https://re.kufar.by/vi/{5000 + i}",
                title=f"Multi Test {i}",
                price=50000 + (i * 5000),
                price_usd=18000 + (i * 1500),
                currency="BYN",
                city="minsk",
                rooms=2 + i,
                area=50.0 + (i * 10),
                floor=3 + i,
                total_floors=9,
                status=ListingStatus.active,
            )
            listings.append(listing)
            test_session.add(listing)

        await test_session.commit()

        # Добавляем все в избранное
        for listing in listings:
            await client.post(f"/api/v1/favorites/{listing.id}")

        # Получаем список
        response = await client.get("/api/v1/favorites", params={"page": 1, "size": 20})

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 3

        # Проверяем что все объявления в списке
        listing_ids = {item["listing_id"] for item in data["items"]}
        expected_ids = {str(listing.id) for listing in listings}
        assert listing_ids == expected_ids
