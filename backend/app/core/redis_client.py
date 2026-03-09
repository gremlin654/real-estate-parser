"""
Redis клиент для Kufar Monitor.

Реализует Singleton паттерн для подключения к Redis через redis.asyncio.
Обеспечивает правильное управление соединением, обработку ошибок и graceful shutdown.

Использование:
    from app.core.redis_client import get_redis, close_redis, RedisClient

    # Получить подключение
    redis = get_redis()
    await redis.set("key", "value")

    # Закрыть подключение (при shutdown)
    await close_redis()
"""

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from loguru import logger
from typing import Optional

from app.config import settings


class RedisClient:
    """
    Singleton класс для управления подключением к Redis.

    Атрибуты:
        _instance: Единственный экземпляр класса
        _redis: Redis подключение
        _is_connected: Флаг состояния подключения
    """

    _instance: Optional["RedisClient"] = None
    _redis: Optional[Redis] = None
    _is_connected: bool = False

    def __new__(cls) -> "RedisClient":
        """Создаёт или возвращает существующий экземпляр (Singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, url: Optional[str] = None) -> None:
        """
        Устанавливает подключение к Redis.

        Args:
            url: Redis URL (по умолчанию из settings.REDIS_URL)

        Raises:
            RedisError: Ошибка подключения к Redis
        """
        if self._is_connected and self._redis:
            logger.debug("Redis connection already established")
            return

        redis_url = url or settings.REDIS_URL

        try:
            logger.info(f"Connecting to Redis: {redis_url}")

            self._redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Проверка подключения
            await self._redis.ping()
            self._is_connected = True

            logger.info("Successfully connected to Redis")

        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._is_connected = False
            raise
        except TimeoutError as e:
            logger.error(f"Redis connection timeout: {e}")
            self._is_connected = False
            raise
        except RedisError as e:
            logger.error(f"Redis error: {e}")
            self._is_connected = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self._is_connected = False
            raise

    async def close(self) -> None:
        """
        Закрывает подключение к Redis (graceful shutdown).
        """
        if self._redis:
            try:
                logger.info("Closing Redis connection...")
                await self._redis.close()
                self._is_connected = False
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._redis = None

    def get_client(self) -> Optional[Redis]:
        """
        Возвращает Redis клиент.

        Returns:
            Redis клиент или None если не подключено

        Raises:
            RedisError: Если подключение не установлено
        """
        if not self._is_connected or not self._redis:
            raise RedisError("Redis is not connected. Call connect() first.")
        return self._redis

    @property
    def is_connected(self) -> bool:
        """Проверяет статус подключения."""
        return self._is_connected

    async def health_check(self) -> bool:
        """
        Проверяет здоровье Redis подключения.

        Returns:
            True если подключение активно, иначе False
        """
        if not self._redis or not self._is_connected:
            return False

        try:
            await self._redis.ping()
            return True
        except Exception:
            return False


# Глобальный экземпляр
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Возвращает singleton экземпляр RedisClient.

    Returns:
        Экземпляр RedisClient
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


async def get_redis() -> Redis:
    """
    Возвращает Redis подключение, создавая его если необходимо.

    Это основная функция для получения Redis подключения в приложении.
    Автоматически создаёт подключение если оно ещё не существует.

    Returns:
        Redis подключение

    Raises:
        RedisError: Если не удалось подключиться к Redis

    Example:
        redis = await get_redis()
        await redis.set("key", "value")
        value = await redis.get("key")
    """
    client = get_redis_client()

    if not client.is_connected:
        await client.connect()

    return client.get_client()


async def close_redis() -> None:
    """
    Закрывает Redis подключение (graceful shutdown).

    Вызывается при остановке приложения в lifespan shutdown.

    Example:
        await close_redis()
    """
    client = get_redis_client()
    await client.close()


async def health_check_redis() -> bool:
    """
    Проверяет здоровье Redis подключения.

    Returns:
        True если Redis доступен, иначе False

    Example:
        if await health_check_redis():
            logger.info("Redis is healthy")
        else:
            logger.warning("Redis is not healthy")
    """
    client = get_redis_client()
    return await client.health_check()
