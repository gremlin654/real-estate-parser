"""
Кастомные исключения для сервиса управления подписками Telegram.

Модуль содержит исключения для валидации параметров подписок
и ограничения бизнес-логики.
"""


class TelegramSubscriptionError(Exception):
    """Базовое исключение для ошибок подписок Telegram."""

    pass


class NotificationSendError(Exception):
    """Ошибка при отправке уведомления в Telegram."""

    pass


class SubscriptionLimitExceeded(TelegramSubscriptionError):
    """Превышен лимит активных подписок пользователя."""

    def __init__(self, user_id, current_count: int, max_count: int = 5):
        self.user_id = user_id
        self.current_count = current_count
        self.max_count = max_count
        super().__init__(
            f"User {user_id} has {current_count} active subscriptions, "
            f"maximum allowed is {max_count}"
        )


class DuplicateSubscriptionError(TelegramSubscriptionError):
    """Подписка с такими параметрами уже существует."""

    def __init__(self, user_id, subscription_id=None):
        self.user_id = user_id
        self.subscription_id = subscription_id
        if subscription_id:
            super().__init__(
                f"Duplicate active subscription for user {user_id}: {subscription_id}"
            )
        else:
            super().__init__(f"Duplicate active subscription for user {user_id}")


class InvalidCityError(TelegramSubscriptionError):
    """Недопустимый город."""

    def __init__(self, city: str):
        self.city = city
        super().__init__(
            f"Invalid city: '{city}'. "
            f"Valid cities are: minsk, mogilev, grodno, brest, gomel, vitebsk"
        )


class InvalidRoomsError(TelegramSubscriptionError):
    """Недопустимое количество комнат."""

    def __init__(self, rooms):
        self.rooms = rooms
        super().__init__(
            f"Invalid rooms value: {rooms}. "
            f"Valid values are: 1-4, [5] для 5+, или None для любых"
        )


class InvalidPriceRangeError(TelegramSubscriptionError):
    """Недопустимый диапазон цен."""

    def __init__(self, price_min=None, price_max=None):
        self.price_min = price_min
        self.price_max = price_max
        if price_min is not None and price_max is not None and price_min >= price_max:
            message = (
                f"Invalid price range: price_min ({price_min}) "
                f"must be less than price_max ({price_max})"
            )
        elif price_min is not None and price_min <= 0:
            message = f"Invalid price_min: {price_min}. Must be positive"
        elif price_max is not None and price_max <= 0:
            message = f"Invalid price_max: {price_max}. Must be positive"
        else:
            message = f"Invalid price range: min={price_min}, max={price_max}"
        super().__init__(message)


class InvalidFloorRangeError(TelegramSubscriptionError):
    """Недопустимый диапазон этажей."""

    def __init__(self, floor_min=None, floor_max=None):
        self.floor_min = floor_min
        self.floor_max = floor_max
        if floor_min is not None and floor_max is not None and floor_min >= floor_max:
            message = (
                f"Invalid floor range: floor_min ({floor_min}) "
                f"must be less than floor_max ({floor_max})"
            )
        elif floor_min is not None and floor_min <= 0:
            message = f"Invalid floor_min: {floor_min}. Must be positive"
        elif floor_max is not None and floor_max <= 0:
            message = f"Invalid floor_max: {floor_max}. Must be positive"
        else:
            message = f"Invalid floor range: min={floor_min}, max={floor_max}"
        super().__init__(message)


class InvalidCurrencyError(TelegramSubscriptionError):
    """Недопустимая валюта."""

    def __init__(self, currency: str):
        self.currency = currency
        super().__init__(
            f"Invalid currency: '{currency}'. Valid currencies are: byn, usd"
        )


class SubscriptionNotFoundError(TelegramSubscriptionError):
    """Подписка не найдена."""

    def __init__(self, subscription_id):
        self.subscription_id = subscription_id
        super().__init__(f"Subscription {subscription_id} not found")


class UserNotFoundError(TelegramSubscriptionError):
    """Пользователь не найден."""

    def __init__(self, user_id=None, telegram_id=None):
        self.user_id = user_id
        self.telegram_id = telegram_id
        if user_id:
            super().__init__(f"User {user_id} not found")
        elif telegram_id:
            super().__init__(f"User with telegram_id {telegram_id} not found")
        else:
            super().__init__("User not found")
