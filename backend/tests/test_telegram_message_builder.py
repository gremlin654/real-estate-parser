"""
Unit тесты для TelegramMessageBuilder.

Тестирует утилиты форматирования сообщений для Telegram бота.

Запуск:
    cd backend
    python -m pytest tests/test_telegram_message_builder.py -v
"""

import pytest
from app.services.telegram_message_builder import TelegramMessageBuilder


class TestFormatCity:
    """Тесты для метода format_city."""

    def test_format_city_minsk(self):
        result = TelegramMessageBuilder.format_city("minsk")
        assert result == "🏙️ Минск"

    def test_format_city_mogilev(self):
        result = TelegramMessageBuilder.format_city("mogilev")
        assert result == "🏙️ Могилёв"

    def test_format_city_grodno(self):
        result = TelegramMessageBuilder.format_city("grodno")
        assert result == "🏙️ Гродно"

    def test_format_city_brest(self):
        result = TelegramMessageBuilder.format_city("brest")
        assert result == "🏙️ Брест"

    def test_format_city_gomel(self):
        result = TelegramMessageBuilder.format_city("gomel")
        assert result == "🏙️ Гомель"

    def test_format_city_vitebsk(self):
        result = TelegramMessageBuilder.format_city("vitebsk")
        assert result == "🏙️ Витебск"

    def test_format_city_unknown(self):
        result = TelegramMessageBuilder.format_city("unknown")
        assert result == "🏙️ Unknown"


class TestFormatPrice:
    """Тесты для метода format_price."""

    def test_format_price_typical(self):
        result = TelegramMessageBuilder.format_price(123750, 42500)
        assert result == "$42,500 (123,750 BYN)"

    def test_format_price_small(self):
        result = TelegramMessageBuilder.format_price(50000, 15000)
        assert result == "$15,000 (50,000 BYN)"

    def test_format_price_large(self):
        result = TelegramMessageBuilder.format_price(500000, 150000)
        assert result == "$150,000 (500,000 BYN)"

    def test_format_price_zero(self):
        result = TelegramMessageBuilder.format_price(0, 0)
        assert result == "$0 (0 BYN)"


class TestFormatRooms:
    """Тесты для метода format_rooms."""

    def test_format_rooms_1(self):
        result = TelegramMessageBuilder.format_rooms(1)
        assert result == "1 комната"

    def test_format_rooms_2(self):
        result = TelegramMessageBuilder.format_rooms(2)
        assert result == "2 комнаты"

    def test_format_rooms_3(self):
        result = TelegramMessageBuilder.format_rooms(3)
        assert result == "3 комнаты"

    def test_format_rooms_4(self):
        result = TelegramMessageBuilder.format_rooms(4)
        assert result == "4 комнаты"

    def test_format_rooms_5(self):
        result = TelegramMessageBuilder.format_rooms(5)
        assert result == "5+ комнат"

    def test_format_rooms_6(self):
        result = TelegramMessageBuilder.format_rooms(6)
        assert result == "6+ комнат"

    def test_format_rooms_10(self):
        result = TelegramMessageBuilder.format_rooms(10)
        assert result == "10+ комнат"


class TestFormatFloor:
    """Тесты для метода format_floor."""

    def test_format_floor_typical(self):
        result = TelegramMessageBuilder.format_floor(5, 9)
        assert result == "5/9"

    def test_format_floor_first(self):
        result = TelegramMessageBuilder.format_floor(1, 5)
        assert result == "1/5"

    def test_format_floor_last(self):
        result = TelegramMessageBuilder.format_floor(9, 9)
        assert result == "9/9"

    def test_format_floor_single(self):
        result = TelegramMessageBuilder.format_floor(1, 1)
        assert result == "1/1"


class TestFormatDealBadge:
    """Тесты для метода format_deal_badge."""

    def test_format_deal_badge_typical(self):
        result = TelegramMessageBuilder.format_deal_badge(16.5)
        assert result == "🔥 Выгода: 16.5%"

    def test_format_deal_badge_small(self):
        result = TelegramMessageBuilder.format_deal_badge(5.0)
        assert result == "🔥 Выгода: 5.0%"

    def test_format_deal_badge_large(self):
        result = TelegramMessageBuilder.format_deal_badge(25.75)
        assert result == "🔥 Выгода: 25.8%"

    def test_format_deal_badge_zero(self):
        result = TelegramMessageBuilder.format_deal_badge(0.0)
        assert result == "🔥 Выгода: 0.0%"


class TestFormatPriceDrop:
    """Тесты для метода format_price_drop."""

    def test_format_price_drop_typical(self):
        result = TelegramMessageBuilder.format_price_drop(10.2)
        assert result == "📉 Цена упала: 10.2%"

    def test_format_price_drop_small(self):
        result = TelegramMessageBuilder.format_price_drop(1.5)
        assert result == "📉 Цена упала: 1.5%"

    def test_format_price_drop_large(self):
        result = TelegramMessageBuilder.format_price_drop(30.0)
        assert result == "📉 Цена упала: 30.0%"


