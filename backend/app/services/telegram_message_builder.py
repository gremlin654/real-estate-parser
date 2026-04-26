"""
Telegram Message Builder — утилиты для форматирования сообщений.

Модуль предоставляет класс TelegramMessageBuilder для создания
красиво отформатированных сообщений для Telegram бота.

Пример использования:
    from app.services.telegram_message_builder import TelegramMessageBuilder

    message = TelegramMessageBuilder.build_listing_message(
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
"""

from app.config import CITY_NAMES


class TelegramMessageBuilder:
    """
    Утилиты для форматирования сообщений Telegram.

    Все методы статические и не требуют создания экземпляра класса.
    """

    @staticmethod
    def format_city(city_code: str) -> str:
        """
        Преобразует код города в читаемое название с эмодзи.

        Args:
            city_code: Код города (minsk, mogilev, grodno, brest, gomel, vitebsk)

        Returns:
            Строка с эмодзи и названием города, например "🏙️ Минск"

        Example:
            >>> TelegramMessageBuilder.format_city("minsk")
            "🏙️ Минск"
        """
        city_name = CITY_NAMES.get(city_code, city_code.capitalize())
        return f"🏙️ {city_name}"

    @staticmethod
    def format_price(price_byn: int, price_usd: int) -> str:
        """
        Форматирует цену в читаемый вид с разделителями тысяч.

        Args:
            price_byn: Цена в BYN (копейках)
            price_usd: Цена в USD (центах)

        Returns:
            Строка с форматированной ценой, например "$42,500 (123,750 BYN)"

        Example:
            >>> TelegramMessageBuilder.format_price(123750, 42500)
            "$42,500 (123,750 BYN)"
        """
        price_usd_formatted = f"${price_usd:,}"
        price_byn_formatted = f"{price_byn:,} BYN"
        return f"{price_usd_formatted} ({price_byn_formatted})"

    @staticmethod
    def format_rooms(rooms: int) -> str:
        """
        Форматирует количество комнат с правильным склонением.

        Args:
            rooms: Количество комнат (1-5+)

        Returns:
            Строка с правильным склонением, например "2 комнаты"

        Example:
            >>> TelegramMessageBuilder.format_rooms(1)
            "1 комната"
            >>> TelegramMessageBuilder.format_rooms(2)
            "2 комнаты"
            >>> TelegramMessageBuilder.format_rooms(5)
            "5+ комнат"
        """
        if rooms >= 5:
            return f"{rooms}+ комнат"

        # Склонения для русского языка
        if rooms == 1:
            return "1 комната"
        elif rooms in (2, 3, 4):
            return f"{rooms} комнаты"
        else:
            return f"{rooms} комнат"

    @staticmethod
    def format_floor(floor: int, total_floors: int) -> str:
        """
        Форматирует этаж в виде "текущий/всего" или просто "текущий".

        Args:
            floor: Текущий этаж
            total_floors: Общее количество этажей

        Returns:
            Строка в формате "5/9" или "5" если total_floors неизвестен

        Example:
            >>> TelegramMessageBuilder.format_floor(5, 9)
            "5/9"
            >>> TelegramMessageBuilder.format_floor(5, 0)
            "5"
        """
        if total_floors and total_floors > 0:
            return f"{floor}/{total_floors}"
        return str(floor)

    @staticmethod
    def format_deal_badge(deal_percent: float) -> str:
        """
        Форматирует процент выгоды для deal badge.

        Args:
            deal_percent: Процент выгоды (положительное число)

        Returns:
            Строка с эмодзи и процентом, например "🔥 Выгода: 16.5%"

        Example:
            >>> TelegramMessageBuilder.format_deal_badge(16.5)
            "🔥 Выгода: 16.5%"
        """
        return f"🔥 Выгода: {deal_percent:.1f}%"

    @staticmethod
    def format_price_drop(drop_percent: float, amount_usd: int | None = None) -> str:
        """
        Форматирует текст о падении цены.

        Args:
            drop_percent: Процент падения (положительное число)
            amount_usd: Абсолютная сумма падения в USD (опционально)

        Returns:
            Строка с эмодзи, процентом и суммой, например "📉 Цена упала: 10.2%\n   💵 Снижение: $1,000"

        Example:
            >>> TelegramMessageBuilder.format_price_drop(10.2, 1000)
            "📉 Цена упала: 10.2%\n   💵 Снижение: $1,000"
        """
        lines = [f"📉 Цена упала: {drop_percent:.1f}%"]
        if amount_usd and amount_usd > 0:
            lines.append(f"   💵 Снижение: ${amount_usd:,}")
        return "\n".join(lines)

    @staticmethod
    def build_listing_message(
        city: str,
        address: str,
        rooms: int,
        area: float,
        floor: int,
        total_floors: int | None = None,
        price_byn: int = 0,
        price_usd: int = 0,
        price_per_m2_usd: float = 0.0,
        listing_url: str = "",
        deal_percent: float | None = None,
        price_drop_percent: float | None = None,
        price_drop_amount: int | None = None,
        event_type: str = "new_listing",
    ) -> str:
        """
        Собирает полное сообщение об объявлении для Telegram.

        Формирует красиво отформатированное сообщение со всеми
        ключевыми характеристиками объявления.

        Args:
            city: Код города (minsk, mogilev, etc.)
            address: Адрес объявления
            rooms: Количество комнат
            area: Площадь в м²
            floor: Этаж
            total_floors: Общее количество этажей
            price_byn: Цена в BYN
            price_usd: Цена в USD
            price_per_m2_usd: Цена за м² в USD
            listing_url: URL объявления на Kufar
            deal_percent: Процент выгоды (None если нет)
            price_drop_percent: Процент падения цены (None если нет)
            price_drop_amount: Абсолютная сумма снижения в USD (None если нет)
            event_type: Тип события — 'new_listing' или 'price_drop'

        Returns:
            Полностью отформатированное сообщение

        Example:
            >>> message = TelegramMessageBuilder.build_listing_message(
            ...     city="minsk",
            ...     address="ул. Примерная, д. 10",
            ...     rooms=2,
            ...     area=54.5,
            ...     floor=5,
            ...     total_floors=9,
            ...     price_byn=156000,
            ...     price_usd=48000,
            ...     price_per_m2_usd=883.5,
            ...     listing_url="https://re.kufar.by/vi/minsk/kupit/kvartiru/123",
            ...     deal_percent=16.5,
            ... )
        """
        city_formatted = TelegramMessageBuilder.format_city(city)

        if event_type == "price_drop":
            message = f"📉 Цена снизилась — {city_formatted}!\n\n"
        else:
            message = f"🏠 Новая квартира в {city_formatted}!\n\n"

        address_display = address if address and address.strip() else "Не указан"

        message += f"📍 Адрес: {address_display}\n"
        message += f"🚪 Комнат: {TelegramMessageBuilder.format_rooms(rooms)}\n"
        message += f"📐 Площадь: {area} м²\n"
        message += (
            f"🏢 Этаж: {TelegramMessageBuilder.format_floor(floor, total_floors)}\n"
        )

        message += (
            f"💰 Цена: {TelegramMessageBuilder.format_price(price_byn, price_usd)}\n"
        )
        message += f"📊 Цена за м²: ${price_per_m2_usd:,.1f}\n"

        if (
            event_type == "price_drop"
            and price_drop_percent is not None
            and price_drop_percent > 0
        ):
            message += (
                f"\n{TelegramMessageBuilder.format_price_drop(price_drop_percent, price_drop_amount)}\n"
            )
        elif deal_percent is not None and deal_percent > 0:
            message += f"\n{TelegramMessageBuilder.format_deal_badge(deal_percent)}\n"

        message += f"\n🔗 {listing_url}"

        return message
