"""
Reply клавиатуры для Telegram бота.

Модуль предоставляет функции для создания reply клавиатур
которые отображаются внизу чата.

Пример использования:
    from app.telegram.keyboards.reply import get_main_keyboard

    await message.answer("Выберите действие:", reply_markup=get_main_keyboard())
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Основная клавиатура с командами бота.

    Returns:
        ReplyKeyboardMarkup с основными командами
    """
    builder = ReplyKeyboardBuilder()

    builder.button(text="/subscribe")
    builder.button(text="/settings")
    builder.button(text="/help")
    builder.button(text="/stop")

    builder.adjust(2)  # 2 кнопки в ряд
    return builder.as_markup(
        resize_keyboard=True,  # Уменьшить размер клавиатуры
        one_time_keyboard=False,  # Не скрывать после нажатия
        input_field_placeholder="Выберите команду:",
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура с кнопкой отмены.

    Используется во время wizard создания подписки.

    Returns:
        ReplyKeyboardMarkup с кнопкой отмены
    """
    builder = ReplyKeyboardBuilder()

    builder.button(text="❌ Отменить")

    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_price_input_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для ввода цены.

    Returns:
        ReplyKeyboardMarkup с кнопкой отмены
    """
    builder = ReplyKeyboardBuilder()

    builder.button(text="❌ Отменить")
    builder.button(text="⏭️ Пропустить (любая цена)")

    builder.adjust(2)
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
    )