class TestBuildListingMessage:
    """Тесты для метода build_listing_message."""

    def test_build_listing_message_full(self):
        result = TelegramMessageBuilder.build_listing_message(
            city="minsk",
            address="ул. Примерная, д. 10",
            rooms=2,
            area=54.5,
            floor=5,
            total_floors=9,
            price_byn=156000,
            price_usd=48000,
            price_per_m2_usd=883.5,
            listing_url="https://re.kufar.by/vi/minsk/kupit/kvartiru/123456",
            deal_percent=16.5,
            price_drop_percent=10.2,
        )

        # Проверяем ключевые части
        assert "🏠 Новая квартира в 🏙️ Минск!" in result
        assert "📍 Адрес: ул. Примерная, д. 10" in result
        assert "🚪 Комнат: 2 комнаты" in result
        assert "📐 Площадь: 54.5 м²" in result
        assert "🏢 Этаж: 5/9" in result
        assert "💰 Цена: $48,000 (156,000 BYN)" in result
        assert "📊 Цена за м²: $883.5" in result
        assert "🔥 Выгода: 16.5%" in result
        assert "📉 Цена упала" not in result
        assert "🔗 https://re.kufar.by/vi/minsk/kupit/kvartiru/123456" not in result

    def test_build_listing_message_minimal(self):
        result = TelegramMessageBuilder.build_listing_message(
            city="mogilev",
            address="Не указан",
            rooms=1,
            area=35.0,
            floor=2,
            total_floors=5,
            price_byn=50000,
            price_usd=15000,
            price_per_m2_usd=428.57,
            listing_url="https://re.kufar.by/vi/mogilev/kupit/kvartiru/789",
            deal_percent=None,
            price_drop_percent=None,
        )

        # Проверяем ключевые части
        assert "🏠 Новая квартира в 🏙️ Могилёв!" in result
        assert "📍 Адрес: Не указан" in result
        assert "🚪 Комнат: 1 комната" in result
        assert "📐 Площадь: 35.0 м²" in result
        assert "🏢 Этаж: 2/5" in result
        assert "💰 Цена: $15,000 (50,000 BYN)" in result
        assert "📊 Цена за м²: $428.6" in result
        assert "🔗 https://re.kufar.by/vi/mogilev/kupit/kvartiru/789" not in result

        # Проверяем что deal и price drop отсутствуют
        assert "🔥 Выгода" not in result
        assert "📉 Цена упала" not in result

    def test_build_listing_message_with_deal_only(self):
        result = TelegramMessageBuilder.build_listing_message(
            city="brest",
            address="ул. Ленина, 5",
            rooms=3,
            area=75.0,
            floor=3,
            total_floors=5,
            price_byn=120000,
            price_usd=37000,
            price_per_m2_usd=493.33,
            listing_url="https://re.kufar.by/vi/brest/kupit/kvartiru/456",
            deal_percent=12.5,
            price_drop_percent=None,
        )

        assert "🔥 Выгода: 12.5%" in result
        assert "📉 Цена упала" not in result

    def test_build_listing_message_with_price_drop_only(self):
        result = TelegramMessageBuilder.build_listing_message(
            city="gomel",
            address="пр. Октября, 20",
            rooms=4,
            area=85.0,
            floor=7,
            total_floors=9,
            price_byn=180000,
            price_usd=55000,
            price_per_m2_usd=647.06,
            listing_url="https://re.kufar.by/vi/gomel/kupit/kvartiru/321",
            deal_percent=None,
            price_drop_percent=8.5,
            event_type="price_drop",
        )

        assert "🔥 Выгода" not in result
        assert "📉 Цена упала: 8.5%" in result

    def test_build_listing_message_event_type_price_drop(self):
        result = TelegramMessageBuilder.build_listing_message(
            city="minsk",
            address="ул. Тестовая, д. 1",
            rooms=2,
            area=50.0,
            floor=3,
            total_floors=9,
            price_byn=150000,
            price_usd=46000,
            price_per_m2_usd=920.0,
            listing_url="https://re.kufar.by/vi/minsk/kupit/kvartiru/999",
            deal_percent=10.0,
            price_drop_percent=15.0,
            event_type="price_drop",
        )

        assert "📉 Цена снизилась — 🏙️ Минск!" in result
        assert "📉 Цена упала: 15.0%" in result
        assert "🔥 Выгода" not in result

    def test_build_listing_message_event_type_new_listing_shows_deal_badge(self):
        result = TelegramMessageBuilder.build_listing_message(
            city="minsk",
            address="ул. Тестовая, д. 1",
            rooms=2,
            area=50.0,
            floor=3,
            total_floors=9,
            price_byn=150000,
            price_usd=46000,
            price_per_m2_usd=920.0,
            listing_url="https://re.kufar.by/vi/minsk/kupit/kvartiru/999",
            deal_percent=10.0,
            price_drop_percent=5.0,
            event_type="new_listing",
        )

        assert "🏠 Новая квартира в 🏙️ Минск!" in result
        assert "🔥 Выгода: 10.0%" in result
        assert "📉 Цена упала" not in result
