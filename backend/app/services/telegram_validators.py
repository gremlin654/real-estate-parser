"""
Валидаторы для сервиса управления подписками Telegram.

Модуль содержит класс для валидации входных параметров подписок:
город, комнаты, цены, этажи, валюта и лимиты.
"""

from typing import Literal

from app.config import CITY_NAMES
from app.services.telegram_exceptions import (
    InvalidCityError,
    InvalidRoomsError,
    InvalidPriceRangeError,
    InvalidFloorRangeError,
    InvalidCurrencyError,
    SubscriptionLimitExceeded,
)

# Допустимые города (из CITY_NAMES keys)
VALID_CITIES = set(CITY_NAMES.keys())

# Допустимые валюты
VALID_CURRENCIES = {"byn", "usd"}

# Максимальное количество подписок на пользователя
MAX_SUBSCRIPTIONS_PER_USER = 5

# Допустимые значения комнат (1-4, [5] для 5+)
VALID_ROOMS = {1, 2, 3, 4, 5}


class TelegramSubscriptionValidator:
    """
    Валидатор параметров подписок Telegram.

    Предоставляет статические методы для проверки входных данных
    перед сохранением в базу данных.
    """

    @staticmethod
    def validate_city(city: str) -> Literal[True]:
        """
        Проверяет что город допустим.

        Args:
            city: Код города для проверки

        Returns:
            True если город валиден

        Raises:
            InvalidCityError: Если город недопустим
        """
        if city not in VALID_CITIES:
            raise InvalidCityError(city)
        return True

    @staticmethod
    def validate_rooms(rooms: list[int] | None) -> Literal[True]:
        """
        Проверяет что значение комнат допустимо.

        Правила:
        - None — допустимо (любые комнаты)
        - Пустой список [] — допустимо (любые комнаты)
        - Список с числами 1-4 — конкретные комнаты
        - [5] — 5+ комнат

        Args:
            rooms: Список комнат или None

        Returns:
            True если комнаты валидны

        Raises:
            InvalidRoomsError: Если комнаты недопустимы
        """
        if rooms is None:
            return True

        if not isinstance(rooms, list):
            raise InvalidRoomsError(rooms)

        # Пустой список = любые комнаты
        if len(rooms) == 0:
            return True

        # Проверяем каждое значение
        for room in rooms:
            if room not in VALID_ROOMS:
                raise InvalidRoomsError(rooms)

        return True

    @staticmethod
    def validate_price_range(
        price_min: int | None, price_max: int | None
    ) -> Literal[True]:
        """
        Проверяет диапазон цен.

        Правила:
        - Оба None — допустимо
        - Только один указан — допустимо
        - Оба указаны: 0 < price_min < price_max

        Args:
            price_min: Минимальная цена
            price_max: Максимальная цена

        Returns:
            True если диапазон валиден

        Raises:
            InvalidPriceRangeError: Если диапазон недопустим
        """
        # Оба не указаны — ок
        if price_min is None and price_max is None:
            return True

        # Только один указан — проверяем что > 0
        if price_min is not None and price_max is None:
            if price_min <= 0:
                raise InvalidPriceRangeError(price_min=price_min)
            return True

        if price_min is None and price_max is not None:
            if price_max <= 0:
                raise InvalidPriceRangeError(price_max=price_max)
            return True

        # Оба указаны — проверяем что 0 < min < max
        if price_min <= 0:
            raise InvalidPriceRangeError(price_min=price_min, price_max=price_max)

        if price_max <= 0:
            raise InvalidPriceRangeError(price_min=price_min, price_max=price_max)

        if price_min >= price_max:
            raise InvalidPriceRangeError(price_min=price_min, price_max=price_max)

        return True

    @staticmethod
    def validate_floor_range(
        floor_min: int | None, floor_max: int | None
    ) -> Literal[True]:
        """
        Проверяет диапазон этажей.

        Правила:
        - Оба None — допустимо
        - Только один указан — допустимо если > 0
        - Оба указаны: 0 < floor_min < floor_max

        Args:
            floor_min: Минимальный этаж
            floor_max: Максимальный этаж

        Returns:
            True если диапазон валиден

        Raises:
            InvalidFloorRangeError: Если диапазон недопустим
        """
        # Оба не указаны — ок
        if floor_min is None and floor_max is None:
            return True

        # Только один указан — проверяем что > 0
        if floor_min is not None and floor_max is None:
            if floor_min <= 0:
                raise InvalidFloorRangeError(floor_min=floor_min)
            return True

        if floor_min is None and floor_max is not None:
            if floor_max <= 0:
                raise InvalidFloorRangeError(floor_max=floor_max)
            return True

        # Оба указаны — проверяем что 0 < min < max
        if floor_min <= 0:
            raise InvalidFloorRangeError(floor_min=floor_min, floor_max=floor_max)

        if floor_max <= 0:
            raise InvalidFloorRangeError(floor_min=floor_min, floor_max=floor_max)

        if floor_min >= floor_max:
            raise InvalidFloorRangeError(floor_min=floor_min, floor_max=floor_max)

        return True

    @staticmethod
    def validate_currency(currency: str) -> Literal[True]:
        """
        Проверяет что валюта допустима.

        Args:
            currency: Код валюты для проверки

        Returns:
            True если валюта валидна

        Raises:
            InvalidCurrencyError: Если валюта недопустима
        """
        if currency not in VALID_CURRENCIES:
            raise InvalidCurrencyError(currency)
        return True

    @staticmethod
    def validate_price_per_m2_max(price_per_m2_max: float | None) -> Literal[True]:
        """
        Проверяет максимальную цену за м².

        Args:
            price_per_m2_max: Максимальная цена за м²

        Returns:
            True если значение валидно

        Raises:
            InvalidPriceRangeError: Если значение <= 0
        """
        if price_per_m2_max is not None and price_per_m2_max <= 0:
            raise InvalidPriceRangeError(
                price_min=None, price_max=None
            )  # Используем общее исключение
        return True

    @staticmethod
    def validate_subscription_limit(
        count: int, max_subscriptions: int = MAX_SUBSCRIPTIONS_PER_USER
    ) -> Literal[True]:
        """
        Проверяет что количество подписок не превышает лимит.

        Args:
            count: Текущее количество активных подписок
            max_subscriptions: Максимально допустимое количество

        Returns:
            True если лимит не превышен

        Raises:
            SubscriptionLimitExceeded: Если лимит превышен
        """
        if count >= max_subscriptions:
            raise SubscriptionLimitExceeded(
                user_id=None, current_count=count, max_count=max_subscriptions
            )
        return True
