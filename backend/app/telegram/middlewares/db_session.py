"""
Middleware для передачи db_session в обработчики.

Этот middleware автоматически создаёт и закрывает сессию базы данных
для каждого обновления (update) от Telegram.

Пример использования:
    # В bot.py:
    from app.telegram.middlewares.db_session import DbSessionMiddleware
    from app.db.database import async_session_pool

    dp.update.middleware(DbSessionMiddleware(async_session_pool))

    # В обработчике:
    @router.message(CommandStart())
    async def cmd_start(message: types.Message, session: AsyncSession):
        # session автоматически передан из middleware
        pass
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware для автоматического управления сессией БД.

    Создаёт новую сессию для каждого update и передаёт её
    в обработчики через data["session"].
    """

    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        """
        Инициализирует middleware.

        Args:
            session_pool: Фабрика сессий SQLAlchemy
        """
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        """
        Вызывается для каждого update от Telegram.

        Создаёт сессию, передаёт её в обработчик и закрывает после.

        Args:
            handler: Обработчик события
            event: Событие от Telegram (update)
            data: Словарь с данными (message, callback_query, etc.)

        Returns:
            Результат работы обработчика
        """
        async with self.session_pool() as session:
            data["session"] = session
            logger.debug(f"DB session opened for event type: {type(event).__name__}")

            try:
                result = await handler(event, data)
                await session.commit()
                logger.debug("DB session committed successfully")
                return result
            except Exception as e:
                await session.rollback()
                logger.error(f"DB session rolled back: {e}")
                raise
