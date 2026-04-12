"""
Тесты для TelegramSubscriptionValidator.

Unit тесты для проверки всех методов валидации:
- validate_city
- validate_rooms
- validate_price_range
- validate_floor_range
- validate_currency
- validate_subscription_limit
"""

import pytest

from app.services.telegram_validators import TelegramSubscriptionValidator
from app.services.telegram_exceptions import (
    InvalidCityError,
    InvalidRoomsError,
    InvalidPriceRangeError,
    InvalidFloorRangeError,
    InvalidCurrencyError,
    SubscriptionLimitExceeded,
)


class TestValidateCity:
    """Тесты для validate_city."""

    def test_validate_city_valid_minsk(self):
        """Тест валидного города: minsk."""
        assert TelegramSubscriptionValidator.validate_city("minsk") == True

    def test_validate_city_valid_mogilev(self):
        """Тест валидного города: mogilev."""
        assert TelegramSubscriptionValidator.validate_city("mogilev") == True

    def test_validate_city_valid_grodno(self):
        """Тест валидного города: grodno."""
        assert TelegramSubscriptionValidator.validate_city("grodno") == True

    def test_validate_city_valid_brest(self):
        """Тест валидного города: brest."""
        assert TelegramSubscriptionValidator.validate_city("brest") == True

    def test_validate_city_valid_gomel(self):
        """Тест валидного города: gomel."""
        assert TelegramSubscriptionValidator.validate_city("gomel") == True

    def test_validate_city_valid_vitebsk(self):
        """Тест валидного города: vitebsk."""
        assert TelegramSubscriptionValidator.validate_city("vitebsk") == True

    def test_validate_city_invalid(self):
        """Тест невалидного города."""
        with pytest.raises(InvalidCityError):
            TelegramSubscriptionValidator.validate_city("moscow")

    def test_validate_city_invalid_empty(self):
        """Тест невалидного города: пустая строка."""
        with pytest.raises(InvalidCityError):
            TelegramSubscriptionValidator.validate_city("")

    def test_validate_city_invalid_case(self):
        """Тест невалидного города: неправильный регистр."""
        # Minsk не равен minsk
        with pytest.raises(InvalidCityError):
            TelegramSubscriptionValidator.validate_city("Minsk")


class TestValidateRooms:
    """Тесты для validate_rooms."""

    def test_validate_rooms_none(self):
        """Тест rooms=None (любые комнаты)."""
        assert TelegramSubscriptionValidator.validate_rooms(None) == True

    def test_validate_rooms_empty_list(self):
        """Тест rooms=[] (любые комнаты)."""
        assert TelegramSubscriptionValidator.validate_rooms([]) == True

    def test_validate_rooms_1(self):
        """Тест rooms=[1]."""
        assert TelegramSubscriptionValidator.validate_rooms([1]) == True

    def test_validate_rooms_2(self):
        """Тест rooms=[2]."""
        assert TelegramSubscriptionValidator.validate_rooms([2]) == True

    def test_validate_rooms_3(self):
        """Тест rooms=[3]."""
        assert TelegramSubscriptionValidator.validate_rooms([3]) == True

    def test_validate_rooms_4(self):
        """Тест rooms=[4]."""
        assert TelegramSubscriptionValidator.validate_rooms([4]) == True

    def test_validate_rooms_5_plus(self):
        """Тест rooms=[5] для 5+ комнат."""
        assert TelegramSubscriptionValidator.validate_rooms([5]) == True

    def test_validate_rooms_multiple(self):
        """Тест rooms=[1, 2, 3]."""
        assert TelegramSubscriptionValidator.validate_rooms([1, 2, 3]) == True

    def test_validate_rooms_invalid_zero(self):
        """Тест невалидных комнат: 0."""
        with pytest.raises(InvalidRoomsError):
            TelegramSubscriptionValidator.validate_rooms([0])

    def test_validate_rooms_invalid_six(self):
        """Тест невалидных комнат: 6 (не в допустимых)."""
        with pytest.raises(InvalidRoomsError):
            TelegramSubscriptionValidator.validate_rooms([6])

    def test_validate_rooms_invalid_negative(self):
        """Тест невалидных комнат: отрицательное число."""
        with pytest.raises(InvalidRoomsError):
            TelegramSubscriptionValidator.validate_rooms([-1])

    def test_validate_rooms_invalid_type(self):
        """Тест невалидных комнат: не список."""
        with pytest.raises(InvalidRoomsError):
            TelegramSubscriptionValidator.validate_rooms(2)  # int вместо list

    def test_validate_rooms_invalid_mixed(self):
        """Тест невалидных комнат: смесь валидных и невалидных."""
        with pytest.raises(InvalidRoomsError):
            TelegramSubscriptionValidator.validate_rooms([1, 2, 6])


