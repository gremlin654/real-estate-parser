"""
Фикстуры для тестирования Telegram бота.

Предоставляет моки для aiogram объектов:
- message — мок сообщения
- callback_query — мок callback запроса
- state — мок FSM состояния
- session — мок сессии БД
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from aiogram.types import User, Message, CallbackQuery


@pytest.fixture
def mock_user():
    """Создать мок пользователя Telegram."""
    user = MagicMock(spec=User)
    user.id = 123456789
    user.username = "test_user"
    user.first_name = "Test"
    user.last_name = "User"
    user.language_code = "ru"
    return user


@pytest.fixture
def mock_message(mock_user):
    """Создать мок сообщения."""
    message = AsyncMock(spec=Message)
    message.from_user = mock_user
    message.message_id = 1
    message.text = ""
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


@pytest.fixture
def mock_callback_query(mock_user):
    """Создать мок callback запроса."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = mock_user
    callback.id = 1
    callback.data = ""
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def mock_state():
    """Создать мок FSM состояния."""
    state = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state


@pytest.fixture
def mock_session():
    """Создать мок сессии БД."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_telegram_user():
    """Создать мок пользователя Telegram из БД."""
    user = MagicMock()
    user.id = uuid4()
    user.telegram_id = 123456789
    user.username = "test_user"
    user.first_name = "Test"
    user.last_name = "User"
    user.is_active = True
    user.blocked_by_user = False
    return user


@pytest.fixture
def mock_subscription():
    """Создать мок подписки."""
    from uuid import uuid4

    sub = MagicMock()
    sub.id = uuid4()
    sub.user_id = uuid4()
    sub.city = "minsk"
    sub.rooms = [1, 2]
    sub.price_min = 50000
    sub.price_max = 150000
    sub.price_per_m2_max = None
    sub.floor_min = None
    sub.floor_max = None
    sub.currency = "usd"
    sub.notify_only_price_drop = False
    sub.exclude_deal_below_percent = None
    sub.is_active = True
    return sub
