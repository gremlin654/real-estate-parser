"""
Тесты для обработчиков команд Telegram бота.

Покрывает:
- /start (новый и существующий пользователь)
- /help
- /stop (зарегистрированный и незарегистрированный)

Coverage target: 85%+
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.telegram.handlers.commands import (
    cmd_start,
    cmd_help,
    cmd_stop,
)


class TestCmdStart:
    """Тесты для обработчика /start."""

    @pytest.mark.asyncio
    async def test_cmd_start_new_user(
        self, mock_message, mock_session, mock_telegram_user
    ):
        """
        Тест: /start для нового пользователя.

        Ожидание:
        - Вызывается create_user
        - Отправляется приветственное сообщение
        - Показывается основная клавиатура
        """
        # Arrange
        mock_service = AsyncMock()
        mock_service.create_user = AsyncMock(return_value=mock_telegram_user)
        mock_service.activate_user = AsyncMock(return_value=True)

        with patch(
            "app.telegram.handlers.commands.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await cmd_start(mock_message, mock_session)

            # Assert
            mock_service.create_user.assert_called_once_with(
                telegram_id=mock_message.from_user.id,
                username=mock_message.from_user.username,
                first_name=mock_message.from_user.first_name,
                last_name=mock_message.from_user.last_name,
                language_code=mock_message.from_user.language_code or "ru",
            )

            # Проверяем что сообщение отправлено
            assert mock_message.answer.called
            call_args = mock_message.answer.call_args
            assert "Добро пожаловать" in call_args[0][0]
            assert "Kufar Monitor" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cmd_start_existing_user(
        self, mock_message, mock_session, mock_telegram_user
    ):
        """
        Тест: /start для существующего пользователя.

        Ожидание:
        - create_user возвращает существующего пользователя
        - Пользователь не активируется повторно
        - Отправляется приветственное сообщение
        """
        # Arrange
        mock_telegram_user.is_active = True  # Уже активен

        mock_service = AsyncMock()
        mock_service.create_user = AsyncMock(return_value=mock_telegram_user)
        mock_service.activate_user = AsyncMock(return_value=True)

        with patch(
            "app.telegram.handlers.commands.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await cmd_start(mock_message, mock_session)

            # Assert
            mock_service.create_user.assert_called_once()
            # activate_user не должен вызываться для активного пользователя
            mock_service.activate_user.assert_not_called()

            assert mock_message.answer.called

    @pytest.mark.asyncio
    async def test_cmd_start_reactivates_deactivated_user(
        self, mock_message, mock_session, mock_telegram_user
    ):
        """
        Тест: /start для деактивированного пользователя.

        Ожидание:
        - create_user возвращает деактивированного пользователя
        - Вызывается activate_user
        - Отправляется приветственное сообщение
        """
        # Arrange
        mock_telegram_user.is_active = False  # Деактивирован

        mock_service = AsyncMock()
        mock_service.create_user = AsyncMock(return_value=mock_telegram_user)
        mock_service.activate_user = AsyncMock(return_value=True)

        with patch(
            "app.telegram.handlers.commands.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await cmd_start(mock_message, mock_session)

            # Assert
            mock_service.create_user.assert_called_once()
            mock_service.activate_user.assert_called_once_with(mock_telegram_user.id)

            assert mock_message.answer.called


class TestCmdHelp:
    """Тесты для обработчика /help."""

    @pytest.mark.asyncio
    async def test_cmd_help(self, mock_message):
        """
        Тест: /help показывает справку.

        Ожидание:
        - Отправляется сообщение со списком команд
        - Содержит описание всех команд
        """
        # Act
        await cmd_help(mock_message)

        # Assert
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args
        help_text = call_args[0][0]

        assert "Справка" in help_text
        assert "/start" in help_text
        assert "/subscribe" in help_text
        assert "/settings" in help_text
        assert "/help" in help_text
        assert "/stop" in help_text


class TestCmdStop:
    """Тесты для обработчика /stop."""

    @pytest.mark.asyncio
    async def test_cmd_stop_registered_user(
        self, mock_message, mock_session, mock_telegram_user
    ):
        """
        Тест: /stop для зарегистрированного пользователя.

        Ожидание:
        - Находится пользователь по telegram_id
        - Вызывается deactivate_user
        - Отправляется сообщение об отписке
        - Удаляется клавиатура
        """
        # Arrange
        mock_service = AsyncMock()
        mock_service.get_user_by_telegram_id = AsyncMock(
            return_value=mock_telegram_user
        )
        mock_service.deactivate_user = AsyncMock(return_value=True)

        with patch(
            "app.telegram.handlers.commands.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await cmd_stop(mock_message, mock_session)

            # Assert
            mock_service.get_user_by_telegram_id.assert_called_once_with(
                mock_message.from_user.id
            )
            mock_service.deactivate_user.assert_called_once_with(mock_telegram_user.id)

            assert mock_message.answer.called
            call_args = mock_message.answer.call_args
            stop_text = call_args[0][0]

            assert "отписались" in stop_text.lower()
            assert "/start" in stop_text

            # Проверяем что клавиатура удалена
            assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_cmd_stop_not_registered(self, mock_message, mock_session):
        """
        Тест: /stop для незарегистрированного пользователя.

        Ожидание:
        - Пользователь не найден
        - Отправляется сообщение что нужно использовать /start
        - Не вызывается deactivate_user
        """
        # Arrange
        mock_service = AsyncMock()
        mock_service.get_user_by_telegram_id = AsyncMock(return_value=None)
        mock_service.deactivate_user = AsyncMock(return_value=False)

        with patch(
            "app.telegram.handlers.commands.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await cmd_stop(mock_message, mock_session)

            # Assert
            mock_service.get_user_by_telegram_id.assert_called_once()
            mock_service.deactivate_user.assert_not_called()

            assert mock_message.answer.called
            call_args = mock_message.answer.call_args
            error_text = call_args[0][0]

            assert "не зарегистрированы" in error_text.lower()
            assert "/start" in error_text