class TestValidatePriceRange:
    """Тесты для validate_price_range."""

    def test_validate_price_range_both_none(self):
        """Тест price_min=None, price_max=None."""
        assert TelegramSubscriptionValidator.validate_price_range(None, None) == True

    def test_validate_price_range_only_min(self):
        """Тест только price_min."""
        assert TelegramSubscriptionValidator.validate_price_range(30000, None) == True

    def test_validate_price_range_only_max(self):
        """Тест только price_max."""
        assert TelegramSubscriptionValidator.validate_price_range(None, 60000) == True

    def test_validate_price_range_valid(self):
        """Тест валидного диапазона цен."""
        assert (
            TelegramSubscriptionValidator.validate_price_range(30000, 60000) == True
        )

    def test_validate_price_range_min_greater_max(self):
        """Тест price_min > price_max."""
        with pytest.raises(InvalidPriceRangeError):
            TelegramSubscriptionValidator.validate_price_range(60000, 30000)

    def test_validate_price_range_min_equals_max(self):
        """Тест price_min == price_max."""
        with pytest.raises(InvalidPriceRangeError):
            TelegramSubscriptionValidator.validate_price_range(50000, 50000)

    def test_validate_price_range_negative_min(self):
        """Тест отрицательного price_min."""
        with pytest.raises(InvalidPriceRangeError):
            TelegramSubscriptionValidator.validate_price_range(-1000, 50000)

    def test_validate_price_range_negative_max(self):
        """Тест отрицательного price_max."""
        with pytest.raises(InvalidPriceRangeError):
            TelegramSubscriptionValidator.validate_price_range(30000, -1000)

    def test_validate_price_range_zero_min(self):
        """Тест price_min=0."""
        with pytest.raises(InvalidPriceRangeError):
            TelegramSubscriptionValidator.validate_price_range(0, 50000)

    def test_validate_price_range_zero_max(self):
        """Тест price_max=0."""
        with pytest.raises(InvalidPriceRangeError):
            TelegramSubscriptionValidator.validate_price_range(30000, 0)


class TestValidateFloorRange:
    """Тесты для validate_floor_range."""

    def test_validate_floor_range_both_none(self):
        """Тест floor_min=None, floor_max=None."""
        assert TelegramSubscriptionValidator.validate_floor_range(None, None) == True

    def test_validate_floor_range_only_min(self):
        """Тест только floor_min."""
        assert TelegramSubscriptionValidator.validate_floor_range(3, None) == True

    def test_validate_floor_range_only_max(self):
        """Тест только floor_max."""
        assert TelegramSubscriptionValidator.validate_floor_range(None, 10) == True

    def test_validate_floor_range_valid(self):
        """Тест валидного диапазона этажей."""
        assert TelegramSubscriptionValidator.validate_floor_range(3, 10) == True

    def test_validate_floor_range_min_greater_max(self):
        """Тест floor_min > floor_max."""
        with pytest.raises(InvalidFloorRangeError):
            TelegramSubscriptionValidator.validate_floor_range(10, 3)

    def test_validate_floor_range_min_equals_max(self):
        """Тест floor_min == floor_max."""
        with pytest.raises(InvalidFloorRangeError):
            TelegramSubscriptionValidator.validate_floor_range(5, 5)

    def test_validate_floor_range_negative_min(self):
        """Тест отрицательного floor_min."""
        with pytest.raises(InvalidFloorRangeError):
            TelegramSubscriptionValidator.validate_floor_range(-1, 10)

    def test_validate_floor_range_negative_max(self):
        """Тест отрицательного floor_max."""
        with pytest.raises(InvalidFloorRangeError):
            TelegramSubscriptionValidator.validate_floor_range(3, -1)

    def test_validate_floor_range_zero_min(self):
        """Тест floor_min=0."""
        with pytest.raises(InvalidFloorRangeError):
            TelegramSubscriptionValidator.validate_floor_range(0, 10)

    def test_validate_floor_range_zero_max(self):
        """Тест floor_max=0."""
        with pytest.raises(InvalidFloorRangeError):
            TelegramSubscriptionValidator.validate_floor_range(3, 0)


