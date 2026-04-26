"""
Inline клавиатуры для Telegram бота.

Модуль предоставляет функции для создания inline клавиатур
с использованием CallbackData для type-safe callbacks.

Пример использования:
    from app.telegram.keyboards.inline import (
        get_city_keyboard,
        get_rooms_keyboard,
    )

    keyboard = get_city_keyboard()
    await message.answer("Выберите город:", reply_markup=keyboard)
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from app.config import CITY_NAMES


class CityCallback(CallbackData, prefix="city"):
    """Callback для выбора города."""

    city: str


class RoomsCallback(CallbackData, prefix="rooms"):
    """Callback для выбора комнат."""

    rooms: str  # "1", "2", "3", "4", "5", "any"


class CurrencyCallback(CallbackData, prefix="curr"):
    """Callback для выбора валюты подписки."""

    currency: str  # "usd" | "byn"


class PriceDropNotifyCallback(CallbackData, prefix="price_drop"):
    """Callback для настройки уведомлений только о падении цены."""

    enabled: str  # "1" | "0"


class SubscriptionActionCallback(CallbackData, prefix="sub_action"):
    """Callback для действий с подпиской."""

    action: str  # "confirm", "cancel", "add_new"


class EditSubscriptionCallback(CallbackData, prefix="edit_sub"):
    """Callback для начала редактирования подписки."""

    subscription_id: str


class EditSubscriptionFieldCallback(CallbackData, prefix="edit_field"):
    """Callback для редактирования конкретного поля подписки."""

    subscription_id: str
    field: str  # city, rooms, price, curr, ppm2, floor, drop, deal


class DeleteSubscriptionCallback(CallbackData, prefix="delete_sub"):
    """Callback для удаления подписки."""

    subscription_id: str


class ListingActionCallback(CallbackData, prefix="listing"):
    """Callback для действий с объявлением."""

    action: str  # "settings"
    listing_id: str | None = None


def get_city_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора города.

    Returns:
        InlineKeyboardMarkup с кнопками городов
    """
    builder = InlineKeyboardBuilder()

    for city_code, city_name in CITY_NAMES.items():
        builder.button(
            text=city_name,
            callback_data=CityCallback(city=city_code),
        )

    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup()


def get_rooms_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора комнат.

    Returns:
        InlineKeyboardMarkup с кнопками комнат
    """
    builder = InlineKeyboardBuilder()

    # Конкретные комнаты
    for rooms in [1, 2, 3, 4]:
        builder.button(
            text=f"{rooms} комн.",
            callback_data=RoomsCallback(rooms=str(rooms)),
        )

    # 5+ комнат
    builder.button(
        text="5+ комн.",
        callback_data=RoomsCallback(rooms="5"),
    )

    # Любые комнаты
    builder.button(
        text="Любые",
        callback_data=RoomsCallback(rooms="any"),
    )

    builder.adjust(3)  # 3 кнопки в ряд
    return builder.as_markup()


def get_price_input_keyboard() -> InlineKeyboardMarkup:
    """
    Inline клавиатура для ввода цены.

    Returns:
        InlineKeyboardMarkup с кнопками отмены и пропуска
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭️ Пропустить (любая цена)", callback_data="skip_price")
    builder.button(text="❌ Отменить", callback_data="cancel_subscription")
    builder.adjust(1)
    return builder.as_markup()


def get_currency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора валюты подписки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="USD ($)", callback_data=CurrencyCallback(currency="usd"))
    builder.button(text="BYN (Br)", callback_data=CurrencyCallback(currency="byn"))
    builder.button(text="❌ Отменить", callback_data="cancel_subscription")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_price_drop_toggle_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора режима уведомлений."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Только падение цены",
        callback_data=PriceDropNotifyCallback(enabled="1"),
    )
    builder.button(
        text="Все новые объявления",
        callback_data=PriceDropNotifyCallback(enabled="0"),
    )
    builder.button(text="❌ Отменить", callback_data="cancel_subscription")
    builder.adjust(1)
    return builder.as_markup()


def get_subscription_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения подписки.

    Returns:
        InlineKeyboardMarkup с кнопками подтвердить/отменить
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Подтвердить",
        callback_data=SubscriptionActionCallback(action="confirm"),
    )
    builder.button(
        text="❌ Отменить",
        callback_data=SubscriptionActionCallback(action="cancel"),
    )

    builder.adjust(2)
    return builder.as_markup()


