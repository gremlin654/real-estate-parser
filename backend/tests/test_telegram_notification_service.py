"""
Unit тесты для TelegramNotificationService.

Тестирует сервис отправки уведомлений в Telegram с моками
для внешних зависимостей (aiogram Bot, database).

Запуск:
    cd backend
    python -m pytest tests/test_telegram_notification_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4
from datetime import datetime

from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramRetryAfter,
    TelegramNetworkError,
)

from app.services.telegram_notification_service import TelegramNotificationService
from app.models.listing import Listing, ListingStatus
from app.models.telegram_user import (
    TelegramUser,
    TelegramSubscription,
    TelegramNotificationLog,
    TelegramNotificationStatus,
)


@pytest.fixture
def mock_db_session():
    """Создает мокированную сессию базы данных."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_bot():
    """Создает мокированный Telegram Bot."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.close = AsyncMock()
    return bot


@pytest.fixture
def test_user():
    """Создает тестового пользователя."""
    return TelegramUser(
        id=uuid4(),
        telegram_id=12345678,
        username="test_user",
        first_name="Test",
        is_active=True,
        blocked_by_user=False,
    )


@pytest.fixture
def test_subscription(test_user):
    """Создает тестовую подписку."""
    return TelegramSubscription(
        id=uuid4(),
        user_id=test_user.id,
        city="minsk",
        rooms=[1, 2],
        price_min=30000,
        price_max=60000,
        currency="usd",
        is_active=True,
    )


@pytest.fixture
def test_listing():
    """Создает тестовое объявление."""
    return Listing(
        id=uuid4(),
        kufar_id="test_123",
        url="https://re.kufar.by/vi/minsk/kupit/kvartiru/123",
        title="Test Apartment",
        price=150000,
        price_usd=46000,
        currency="BYN",
        city="minsk",
        address="ул. Тестовая, д. 1",
        rooms=2,
        area=55.5,
        floor=5,
        total_floors=9,
        status=ListingStatus.new,
        first_seen_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        images=["https://example.com/image1.jpg"],
        price_per_m2_byn=2702.70,
        price_per_m2_usd=836.36,
    )


@pytest.fixture
def notification_service(mock_db_session, mock_bot):
    """Создает сервис с мокированными зависимостями."""
    with patch(
        "app.services.telegram_notification_service.settings"
    ) as mock_settings, patch(
        "app.services.telegram_notification_service.Bot"
    ) as MockBot, patch(
        "app.services.telegram_notification_service.TelegramSubscriptionService"
    ) as MockSubService:

        # Настраиваем моки
        mock_settings.TELEGRAM_BOT_ENABLED = True
        mock_settings.TELEGRAM_BOT_TOKEN = "test:token"
        mock_settings.TELEGRAM_MAX_RETRIES = 3
        mock_settings.TELEGRAM_RETRY_DELAY_SECONDS = 0.01  # Быстрые тесты

        MockBot.return_value = mock_bot

        # Мокаем subscription service
        mock_sub_service = AsyncMock()
        mock_sub_service.get_matching_subscriptions = AsyncMock(return_value=[])
        mock_sub_service.get_user_by_id = AsyncMock(return_value=None)
        MockSubService.return_value = mock_sub_service

        # Создаем сервис
        service = TelegramNotificationService(mock_db_session)
        service.bot = mock_bot
        service.subscription_service = mock_sub_service

        yield service


class TestSendNewListingsNoSubscriptions:
    """Тесты отправки когда нет подходящих подписок."""

    @pytest.mark.asyncio
    async def test_send_new_listings_no_subscriptions(
        self, notification_service, test_listing
    ):
        """Тест: объявления без подписок пропускаются."""
        notification_service.subscription_service.get_matching_subscriptions.return_value = (
            []
        )

        result = await notification_service.send_new_listings_notifications(
            [test_listing]
        )

        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["blocked"] == 0
        assert result["rate_limited"] == 0
        assert result["skipped_no_match"] == 1

    @pytest.mark.asyncio
    async def test_send_new_listings_bot_not_configured(
        self, mock_db_session, test_listing
    ):
        """Тест: когда бот не настроен, все пропускаются."""
        with patch(
            "app.services.telegram_notification_service.settings"
        ) as mock_settings, patch(
            "app.services.telegram_notification_service.TelegramSubscriptionService"
        ) as MockSubService:

            mock_settings.TELEGRAM_BOT_ENABLED = False
            mock_settings.TELEGRAM_BOT_TOKEN = ""

            service = TelegramNotificationService(mock_db_session)
            service.subscription_service = AsyncMock()

            result = await service.send_new_listings_notifications([test_listing])

            assert result["sent"] == 0
            assert result["skipped_no_match"] == 1


class TestSendNewListingsWithMatches:
    """Тесты отправки когда есть подходящие подписки."""

    @pytest.mark.asyncio
    async def test_send_new_listings_with_matches(
        self, notification_service, test_listing, test_user, test_subscription
    ):
        """Тест: успешная отправка уведомлений с matching подписками."""
        notification_service.subscription_service.get_matching_subscriptions.return_value = [
            test_subscription
        ]
        notification_service.subscription_service.get_user_by_id.return_value = (
            test_user
        )

        # Мокаем send_listing_to_user
        with patch.object(
            notification_service, "send_listing_to_user", return_value="sent"
        ) as mock_send:
            result = await notification_service.send_new_listings_notifications(
                [test_listing]
            )

            mock_send.assert_called_once_with(
                test_user, test_listing, test_subscription
            )
            assert result["sent"] == 1
            assert result["skipped_no_match"] == 0

    @pytest.mark.asyncio
    async def test_send_new_listings_blocked_user(
        self, notification_service, test_listing, test_subscription
    ):
        """Тест: заблокированные пользователи пропускаются."""
        blocked_user = TelegramUser(
            id=uuid4(),
            telegram_id=87654321,
            username="blocked_user",
            is_active=True,
            blocked_by_user=True,
        )

        notification_service.subscription_service.get_matching_subscriptions.return_value = [
            test_subscription
        ]
        notification_service.subscription_service.get_user_by_id.return_value = (
            blocked_user
        )

        result = await notification_service.send_new_listings_notifications(
            [test_listing]
        )

        assert result["sent"] == 0
        assert result["skipped_no_match"] == 0

    @pytest.mark.asyncio
    async def test_send_new_listings_inactive_user(
        self, notification_service, test_listing, test_subscription
    ):
        """Тест: неактивные пользователи пропускаются."""
        inactive_user = TelegramUser(
            id=uuid4(),
            telegram_id=87654321,
            username="inactive_user",
            is_active=False,
            blocked_by_user=False,
        )

        notification_service.subscription_service.get_matching_subscriptions.return_value = [
            test_subscription
        ]
        notification_service.subscription_service.get_user_by_id.return_value = (
            inactive_user
        )

        result = await notification_service.send_new_listings_notifications(
            [test_listing]
        )

        assert result["sent"] == 0
        assert result["skipped_no_match"] == 0

    @pytest.mark.asyncio
    async def test_send_new_listings_user_not_found(
        self, notification_service, test_listing, test_subscription
    ):
        """Тест: когда пользователь не найден, подписка пропускается."""
        notification_service.subscription_service.get_matching_subscriptions.return_value = [
            test_subscription
        ]
        notification_service.subscription_service.get_user_by_id.return_value = None

        result = await notification_service.send_new_listings_notifications(
            [test_listing]
        )

        # Пользователь не найден — подписка пропускается без ошибки
        assert result["failed"] == 0
        assert result["sent"] == 0
        assert result["skipped_no_match"] == 0

    @pytest.mark.asyncio
    async def test_send_new_listings_multiple_subscriptions(
        self, notification_service, test_listing, test_user
    ):
        """Тест: несколько подписок на одно объявление."""
        subscriptions = [
            TelegramSubscription(
                id=uuid4(),
                user_id=test_user.id,
                city="minsk",
                rooms=[1],
                is_active=True,
            ),
            TelegramSubscription(
                id=uuid4(),
                user_id=test_user.id,
                city="minsk",
                rooms=[2],
                is_active=True,
            ),
        ]

        notification_service.subscription_service.get_matching_subscriptions.return_value = (
            subscriptions
        )
        notification_service.subscription_service.get_user_by_id.return_value = (
            test_user
        )

        with patch.object(
            notification_service, "send_listing_to_user", return_value="sent"
        ) as mock_send:
            result = await notification_service.send_new_listings_notifications(
                [test_listing]
            )

            assert mock_send.call_count == 2
            assert result["sent"] == 2


class TestSendListingToUser:
    """Тесты отправки одного объявления пользователю."""

    @pytest.mark.asyncio
    async def test_send_listing_to_user_success(
        self, notification_service, test_user, test_listing, test_subscription, mock_bot
    ):
        """Тест: успешная отправка сообщения."""
        mock_message = AsyncMock()
        mock_message.message_id = 12345
        mock_bot.send_message.return_value = mock_message

        # Мокаем _log_notification
        with patch.object(
            notification_service, "_log_notification", new_callable=AsyncMock
        ) as mock_log:
            with patch.object(
                notification_service, "_send_message_with_photo", return_value=12345
            ) as mock_send:
                result = await notification_service.send_listing_to_user(
                    test_user, test_listing, test_subscription
                )

                assert result == "sent"
                mock_send.assert_called_once()
                mock_log.assert_called_once()
                assert mock_log.call_args.kwargs["status"] == "sent"
                assert mock_log.call_args.kwargs["message_id"] == 12345

    @pytest.mark.asyncio
    async def test_send_listing_to_user_with_photo(
        self, notification_service, test_user, test_listing, test_subscription, mock_bot
    ):
        """Тест: отправка с фото."""
        with patch.object(
            notification_service, "_log_notification", new_callable=AsyncMock
        ):
            with patch.object(
                notification_service, "_send_message_with_photo", return_value=12346
            ) as mock_send_photo:
                result = await notification_service.send_listing_to_user(
                    test_user, test_listing, test_subscription
                )

                assert result == "sent"
                mock_send_photo.assert_called_once()
                # Проверяем что фото было передано
                call_args = mock_send_photo.call_args[0]
                assert (
                    call_args[3] == "https://example.com/image1.jpg"
                )  # image_url argument

    @pytest.mark.asyncio
    async def test_send_listing_to_user_forbidden(
        self, notification_service, test_user, test_listing, test_subscription
    ):
        """Тест: пользователь заблокировал бота."""
        # Мокаем _send_message_with_photo чтобы вызывать ForbiddenError
        with patch.object(
            notification_service,
            "_send_message_with_photo",
            side_effect=TelegramForbiddenError(
                method=MagicMock(), message="Forbidden: bot was blocked by the user"
            ),
        ):
            result = await notification_service.send_listing_to_user(
                test_user, test_listing, test_subscription
            )

            assert result == "blocked"
            assert test_user.blocked_by_user == True
            # Commit вызывается минимум 1 раз (для обновления blocked_by_user и для логирования)
            notification_service.db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_send_listing_to_user_network_error(
        self, notification_service, test_user, test_listing, test_subscription
    ):
        """Тест: сетевая ошибка при отправке."""
        # Мокаем _send_message_with_photo чтобы вызывать NetworkError
        with patch.object(
            notification_service,
            "_send_message_with_photo",
            side_effect=TelegramNetworkError(
                method=MagicMock(), message="Connection error"
            ),
        ):
            with patch.object(
                notification_service, "_log_notification", new_callable=AsyncMock
            ) as mock_log:
                result = await notification_service.send_listing_to_user(
                    test_user, test_listing, test_subscription
                )

                assert result == "failed"
                mock_log.assert_called_once()
                assert mock_log.call_args.kwargs["status"] == "failed"


class TestRetryWithBackoff:
    """Тесты retry логики с exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success_first_try(
        self, notification_service, mock_bot
    ):
        """Тест: успешное выполнение с первой попытки."""
        mock_func = AsyncMock(return_value="success")

        result = await notification_service._retry_with_backoff(
            mock_func, "arg1", kwarg1="value1"
        )

        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success_after_retries(self, notification_service):
        """Тест: успешное выполнение после нескольких retry."""
        mock_func = AsyncMock()
        mock_func.side_effect = [
            TelegramNetworkError(method=MagicMock(), message="Error 1"),
            TelegramNetworkError(method=MagicMock(), message="Error 2"),
            "success",
        ]

        result = await notification_service._retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_max_retries_exceeded(self, notification_service):
        """Тест: превышение максимального количества retry."""
        mock_func = AsyncMock(
            side_effect=TelegramNetworkError(
                method=MagicMock(), message="Persistent error"
            )
        )

        with pytest.raises(TelegramNetworkError):
            await notification_service._retry_with_backoff(mock_func)

        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_forbidden_no_retry(self, notification_service):
        """Тест: ForbiddenError не retry-ится."""
        mock_func = AsyncMock(
            side_effect=TelegramForbiddenError(method=MagicMock(), message="Forbidden")
        )

        with pytest.raises(TelegramForbiddenError):
            await notification_service._retry_with_backoff(mock_func)

        # Вызвана только 1 раз (без retry)
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_with_backoff_rate_limit_exceeded(self, notification_service):
        """
        Тест: RateLimit после max_retries должен вызывать NotificationSendError.

        Ожидание:
        - TelegramRetryAfter повторяется 3 раза (max_retries)
        - На 3-й попытке вызывается NotificationSendError
        - Функция вызвана ровно 3 раза
        """
        from app.services.telegram_exceptions import NotificationSendError

        mock_func = AsyncMock(
            side_effect=TelegramRetryAfter(
                method=MagicMock(), message="Rate limited", retry_after=10
            )
        )

        with pytest.raises(NotificationSendError, match="Rate limited after 3 attempts"):
            await notification_service._retry_with_backoff(mock_func)

        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_max_wait_capped_at_60s(
        self, notification_service
    ):
        """
        Тест: TelegramRetryAfter с retry_after > 60s должен ждать максимум 60s.

        Ожидание:
        - retry_after=300 (5 минут) но ждать должен максимум 60s
        - Функция должна вызвать asyncio.sleep с wait_time <= 60
        - После max_retries вызывается NotificationSendError
        """
        from app.services.telegram_exceptions import NotificationSendError

        mock_func = AsyncMock(
            side_effect=TelegramRetryAfter(
                method=MagicMock(), message="Rate limited", retry_after=300
            )
        )

        with patch(
            "app.services.telegram_notification_service.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            with pytest.raises(NotificationSendError):
                await notification_service._retry_with_backoff(mock_func)

            # Все sleep вызовы должны быть <= 60 секунд
            for call in mock_sleep.call_args_list:
                wait_time = call[0][0]
                assert wait_time <= 60, f"Wait time {wait_time}s exceeds 60s cap"


class TestHandleSendError:
    """Тесты обработки ошибок отправки."""

    @pytest.mark.asyncio
    async def test_handle_send_error_forbidden(self, notification_service, test_user):
        """Тест: обработка ForbiddenError."""
        error = TelegramForbiddenError(method=MagicMock(), message="Bot blocked")

        result = await notification_service._handle_send_error(error, test_user)

        assert result == "blocked"
        assert test_user.blocked_by_user == True

    @pytest.mark.asyncio
    async def test_handle_send_error_retry_after(self, notification_service, test_user):
        """Тест: обработка RetryAfter."""
        error = TelegramRetryAfter(
            method=MagicMock(), message="Rate limited", retry_after=30
        )

        result = await notification_service._handle_send_error(error, test_user)

        assert result == "rate_limited"

    @pytest.mark.asyncio
    async def test_handle_send_error_network(self, notification_service, test_user):
        """Тест: обработка NetworkError."""
        error = TelegramNetworkError(method=MagicMock(), message="Connection timeout")

        result = await notification_service._handle_send_error(error, test_user)

        assert result == "retry"

    @pytest.mark.asyncio
    async def test_handle_send_error_unknown(self, notification_service, test_user):
        """Тест: обработка неизвестной ошибки."""
        error = ValueError("Some unexpected error")

        result = await notification_service._handle_send_error(error, test_user)

        assert result == "failed"


class TestFormatListingMessage:
    """Тесты форматирования сообщения."""

    @pytest.mark.asyncio
    async def test_format_listing_message(
        self, notification_service, test_listing, test_subscription
    ):
        """Тест: форматирование сообщения с объявлением."""
        message = notification_service._format_listing_message(
            test_listing, test_subscription
        )

        assert "🏠 Новая квартира в 🏙️ Минск!" in message
        assert "📍 Адрес: ул. Тестовая, д. 1" in message
        assert "🚪 Комнат: 2 комнаты" in message
        assert "📐 Площадь: 55.5 м²" in message
        assert "🏢 Этаж: 5/9" in message
        assert "💰 Цена:" in message
        assert "📊 Цена за м²:" in message
        assert "🔗 https://re.kufar.by/vi/minsk/kupit/kvartiru/123" in message


class TestBuildListingKeyboard:
    """Тесты создания inline клавиатуры."""

    def test_build_listing_keyboard(self, notification_service, test_listing):
        """Тест: клавиатура содержит правильные кнопки."""
        keyboard = notification_service._build_listing_keyboard(test_listing)

        assert len(keyboard.inline_keyboard) == 2

        # Первая кнопка - URL
        url_button = keyboard.inline_keyboard[0][0]
        assert url_button.text == "🔗 Открыть на Kufar"
        assert url_button.url == test_listing.url

        # Вторая кнопка - callback
        callback_button = keyboard.inline_keyboard[1][0]
        assert callback_button.text == "⚙️ Настройки уведомлений"
        assert callback_button.callback_data == "settings"


class TestLogNotification:
    """Тесты логирования уведомлений."""

    @pytest.mark.asyncio
    async def test_log_notification_success(self, notification_service):
        """Тест: успешное логирование уведомления."""
        user_id = uuid4()
        listing_id = uuid4()
        subscription_id = uuid4()

        await notification_service._log_notification(
            user_id=user_id,
            listing_id=listing_id,
            subscription_id=subscription_id,
            status="sent",
            message_id=12345,
        )

        # Проверяем что add был вызван
        notification_service.db.add.assert_called_once()
        log_entry = notification_service.db.add.call_args[0][0]

        assert isinstance(log_entry, TelegramNotificationLog)
        assert log_entry.user_id == user_id
        assert log_entry.listing_id == listing_id
        assert log_entry.subscription_id == subscription_id
        assert log_entry.status == TelegramNotificationStatus.sent
        assert log_entry.response_message_id == 12345
        assert log_entry.retry_count == 0

    @pytest.mark.asyncio
    async def test_log_notification_with_error(self, notification_service):
        """Тест: логирование с ошибкой."""
        user_id = uuid4()
        listing_id = uuid4()
        subscription_id = uuid4()

        await notification_service._log_notification(
            user_id=user_id,
            listing_id=listing_id,
            subscription_id=subscription_id,
            status="failed",
            error_message="Connection timeout",
            retry_count=2,
        )

        log_entry = notification_service.db.add.call_args[0][0]

        assert log_entry.status == TelegramNotificationStatus.failed
        assert log_entry.error_message == "Connection timeout"
        assert log_entry.retry_count == 2

    @pytest.mark.asyncio
    async def test_log_notification_db_error(self, notification_service):
        """Тест: обработка ошибки при логировании."""
        notification_service.db.commit.side_effect = Exception("DB error")

        # Не должно вызывать исключение
        await notification_service._log_notification(
            user_id=uuid4(),
            listing_id=uuid4(),
            subscription_id=uuid4(),
            status="sent",
        )

        # Проверяем что был вызван rollback
        notification_service.db.rollback.assert_called_once()


class TestClose:
    """Тесты закрытия соединения."""

    @pytest.mark.asyncio
    async def test_close(self, notification_service, mock_bot):
        """Тест: закрытие bot connection."""
        await notification_service.close()

        mock_bot.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_bot(self, mock_db_session):
        """Тест: закрытие без bot (не должно вызывать ошибок)."""
        with patch(
            "app.services.telegram_notification_service.settings"
        ) as mock_settings, patch(
            "app.services.telegram_notification_service.TelegramSubscriptionService"
        ) as MockSubService:

            mock_settings.TELEGRAM_BOT_ENABLED = False
            mock_settings.TELEGRAM_BOT_TOKEN = ""
            MockSubService.return_value = AsyncMock()

            service = TelegramNotificationService(mock_db_session)

            # Не должно вызывать ошибок
            await service.close()
