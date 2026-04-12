"""
Обработчики базовых команд Telegram бота.

Реализует обработчики для команд:
- /start — регистрация пользователя
- /help — справка по командам
- /stop — отписка от уведомлений

Все обработчики используют middleware для получения db_session.
"""

from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardRemove
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.telegram_subscription_service import TelegramSubscriptionService
from app.telegram.keyboards.reply import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    """
    Обработчик команды /start — регистрация пользователя.

    Создаёт или получает пользователя Telegram,
    затем показывает приветственное сообщение с основной клавиатурой.

    Response:
        🏠 Добро пожаловать в Kufar Monitor!

        Я буду уведомлять вас о новых квартирах.

        Команды:
        • /subscribe — создать подписку
        • /settings — мои подписки
        • /help — справка
        • /stop — отписаться
    """
    logger.info(f"User {message.from_user.id} sent /start command")

    # Создаём или получаем пользователя (идемпотентно)
    service = TelegramSubscriptionService(session)
    user = await service.create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code or "ru",
    )

    # Если пользователь был деактивирован — активируем
    if not user.is_active:
        await service.activate_user(user.id)
        logger.info(f"Reactivated user {user.id}")

    # Формируем приветственное сообщение
    first_name = message.from_user.first_name or "пользователь"
    welcome_text = (
        f"🏠 <b>Добро пожаловать в Kufar Monitor, {first_name}!</b>\n\n"
        f"Я буду уведомлять вас о новых квартирах на Kufar.by.\n\n"
        f"<b>Доступные команды:</b>\n"
        f"• /subscribe — создать подписку на новые квартиры\n"
        f"• /settings — мои подписки и их редактирование\n"
        f"• /help — справка по боту\n"
        f"• /stop — отписаться от уведомлений"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
    )

    logger.info(f"User {message.from_user.id} registered/activated: user_id={user.id}")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """
    Обработчик команды /help — справка по командам бота.

    Показывает подробное описание всех доступных команд
    и как ими пользоваться.

    Response:
        📖 Справка по командам бота

        /start — Начать работу с ботом
        /subscribe — Создать новую подписку
        /settings — Посмотреть/изменить подписки
        /unsubscribe — Отписаться от всех подписок
        /help — Эта справка
        /stop — Отписаться от уведомлений
    """
    logger.info(f"User {message.from_user.id} sent /help command")

    help_text = (
        f"📖 <b>Справка по командам бота</b>\n\n"
        f"<b>Основные команды:</b>\n"
        f"• /start — Начать работу с ботом\n"
        f"• /subscribe — Создать новую подписку на квартиры\n"
        f"• /settings — Посмотреть и изменить свои подписки\n"
        f"• /unsubscribe — Отписаться от всех подписок\n"
        f"• /help — Эта справка\n"
        f"• /stop — Отписаться от уведомлений (деактивировать)\n\n"
        f"<b>Как создать подписку:</b>\n"
        f"1. Отправьте /subscribe\n"
        f"2. Выберите город\n"
        f"3. Выберите количество комнат\n"
        f"4. Укажите минимальную цену (или пропустите)\n"
        f"5. Укажите максимальную цену (или пропустите)\n"
        f"6. Подтвердите подписку\n\n"
        f"<b>Пример:</b>\n"
        f"Вы получите уведомление когда появится квартира:\n"
        f"• В Минске\n"
        f"• 2 комнаты\n"
        f"• Цена: $50,000-$100,000"
    )

    await message.answer(help_text)

    logger.info(f"Help sent to user {message.from_user.id}")


@router.message(Command("stop"))
async def cmd_stop(message: types.Message, session: AsyncSession):
    """
    Обработчик команды /stop — деактивация пользователя.

    Деактивирует пользователя (is_active=False) и удаляет клавиатуру.
    Пользователь перестанет получать уведомления.

    Response:
        ❌ Вы отписались от уведомлений.

        Вы больше не будете получать уведомления о новых квартирах.
        Для возврата используйте /start
    """
    logger.info(f"User {message.from_user.id} sent /stop command")

    service = TelegramSubscriptionService(session)
    user = await service.get_user_by_telegram_id(message.from_user.id)

    if not user:
        # Пользователь не зарегистрирован
        await message.answer(
            "❌ Вы не зарегистрированы в системе.\n\n"
            "Используйте /start для регистрации.",
        )
        logger.warning(f"User {message.from_user.id} tried /stop but not registered")
        return

    # Деактивируем пользователя
    await service.deactivate_user(user.id)

    stop_text = (
        f"❌ <b>Вы отписались от уведомлений</b>\n\n"
        f"Вы больше не будете получать уведомления о новых квартирах.\n"
        f"Все ваши подписки деактивированы.\n\n"
        f"Для возврата используйте /start"
    )

    await message.answer(
        stop_text,
        reply_markup=ReplyKeyboardRemove(),
    )

    logger.info(f"User {message.from_user.id} deactivated: user_id={user.id}")
