"""
Тесты для обработчиков подписок Telegram бота.

Покрывает:
- /subscribe — запуск wizard
- Выбор города и комнат
- Ввод цены (валидный и невалидный)
- Подтверждение и отмена подписки
- /settings — с подписками и без
- Редактирование и удаление подписки
- /unsubscribe

Coverage target: 85%+
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.telegram.handlers.subscriptions import (
    cmd_subscribe,
    process_city_selection,
    process_rooms_selection,
    process_price_min,
    process_price_max,
    confirm_subscription,
    cancel_subscription,
    cmd_settings,
    edit_subscription,
    delete_subscription,
    cmd_unsubscribe,
    SubscriptionStates,
    _format_rooms,
)
from app.telegram.keyboards.inline import (
    CityCallback,
    RoomsCallback,
    SubscriptionActionCallback,
    EditSubscriptionCallback,
    DeleteSubscriptionCallback,
)


class TestCmdSubscribe:
    """Тесты для команды /subscribe."""

    @pytest.mark.asyncio
    async def test_cmd_subscribe_starts_flow(self, mock_message, mock_state):
        """
        Тест: /subscribe запускает wizard выбора города.

        Ожидание:
        - state.clear() вызывается
        - Устанавливается состояние waiting_for_city
        - Отправляется сообщение с клавиатурой выбора города
        """
        # Act
        await cmd_subscribe(mock_message, mock_state)

        # Assert
        mock_state.clear.assert_called_once()
        mock_state.set_state.assert_called_once_with(
            SubscriptionStates.waiting_for_city
        )

        assert mock_message.answer.called
        call_args = mock_message.answer.call_args
        assert "Выберите город" in call_args[0][0]


class TestCitySelection:
    """Тесты для выбора города."""

    @pytest.mark.asyncio
    async def test_process_city_selection(self, mock_callback_query, mock_state):
        """
        Тест: Выбор города сохраняет city и переходит к rooms.

        Ожидание:
        - city сохраняется в state
        - Устанавливается состояние waiting_for_rooms
        - Сообщение редактируется с клавиатурой комнат
        """
        # Arrange
        callback_data = CityCallback(city="minsk")

        # Act
        await process_city_selection(mock_callback_query, callback_data, mock_state)

        # Assert
        mock_state.update_data.assert_called_once_with(city="minsk")
        mock_state.set_state.assert_called_once_with(
            SubscriptionStates.waiting_for_rooms
        )

        assert mock_callback_query.message.edit_text.called
        mock_callback_query.answer.assert_called_once()


class TestRoomsSelection:
    """Тесты для выбора комнат."""

    @pytest.mark.asyncio
    async def test_process_rooms_selection(self, mock_callback_query, mock_state):
        """
        Тест: Выбор комнат сохраняет rooms и переходит к price_min.

        Ожидание:
        - rooms=[2] сохраняется в state
        - Устанавливается состояние waiting_for_price_min
        - Сообщение редактируется с запросом цены
        """
        # Arrange
        callback_data = RoomsCallback(rooms="2")
        mock_state.get_data = AsyncMock(return_value={"city": "minsk"})

        # Act
        await process_rooms_selection(mock_callback_query, callback_data, mock_state)

        # Assert
        mock_state.update_data.assert_called_once_with(rooms=[2])
        mock_state.set_state.assert_called_once_with(
            SubscriptionStates.waiting_for_price_min
        )

        assert mock_callback_query.message.edit_text.called
        mock_callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_rooms_selection_any(self, mock_callback_query, mock_state):
        """
        Тест: Выбор "Любые" комнаты сохраняет rooms=None.
        """
        # Arrange
        callback_data = RoomsCallback(rooms="any")
        mock_state.get_data = AsyncMock(return_value={"city": "minsk"})

        # Act
        await process_rooms_selection(mock_callback_query, callback_data, mock_state)

        # Assert
        mock_state.update_data.assert_called_once_with(rooms=None)
        assert mock_callback_query.message.edit_text.called


class TestPriceMinInput:
    """Тесты для ввода минимальной цены."""

    @pytest.mark.asyncio
    async def test_process_price_min_valid(self, mock_message, mock_state):
        """
        Тест: Валидная минимальная цена.

        Ожидание:
        - price_min сохраняется
        - Переход к waiting_for_confirmation (показывается подтверждение)
        """
        # Arrange
        mock_message.text = "50000"
        mock_state.get_data = AsyncMock(
            return_value={
                "city": "minsk",
                "rooms": [2],
            }
        )

        # Act
        await process_price_min(mock_message, mock_state)

        # Assert
        mock_state.update_data.assert_called_once_with(price_min=50000)
        mock_state.set_state.assert_called_once_with(
            SubscriptionStates.waiting_for_confirmation
        )

    @pytest.mark.asyncio
    async def test_process_price_min_invalid(self, mock_message, mock_state):
        """
        Тест: Невалидная минимальная цена (текст).

        Ожидание:
        - Показывается ошибка
        - Предлагается ввести число снова
        """
        # Arrange
        mock_message.text = "not_a_number"
        mock_state.get_data = AsyncMock(return_value={})

        # Act
        await process_price_min(mock_message, mock_state)

        # Assert
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args
        assert "Неверный формат" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_price_min_negative(self, mock_message, mock_state):
        """
        Тест: Отрицательная минимальная цена.

        Ожидание:
        - Показывается ошибка
        """
        # Arrange
        mock_message.text = "-50000"
        mock_state.get_data = AsyncMock(return_value={})

        # Act
        await process_price_min(mock_message, mock_state)

        # Assert
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args
        assert "Неверный формат" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_price_min_no_cancel_handler(self, mock_message, mock_state):
        """
        Тест: process_price_min больше не обрабатывает кнопку отмены.

        Ожидание:
        - При вводе "❌ Отменить" обрабатывается как обычный текст
        - Показывается ошибка валидации (т.к. не число)
        """
        # Arrange
        mock_message.text = "❌ Отменить"

        # Act
        await process_price_min(mock_message, mock_state)

        # Assert - должна быть ошибка валидации
        assert mock_message.answer.called
        assert "❌" in mock_message.answer.call_args[0][0]


class TestPriceMaxInput:
    """Тесты для ввода максимальной цены."""

    @pytest.mark.asyncio
    async def test_process_price_max_valid(self, mock_message, mock_state):
        """
        Тест: Валидная максимальная цена.

        Ожидание:
        - price_max сохраняется
        - Показывается подтверждение
        """
        # Arrange
        mock_message.text = "150000"
        mock_state.get_data = AsyncMock(
            return_value={
                "city": "minsk",
                "rooms": [2],
                "price_min": 50000,
            }
        )

        # Act
        await process_price_max(mock_message, mock_state)

        # Assert
        mock_state.update_data.assert_called_once_with(price_max=150000)
        mock_state.set_state.assert_called_once_with(
            SubscriptionStates.waiting_for_confirmation
        )

    @pytest.mark.asyncio
    async def test_process_price_max_less_than_min(self, mock_message, mock_state):
        """
        Тест: Максимальная цена меньше минимальной.

        Ожидание:
        - Показывается ошибка
        - Предлагается ввести снова
        """
        # Arrange
        mock_message.text = "30000"  # Меньше price_min=50000
        mock_state.get_data = AsyncMock(
            return_value={
                "city": "minsk",
                "rooms": [2],
                "price_min": 50000,
            }
        )

        # Act
        await process_price_max(mock_message, mock_state)

        # Assert
        assert mock_message.answer.called
        call_args = mock_message.answer.call_args
        assert "должна быть больше" in call_args[0][0]


class TestConfirmSubscription:
    """Тесты для подтверждения подписки."""

    @pytest.mark.asyncio
    async def test_confirm_subscription_created(
        self,
        mock_callback_query,
        mock_state,
        mock_session,
        mock_telegram_user,
        mock_subscription,
    ):
        """
        Тест: Подтверждение создаёт подписку.

        Ожидание:
        - Получается пользователь
        - Создаётся подписка
        - state очищается
        - Показывается сообщение об успехе
        """
        # Arrange
        callback_data = SubscriptionActionCallback(action="confirm")
        mock_state.get_data = AsyncMock(
            return_value={
                "city": "minsk",
                "rooms": [2],
                "price_min": 50000,
                "price_max": 150000,
            }
        )

        mock_service = AsyncMock()
        mock_service.get_user_by_telegram_id = AsyncMock(
            return_value=mock_telegram_user
        )
        mock_service.create_subscription = AsyncMock(return_value=mock_subscription)

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await confirm_subscription(
                mock_callback_query, callback_data, mock_state, mock_session
            )

            # Assert
            mock_service.get_user_by_telegram_id.assert_called_once()
            mock_service.create_subscription.assert_called_once_with(
                user_id=mock_telegram_user.id,
                city="minsk",
                rooms=[2],
                price_min=50000,
                price_max=150000,
                currency="usd",
            )

            mock_state.clear.assert_called_once()
            assert mock_callback_query.message.answer.called

    @pytest.mark.asyncio
    async def test_confirm_subscription_limit_exceeded(
        self, mock_callback_query, mock_state, mock_session, mock_telegram_user
    ):
        """
        Тест: Превышен лимит подписок.

        Ожидание:
        - Вызывается create_subscription с исключением
        - Показывается сообщение о лимите
        - state очищается
        """
        # Arrange
        from app.services.telegram_exceptions import SubscriptionLimitExceeded

        callback_data = SubscriptionActionCallback(action="confirm")
        mock_state.get_data = AsyncMock(
            return_value={
                "city": "minsk",
                "rooms": [2],
            }
        )

        mock_service = AsyncMock()
        mock_service.get_user_by_telegram_id = AsyncMock(
            return_value=mock_telegram_user
        )
        mock_service.create_subscription = AsyncMock(
            side_effect=SubscriptionLimitExceeded(
                user_id=mock_telegram_user.id,
                current_count=5,
                max_count=5,
            )
        )

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await confirm_subscription(
                mock_callback_query, callback_data, mock_state, mock_session
            )

            # Assert
            mock_state.clear.assert_called_once()
            assert mock_callback_query.message.edit_text.called
            call_args = mock_callback_query.message.edit_text.call_args
            assert "Превышен лимит" in call_args[0][0]


class TestCancelSubscription:
    """Тесты для отмены создания подписки."""

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, mock_callback_query, mock_state):
        """
        Тест: Отмена через callback.

        Ожидание:
        - state очищается
        - Показывается сообщение об отмене
        """
        # Arrange
        callback_data = SubscriptionActionCallback(action="cancel")

        # Act
        await cancel_subscription(mock_callback_query, mock_state)

        # Assert
        mock_state.clear.assert_called_once()
        # cancel_flow использует message.answer
        assert mock_callback_query.message.answer.called
        call_args = mock_callback_query.message.answer.call_args
        assert "отменено" in call_args[0][0].lower()


class TestCmdSettings:
    """Тесты для команды /settings."""

    @pytest.mark.asyncio
    async def test_cmd_settings_no_subscriptions(
        self, mock_message, mock_session, mock_telegram_user
    ):
        """
        Тест: /settings без подписок.

        Ожидание:
        - Показывается сообщение что нет подписок
        - Предлагается создать подписку
        """
        # Arrange
        mock_service = AsyncMock()
        mock_service.get_user_by_telegram_id = AsyncMock(
            return_value=mock_telegram_user
        )
        mock_service.get_active_subscriptions = AsyncMock(return_value=[])

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await cmd_settings(mock_message, mock_session)

            # Assert
            assert mock_message.answer.called
            call_args = mock_message.answer.call_args
            assert "нет активных подписок" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_cmd_settings_with_subscriptions(
        self, mock_message, mock_session, mock_telegram_user, mock_subscription
    ):
        """
        Тест: /settings с подписками.

        Ожидание:
        - Показывается список подписок
        - Для каждой подписи есть кнопки редактирования/удаления
        """
        # Arrange
        mock_service = AsyncMock()
        mock_service.get_user_by_telegram_id = AsyncMock(
            return_value=mock_telegram_user
        )
        mock_service.get_active_subscriptions = AsyncMock(
            return_value=[mock_subscription]
        )

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await cmd_settings(mock_message, mock_session)

            # Assert
            assert mock_message.answer.called
            call_args = mock_message.answer.call_args
            settings_text = call_args[0][0]

            assert "подписки" in settings_text.lower()
            assert "Минск" in settings_text


class TestEditSubscription:
    """Тесты для редактирования подписки."""

    @pytest.mark.asyncio
    async def test_edit_subscription(
        self, mock_callback_query, mock_session, mock_subscription, mock_telegram_user
    ):
        """
        Тест: Начать редактирование подписки.

        Ожидание:
        - Получается подписка по ID
        - Проверяется владелец
        - Показываются текущие параметры
        - Предлагается выбрать поле для редактирования
        """
        # Arrange
        callback_data = EditSubscriptionCallback(
            subscription_id=str(mock_subscription.id)
        )
        mock_state = AsyncMock()

        # ВАЖНО: subscription.user_id должен совпадать с user.id
        mock_subscription.user_id = mock_telegram_user.id

        mock_service = AsyncMock()
        mock_service.get_subscription_by_id = AsyncMock(return_value=mock_subscription)
        mock_service.get_user_by_telegram_id = AsyncMock(return_value=mock_telegram_user)

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await edit_subscription(
                mock_callback_query, callback_data, mock_state, mock_session
            )

            # Assert
            mock_service.get_subscription_by_id.assert_called_once()
            mock_service.get_user_by_telegram_id.assert_called_once()
            assert mock_callback_query.message.edit_text.called
            call_args = mock_callback_query.message.edit_text.call_args
            assert "Редактирование" in call_args[0][0]


class TestDeleteSubscription:
    """Тесты для удаления подписки."""

    @pytest.mark.asyncio
    async def test_delete_subscription(
        self, mock_callback_query, mock_session, mock_subscription, mock_telegram_user
    ):
        """
        Тест: Удаление подписки.

        Ожидание:
        - Получается подписка по ID
        - Проверяется владелец
        - Вызывается delete_subscription
        - Показывается сообщение об успехе
        """
        # Arrange
        callback_data = DeleteSubscriptionCallback(
            subscription_id=str(mock_subscription.id)
        )

        # ВАЖНО: subscription.user_id должен совпадать с user.id
        mock_subscription.user_id = mock_telegram_user.id

        mock_service = AsyncMock()
        mock_service.get_subscription_by_id = AsyncMock(return_value=mock_subscription)
        mock_service.get_user_by_telegram_id = AsyncMock(return_value=mock_telegram_user)
        mock_service.delete_subscription = AsyncMock(return_value=True)

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await delete_subscription(mock_callback_query, callback_data, mock_session)

            # Assert
            mock_service.get_subscription_by_id.assert_called_once()
            mock_service.get_user_by_telegram_id.assert_called_once()
            mock_service.delete_subscription.assert_called_once_with(
                mock_subscription.id
            )
            assert mock_callback_query.message.edit_text.called
            call_args = mock_callback_query.message.edit_text.call_args
            assert "удалена" in call_args[0][0].lower()


class TestCmdUnsubscribe:
    """Тесты для команды /unsubscribe."""

    @pytest.mark.asyncio
    async def test_cmd_unsubscribe(
        self, mock_message, mock_session, mock_telegram_user, mock_subscription
    ):
        """
        Тест: /unsubscribe отписывает от всех подписок.

        Ожидание:
        - Получаются активные подписки
        - Все подписки деактивируются
        - Показывается сообщение с количеством удалённых
        """
        # Arrange
        mock_service = AsyncMock()
        mock_service.get_user_by_telegram_id = AsyncMock(
            return_value=mock_telegram_user
        )
        mock_service.get_active_subscriptions = AsyncMock(
            return_value=[mock_subscription, mock_subscription]
        )
        mock_service.delete_subscription = AsyncMock(return_value=True)

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await cmd_unsubscribe(mock_message, mock_session)

            # Assert
            mock_service.get_active_subscriptions.assert_called_once()
            assert mock_service.delete_subscription.call_count == 2

            assert mock_message.answer.called
            call_args = mock_message.answer.call_args
            assert "удалены" in call_args[0][0].lower()
            assert "2" in call_args[0][0]


class TestFormatRooms:
    """Тесты для хелпера _format_rooms."""

    def test_format_rooms_none(self):
        """Тест: rooms=None → 'Любые'."""
        assert _format_rooms(None) == "Любые"

    def test_format_rooms_empty_list(self):
        """Тест: rooms=[] → 'Любые'."""
        assert _format_rooms([]) == "Любые"

    def test_format_rooms_5plus(self):
        """Тест: rooms=[5] → '5+ комнат'."""
        assert _format_rooms([5]) == "5+ комнат"

    def test_format_rooms_single(self):
        """Тест: rooms=[1] → '1 комната'."""
        assert _format_rooms([1]) == "1 комната"

    def test_format_rooms_multiple(self):
        """Тест: rooms=[1, 2] → '1 комната, 2 комнаты'."""
        result = _format_rooms([1, 2])
        assert "1 комната" in result
        assert "2 комнаты" in result


class TestOwnerChecks:
    """Тесты для проверки принадлежности подписки пользователю (IDOR protection)."""

    @pytest.mark.asyncio
    async def test_delete_subscription_wrong_owner(
        self, mock_callback_query, mock_session, mock_subscription, mock_telegram_user
    ):
        """
        Тест: Удаление чужой подписки должно быть заблокировано.

        Ожидание:
        - Подписка существует но принадлежит другому пользователю
        - callback.answer вызывается с ошибкой "Это не ваша подписка"
        - delete_subscription НЕ вызывается
        """
        # Arrange — подписка принадлежит ДРУГОМУ пользователю
        other_user_id = uuid4()
        mock_subscription.user_id = other_user_id

        callback_data = DeleteSubscriptionCallback(
            subscription_id=str(mock_subscription.id)
        )

        mock_service = AsyncMock()
        mock_service.get_subscription_by_id = AsyncMock(return_value=mock_subscription)
        mock_service.get_user_by_telegram_id = AsyncMock(return_value=mock_telegram_user)
        mock_service.delete_subscription = AsyncMock(return_value=True)

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await delete_subscription(
                mock_callback_query, callback_data, mock_session
            )

            # Assert — доступ заблокирован
            mock_service.delete_subscription.assert_not_called()
            mock_callback_query.answer.assert_called_once()
            call_args = mock_callback_query.answer.call_args
            assert "не ваша подписка" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_edit_subscription_wrong_owner(
        self, mock_callback_query, mock_session, mock_subscription, mock_telegram_user
    ):
        """
        Тест: Редактирование чужой подписки должно быть заблокировано.

        Ожидание:
        - Подписка существует но принадлежит другому пользователю
        - callback.answer вызывается с ошибкой "Это не ваша подписка"
        - Сообщение об редактировании НЕ показывается
        """
        # Arrange — подписка принадлежит ДРУГОМУ пользователю
        other_user_id = uuid4()
        mock_subscription.user_id = other_user_id

        callback_data = EditSubscriptionCallback(
            subscription_id=str(mock_subscription.id)
        )
        mock_state = AsyncMock()

        mock_service = AsyncMock()
        mock_service.get_subscription_by_id = AsyncMock(return_value=mock_subscription)
        mock_service.get_user_by_telegram_id = AsyncMock(return_value=mock_telegram_user)

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await edit_subscription(
                mock_callback_query, callback_data, mock_state, mock_session
            )

            # Assert — доступ заблокирован
            mock_callback_query.answer.assert_called_once()
            call_args = mock_callback_query.answer.call_args
            assert "не ваша подписка" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_nonexistent_subscription(
        self, mock_callback_query, mock_session
    ):
        """
        Тест: Удаление несуществующей подписки.

        Ожидание:
        - get_subscription_by_id возвращает None
        - callback.answer вызывается с ошибкой "Подписка не найдена"
        """
        # Arrange
        callback_data = DeleteSubscriptionCallback(
            subscription_id=str(uuid4())
        )

        mock_service = AsyncMock()
        mock_service.get_subscription_by_id = AsyncMock(return_value=None)

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await delete_subscription(
                mock_callback_query, callback_data, mock_session
            )

            # Assert
            mock_callback_query.answer.assert_called_once()
            call_args = mock_callback_query.answer.call_args
            assert "не найдена" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_edit_nonexistent_subscription(
        self, mock_callback_query, mock_session
    ):
        """
        Тест: Редактирование несуществующей подписки.

        Ожидание:
        - get_subscription_by_id возвращает None
        - callback.answer вызывается с ошибкой "Подписка не найдена"
        """
        # Arrange
        callback_data = EditSubscriptionCallback(
            subscription_id=str(uuid4())
        )
        mock_state = AsyncMock()

        mock_service = AsyncMock()
        mock_service.get_subscription_by_id = AsyncMock(return_value=None)

        with patch(
            "app.telegram.handlers.subscriptions.TelegramSubscriptionService",
            return_value=mock_service,
        ):
            # Act
            await edit_subscription(
                mock_callback_query, callback_data, mock_state, mock_session
            )

            # Assert
            mock_callback_query.answer.assert_called_once()
            call_args = mock_callback_query.answer.call_args
            assert "не найдена" in call_args[0][0]