class TestValidateCurrency:
    """Тесты для validate_currency."""

    def test_validate_currency_usd(self):
        """Тест валюты: usd."""
        assert TelegramSubscriptionValidator.validate_currency("usd") == True

    def test_validate_currency_byn(self):
        """Тест валюты: byn."""
        assert TelegramSubscriptionValidator.validate_currency("byn") == True

    def test_validate_currency_invalid_eur(self):
        """Тест невалидной валюты: eur."""
        with pytest.raises(InvalidCurrencyError):
            TelegramSubscriptionValidator.validate_currency("eur")

    def test_validate_currency_invalid_rub(self):
        """Тест невалидной валюты: rub."""
        with pytest.raises(InvalidCurrencyError):
            TelegramSubscriptionValidator.validate_currency("rub")

    def test_validate_currency_invalid_case(self):
        """Тест невалидной валюты: неправильный регистр."""
        with pytest.raises(InvalidCurrencyError):
            TelegramSubscriptionValidator.validate_currency("USD")

    def test_validate_currency_invalid_empty(self):
        """Тест невалидной валюты: пустая строка."""
        with pytest.raises(InvalidCurrencyError):
            TelegramSubscriptionValidator.validate_currency("")


class TestValidateSubscriptionLimit:
    """Тесты для validate_subscription_limit."""

    def test_validate_subscription_limit_under(self):
        """Тест: количество ниже лимита."""
        assert (
            TelegramSubscriptionValidator.validate_subscription_limit(
                3, max_subscriptions=5
            )
            == True
        )

    def test_validate_subscription_limit_at(self):
        """Тест: количество на лимите (должно проходить, т.к. считаем ДО добавления)."""
        # 4 < 5 — всё ещё можно добавить
        assert (
            TelegramSubscriptionValidator.validate_subscription_limit(
                4, max_subscriptions=5
            )
            == True
        )

    def test_validate_subscription_limit_over(self):
        """Тест: количество превысило лимит."""
        with pytest.raises(SubscriptionLimitExceeded):
            TelegramSubscriptionValidator.validate_subscription_limit(
                5, max_subscriptions=5
            )

    def test_validate_subscription_limit_zero(self):
        """Тест: ноль подписок."""
        assert (
            TelegramSubscriptionValidator.validate_subscription_limit(
                0, max_subscriptions=5
            )
            == True
        )

    def test_validate_subscription_limit_default_max(self):
        """Тест: использование лимита по умолчанию (5)."""
        with pytest.raises(SubscriptionLimitExceeded):
            TelegramSubscriptionValidator.validate_subscription_limit(5)

    def test_validate_subscription_limit_custom_max(self):
        """Тест: кастомный лимит."""
        assert (
            TelegramSubscriptionValidator.validate_subscription_limit(
                2, max_subscriptions=10
            )
            == True
        )

    def test_validate_subscription_limit_exceeded_exception_attributes(self):
        """Тест: проверка атрибутов исключения."""
        try:
            TelegramSubscriptionValidator.validate_subscription_limit(
                7, max_subscriptions=5
            )
            assert False, "Should have raised SubscriptionLimitExceeded"
        except SubscriptionLimitExceeded as e:
            assert e.current_count == 7
            assert e.max_count == 5
            assert e.user_id is None  # Не передан в валидаторе
