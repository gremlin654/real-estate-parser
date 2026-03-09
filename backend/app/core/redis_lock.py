"""
Redis Distributed Lock для Kufar Monitor.

Реализует распределённую блокировку с использованием Redis для предотвращения
дублирования сканирования городов при параллельных запросах и рестартах backend.

Features:
- SETNX для атомарного захвата блокировки
- TTL для авто-экспайр при крэше процесса
- Проверка owner для безопасного релиза (не освободить чужой lock)
- Async поддержка через redis.asyncio
- Context manager для удобного использования

Пример использования:
    from app.core.redis_lock import RedisLock
    from app.core.redis_client import get_redis

    redis_client = await get_redis()
    lock = RedisLock(redis_client, "lock:scan:minsk", timeout=3600)

    if await lock.acquire():
        try:
            # Критическая секция - сканирование
            await run_scan()
        finally:
            await lock.release()

    # Или через context manager:
    async with RedisLock(redis_client, "lock:scan:minsk", timeout=3600) as lock:
        await run_scan()
"""

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError
from typing import Optional
import time
import uuid

from loguru import logger


class RedisLockError(Exception):
    """Исключение при ошибках работы с Redis lock."""

    pass


class RedisLock:
    """
    Distributed lock implementation using Redis.

    Атомарный захват блокировки через SETNX с TTL для защиты от вечных блокировок.
    Проверка owner при релизе предотвращает освобождение чужой блокировки.

    Attributes:
        redis: Redis клиент
        lock_name: Имя блокировки (ключ в Redis)
        timeout: TTL блокировки в секундах (default: 3600)
        lock_value: Уникальное значение блокировки (owner identifier)

    Example:
        redis_client = await get_redis()
        lock = RedisLock(redis_client, "lock:scan:minsk", timeout=3600)

        acquired = await lock.acquire()
        if acquired:
            try:
                # Критическая секция
                await process()
            finally:
                await lock.release()
    """

    def __init__(
        self,
        redis_client: Redis,
        lock_name: str,
        timeout: int = 3600,
    ):
        """
        Инициализация Redis lock.

        Args:
            redis_client: Redis клиент (redis.asyncio.Redis)
            lock_name: Имя блокировки (будет использовано как ключ в Redis)
            timeout: TTL блокировки в секундах (default: 3600 = 1 час)
        """
        self.redis = redis_client
        self.lock_name = lock_name
        self.timeout = timeout
        self.lock_value: Optional[str] = None

    async def acquire(self) -> bool:
        """
        Захват блокировки.

        Использует атомарную операцию SETNX с TTL:
        - Если ключ не существует - создаётся и возвращается True
        - Если ключ существует - возвращается False (блокировка занята)

        Returns:
            True если блокировка захвачена успешно
            False если блокировка уже захвачена другим процессом

        Raises:
            RedisLockError: Ошибка при захвате блокировки
        """
        try:
            # Генерируем уникальный идентификатор (owner)
            # Формат: {lock_name}:{timestamp}:{uuid}
            self.lock_value = (
                f"{self.lock_name}:{time.time_ns()}:{uuid.uuid4().hex[:8]}"
            )

            # SETNX с TTL — атомарная операция
            # nx=True — установить только если не существует
            # ex=self.timeout — установить TTL в секундах
            acquired = await self.redis.set(
                self.lock_name,
                self.lock_value,
                nx=True,  # Только если не существует (SETNX)
                ex=self.timeout,  # TTL в секундах
            )

            if acquired:
                logger.debug(
                    f"Lock acquired: {self.lock_name}, value={self.lock_value}"
                )
            else:
                logger.debug(f"Lock busy: {self.lock_name}")

            return acquired is True

        except RedisError as e:
            logger.error(f"Redis error acquiring lock {self.lock_name}: {e}")
            raise RedisLockError(f"Failed to acquire lock: {e}")
        except Exception as e:
            logger.error(f"Unexpected error acquiring lock {self.lock_name}: {e}")
            raise RedisLockError(f"Failed to acquire lock: {e}")

    async def release(self) -> bool:
        """
        Освобождение блокировки.

        Перед удалением ключа проверяется owner identifier:
        - Если текущее значение совпадает с self.lock_value — удаляем ключ
        - Если не совпадает — не удаляем (это чужой lock)

        Returns:
            True если блокировка успешно освобождена
            False если блокировка не принадлежала нам или уже удалена

        Raises:
            RedisLockError: Ошибка при освобождении блокировки
        """
        if not self.lock_value:
            logger.debug(f"Cannot release lock {self.lock_name}: never acquired")
            return False

        try:
            # Проверяем что блокировка всё ещё принадлежит нам
            current_value = await self.redis.get(self.lock_name)

            if current_value == self.lock_value:
                await self.redis.delete(self.lock_name)
                logger.debug(
                    f"Lock released: {self.lock_name}, value={self.lock_value}"
                )
                self.lock_value = None
                return True
            else:
                # Lock был перехвачен другим процессом (например после экспайра)
                logger.warning(
                    f"Lock release skipped: {self.lock_name} - not owner. "
                    f"Current: {current_value}, Expected: {self.lock_value}"
                )
                self.lock_value = None  # Очищаем локальное значение
                return False

        except RedisError as e:
            logger.error(f"Redis error releasing lock {self.lock_name}: {e}")
            raise RedisLockError(f"Failed to release lock: {e}")
        except Exception as e:
            logger.error(f"Unexpected error releasing lock {self.lock_name}: {e}")
            raise RedisLockError(f"Failed to release lock: {e}")

    async def extend(self, additional_time: Optional[int] = None) -> bool:
        """
        Продление TTL блокировки.

        Полезно для длительных операций чтобы lock не экспайрировался.

        Args:
            additional_time: Дополнительное время в секундах.
                           Если None, используется original timeout.

        Returns:
            True если TTL успешно продлён
            False если lock не принадлежит нам

        Raises:
            RedisLockError: Ошибка при продлении блокировки
        """
        if not self.lock_value:
            logger.debug(f"Cannot extend lock {self.lock_name}: never acquired")
            return False

        try:
            # Проверяем что блокировка всё ещё принадлежит нам
            current_value = await self.redis.get(self.lock_name)

            if current_value == self.lock_value:
                extend_time = additional_time or self.timeout
                await self.redis.expire(self.lock_name, extend_time)
                logger.debug(f"Lock extended: {self.lock_name}, new TTL={extend_time}s")
                return True
            else:
                logger.warning(f"Lock extend skipped: {self.lock_name} - not owner")
                return False

        except RedisError as e:
            logger.error(f"Redis error extending lock {self.lock_name}: {e}")
            raise RedisLockError(f"Failed to extend lock: {e}")
        except Exception as e:
            logger.error(f"Unexpected error extending lock {self.lock_name}: {e}")
            raise RedisLockError(f"Failed to extend lock: {e}")

    async def __aenter__(self) -> "RedisLock":
        """
        Async context manager: вход.

        Automatically acquires the lock on entry.

        Returns:
            Self

        Raises:
            RedisLockError: Если не удалось захватить блокировку
        """
        acquired = await self.acquire()
        if not acquired:
            raise RedisLockError(f"Failed to acquire lock: {self.lock_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Async context manager: выход.

        Automatically releases the lock on exit (even if exception occurred).
        """
        await self.release()

    def __repr__(self) -> str:
        return f"<RedisLock name={self.lock_name}, timeout={self.timeout}, acquired={self.lock_value is not None}>"


# ============== Helper функции для удобного использования ==============


async def acquire_scan_lock(
    redis_client: Redis,
    city: str,
    scan_id: str,
    timeout: int = 3600,
) -> RedisLock:
    """
    Захват блокировки сканирования для города.

    Args:
        redis_client: Redis клиент
        city: Код города (minsk, mogilev, etc.)
        scan_id: Уникальный ID сканирования
        timeout: TTL блокировки в секундах (default: 3600)

    Returns:
        RedisLock объект с захваченной блокировкой

    Raises:
        RedisLockError: Если не удалось захватить блокировку

    Example:
        lock = await acquire_scan_lock(redis, "minsk", "scan_123")
        try:
            await run_scan()
        finally:
            await lock.release()
    """
    lock_key = f"lock:scan:{city}"
    lock = RedisLock(redis_client, lock_key, timeout)

    acquired = await lock.acquire()
    if not acquired:
        # Проверяем кто держит lock
        current_lock = await redis_client.get(lock_key)
        raise RedisLockError(
            f"Failed to acquire scan lock for {city}. " f"Lock holder: {current_lock}"
        )

    logger.info(f"Scan lock acquired for {city}, scan_id={scan_id}")
    return lock


async def release_scan_lock(
    redis_client: Redis,
    city: str,
    scan_id: str,
) -> bool:
    """
    Освобождение блокировки сканирования.

    Args:
        redis_client: Redis клиент
        city: Код города
        scan_id: Уникальный ID сканирования

    Returns:
        True если успешно освобождено, False если не принадлежало нам

    Example:
        await release_scan_lock(redis, "minsk", "scan_123")
    """
    lock_key = f"lock:scan:{city}"
    lock = RedisLock(redis_client, lock_key)
    # Восстанавливаем value для проверки owner
    # В реальном использовании lock_value должен сохраняться в процессе сканирования
    lock.lock_value = f"lock:scan:{city}:{scan_id}"

    released = await lock.release()
    if released:
        logger.info(f"Scan lock released for {city}, scan_id={scan_id}")
    return released


def get_scan_lock_key(city: str) -> str:
    """
    Получить ключ Redis для lock сканирования города.

    Args:
        city: Код города

    Returns:
        Ключ в формате "lock:scan:{city}"

    Example:
        >>> get_scan_lock_key("minsk")
        'lock:scan:minsk'
    """
    return f"lock:scan:{city}"