def get_subscriptions_list_keyboard(
    subscriptions: list,
) -> InlineKeyboardMarkup:
    """
    Клавиатура списка подписок.

    Args:
        subscriptions: Список объектов TelegramSubscription

    Returns:
        InlineKeyboardMarkup с кнопками редактирования/удаления
    """
    builder = InlineKeyboardBuilder()

    for idx, sub in enumerate(subscriptions, start=1):
        # Формируем текст для кнопки
        rooms_text = _format_rooms_short(sub.rooms)
        city_name = CITY_NAMES.get(sub.city, sub.city)
        label = f"{idx}. {city_name} | {rooms_text}"

        # Кнопка редактирования
        builder.button(
            text=f"✏️ {label}",
            callback_data=EditSubscriptionCallback(subscription_id=str(sub.id)),
        )

        # Кнопка удаления
        builder.button(
            text=f"🗑 Удалить",
            callback_data=DeleteSubscriptionCallback(subscription_id=str(sub.id)),
        )

    # Кнопка добавления новой подписки
    builder.button(
        text="➕ Добавить новую",
        callback_data=SubscriptionActionCallback(action="add_new"),
    )

    builder.adjust(2)
    return builder.as_markup()


def get_listing_keyboard(url: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для объявления.

    Args:
        url: URL объявления на Kufar

    Returns:
        InlineKeyboardMarkup с кнопкой открытия и настройками
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔗 Открыть объявление",
        web_app=WebAppInfo(url=url),
    )
    builder.button(
        text="⚙️ Настройки уведомомлений",
        callback_data=ListingActionCallback(action="settings"),
    )

    builder.adjust(1)
    return builder.as_markup()


def get_edit_subscription_keyboard(
    subscription_id: str,
) -> InlineKeyboardMarkup:
    """
    Клавиатура для редактирования подписки.

    Args:
        subscription_id: UUID подписки

    Returns:
        InlineKeyboardMarkup с полями для редактирования
    """
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🏙️ Изменить город",
        callback_data=EditSubscriptionFieldCallback(
            subscription_id=subscription_id,
            field="city",
        ),
    )
    builder.button(
        text="🚪 Изменить комнаты",
        callback_data=EditSubscriptionFieldCallback(
            subscription_id=subscription_id,
            field="rooms",
        ),
    )
    builder.button(
        text="💰 Изменить цену",
        callback_data=EditSubscriptionFieldCallback(
            subscription_id=subscription_id,
            field="price",
        ),
    )
    builder.button(
        text="💱 Изменить валюту",
        callback_data=EditSubscriptionFieldCallback(
            subscription_id=subscription_id,
            field="curr",
        ),
    )
    builder.button(
        text="📏 Изменить цену за м²",
        callback_data=EditSubscriptionFieldCallback(
            subscription_id=subscription_id,
            field="ppm2",
        ),
    )
    builder.button(
        text="🏢 Изменить этаж",
        callback_data=EditSubscriptionFieldCallback(
            subscription_id=subscription_id,
            field="floor",
        ),
    )
    builder.button(
        text="📉 Price-drop режим",
        callback_data=EditSubscriptionFieldCallback(
            subscription_id=subscription_id,
            field="drop",
        ),
    )
    builder.button(
        text="🎯 Порог Deal Score",
        callback_data=EditSubscriptionFieldCallback(
            subscription_id=subscription_id,
            field="deal",
        ),
    )
    builder.button(
        text="🗑 Удалить подписку",
        callback_data=DeleteSubscriptionCallback(subscription_id=subscription_id),
    )
    builder.button(
        text="⬅️ Назад",
        callback_data=SubscriptionActionCallback(action="cancel"),
    )

    builder.adjust(1)
    return builder.as_markup()


def _format_rooms_short(rooms: list | None) -> str:
    """
    Форматирует количество комнат для короткого отображения.

    Args:
        rooms: Список комнат или None

    Returns:
        Короткая строка с количеством комнат
    """
    if rooms is None or len(rooms) == 0:
        return "Любые"
    if rooms == [5]:
        return "5+"
    return ", ".join(str(r) for r in rooms)
