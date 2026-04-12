"""
Telegram Bot — инициализация и запуск.

Модуль предоставляет функции для создания экземпляров Bot и Dispatcher,
а также для запуска бота в polling режиме.

Пример использования:
    from app.telegram import start_bot

    # Запуск бота
    await start_bot()
"""

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.telegram.middlewares.db_session import DbSessionMiddleware
from app.db.database import async_session_maker

from loguru import logger


def create_bot() -> Bot:
    """
    Создать экземляр бота с настройками по умолчанию.

    Returns:
        Настроенный экземпляр Bot
    """
    return Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """
    Создать dispatcher с зарегистрированными роутерами и middleware.

    Returns:
        Настроенный экземпляр Dispatcher
    """
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем middleware для передачи db_session
    dp.update.middleware(DbSessionMiddleware(async_session_maker))

    # Импортируем и регистрируем роутеры
    from app.telegram.handlers.commands import router as commands_router
    from app.telegram.handlers.subscriptions import (
        router as subscriptions_router,
    )

    dp.include_router(commands_router)
    dp.include_router(subscriptions_router)

    logger.info("Telegram dispatcher initialized with all routers")
    return dp


async def start_bot():
    """
    Запустить бота в polling режиме.

    Если бот не включён (TELEGRAM_BOT_ENABLED=False), функция возвращает
    управление немедленно.
    """
    if not settings.TELEGRAM_BOT_ENABLED:
        logger.info("Telegram bot is disabled, skipping startup")
        return

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is not set, cannot start bot")
        return

    logger.info("Starting Telegram bot in polling mode...")

    bot = create_bot()
    dp = create_dispatcher()

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Telegram bot polling error: {e}")
    finally:
        await bot.session.close()
        logger.info("Telegram bot stopped")
