"""
Redis Lock Watchdog для Kufar Monitor.

Фоновый сервис для мониторинга и очистки застрявших Redis lock.
Автоматически освобождает блокировки которые превысили максимальный возраст.

Особенности:
- Периодическая проверка всех lock сканирования
- Очистка застрявших lock с истёкшим TTL
- Логирование всех операций очистки
- Безопасная работа с Redis (обработка ошибок подключения)

Пример использования:
    from app.core.redis_watchdog import RedisLockWatchdog
    from app.core.redis_client import get_redis

    redis_client = await get_redis()
    watchdog = RedisLockWatchdog(redis_client)
    await watchdog.cleanup_stale_locks(max_age_seconds=3700)

    # Или запустить фоновую задачу:
    asyncio.create_task(watchdog.run_periodically(interval_seconds=600))
"""

import asyncio
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError, ConnectionError
from typing import List, Dict, Optional
from datetime import datetime, timezone
from loguru import logger


class RedisLockWatchdog:
    """
    Watchdog для очистки застрявших Redis lock.

    Мониторит lock сканирования и автоматически освобождает те,
    которые превысили максимальный возраст (timeout).

    Attributes:
        redis: Redis клиент
        lock_pattern: Шаблон для поиска lock ключей (по умолчанию "lock:scan:*")

    Example:
        redis_client = await get_redis()
        watchdog = RedisLockWatchdog(redis_client)
        await watchdog.cleanup_stale_locks(max_age_seconds=3700)
    """

    def __init__(self, redis_client: Redis, lock_pattern: str = "lock:scan:*"):
        """
        Инициализация watchdog.

        Args:
            redis_client: Redis клиент (redis.asyncio.Redis)
            lock_pattern: Шаблон для поиска lock ключей (default: "lock:scan:*")
        """
        self.redis = redis_client
        self.lock_pattern = lock_pattern
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def cleanup_stale_locks(
        self, max_age_seconds: int = 3700
    ) -> Dict[str, int]:
        """
        Очистить lock которые старше max_age_seconds.

        Проверяет все lock сканирования и удаляет те, у которых:
        - TTL истёк (ключ не существует)
        - TTL отсутствует (-1) и lock старше max_age_seconds
        - TTL > max_age_seconds (слишком старый lock)

        Args:
            max_age_seconds: Максимальный возраст lock в секундах
                           (default: 3700 = 1 час 1 минута, чуть больше timeout сканирования)

        Returns:
            Словарь со статистикой:
            - cleaned: количество очищенных lock
            - skipped: количество пропущенных lock
            - errors: количество ошибок

        Raises:
            RedisLockWatchdogError: Ошибка при очистке lock
        """
        stats = {"cleaned": 0, "skipped": 0, "errors": 0}

        try:
            # Найти все lock сканирования
            lock_keys: List[bytes] = await self.redis.keys(self.lock_pattern)

            if not lock_keys:
                logger.debug("No scan locks found")
                return stats

            logger.info(f"Checking {len(lock_keys)} scan locks for staleness")

            for key_bytes in lock_keys:
                key = key_bytes.decode("utf-8") if isinstance(key_bytes, bytes) else key_bytes

                try:
                    # Получить TTL ключа
                    ttl = await self.redis.ttl(key)

                    if ttl == -2:
                        # Ключ не существует (уже удалён)
                        logger.debug(f"Lock {key} does not exist (already removed)")
                        stats["skipped"] += 1
                        continue

                    if ttl == -1:
                        # Lock без TTL (бессрочный) - очистить
                        logger.warning(
                            f"Lock {key} has no TTL - cleaning up stale lock"
                        )
                        await self.redis.delete(key)
                        stats["cleaned"] += 1
                        continue

                    if ttl > max_age_seconds:
                        # Lock слишком старый - очистить
                        logger.warning(
                            f"Lock {key} TTL ({ttl}s) exceeds max_age ({max_age_seconds}s) - cleaning up"
                        )
                        await self.redis.delete(key)
                        stats["cleaned"] += 1
                        continue

                    # Lock валидный - пропустить
                    logger.debug(f"Lock {key} TTL={ttl}s - valid, skipping")
                    stats["skipped"] += 1

                except RedisError as e:
                    logger.error(f"Redis error processing lock {key}: {e}")
                    stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Unexpected error processing lock {key}: {e}")
                    stats["errors"] += 1

            if stats["cleaned"] > 0:
                logger.info(
                    f"Lock cleanup completed: {stats['cleaned']} cleaned, "
                    f"{stats['skipped']} skipped, {stats['errors']} errors"
                )

            return stats

        except ConnectionError as e:
            logger.error(f"Redis connection error during lock cleanup: {e}")
            raise
        except RedisError as e:
            logger.error(f"Redis error during lock cleanup: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during lock cleanup: {e}")
            raise

    async def get_lock_info(self, lock_key: str) -> Optional[Dict]:
        """
        Получить информацию о конкретном lock.

        Args:
            lock_key: Ключ lock (например, "lock:scan:minsk")

        Returns:
            Словарь с информацией о lock или None если не существует:
            - exists: bool
            - ttl: int (в секундах)
            - value: str (owner identifier)
        """
        try:
            exists = await self.redis.exists(lock_key)
            if not exists:
                return None

            ttl = await self.redis.ttl(lock_key)
            value = await self.redis.get(lock_key)

            return {
                "exists": True,
                "ttl": ttl,
                "value": value,
                "key": lock_key,
            }

        except RedisError as e:
            logger.error(f"Redis error getting lock info for {lock_key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting lock info for {lock_key}: {e}")
            return None

    async def get_all_locks_status(self) -> List[Dict]:
        """
        Получить статус всех lock сканирования.

        Returns:
            Список словарей с информацией о каждом lock
        """
        locks = []

        try:
            lock_keys: List[bytes] = await self.redis.keys(self.lock_pattern)

            for key_bytes in lock_keys:
                key = key_bytes.decode("utf-8") if isinstance(key_bytes, bytes) else key_bytes
                info = await self.get_lock_info(key)
                if info:
                    locks.append(info)

            return locks

        except Exception as e:
            logger.error(f"Error getting all locks status: {e}")
            return []

    async def run_periodically(self, interval_seconds: int = 600) -> None:
        """
        Запустить периодическую очистку lock в фоновом режиме.

        Args:
            interval_seconds: Интервал между очистками в секундах (default: 600 = 10 минут)

        Example:
            watchdog = RedisLockWatchdog(redis_client)
            asyncio.create_task(watchdog.run_periodically(600))
        """
        self._running = True
        logger.info(
            f"Lock watchdog started: cleaning every {interval_seconds} seconds"
        )

        try:
            while self._running:
                await asyncio.sleep(interval_seconds)

                try:
                    stats = await self.cleanup_stale_locks()
                    logger.debug(
                        f"Periodic lock cleanup: {stats['cleaned']} cleaned, "
                        f"{stats['skipped']} skipped"
                    )
                except ConnectionError as e:
                    logger.warning(f"Redis connection unavailable for watchdog: {e}")
                except Exception as e:
                    logger.error(f"Error in periodic lock cleanup: {e}")

        except asyncio.CancelledError:
            logger.info("Lock watchdog task cancelled")
            raise
        finally:
            self._running = False
            logger.info("Lock watchdog stopped")

    def stop(self) -> None:
        """
        Остановить периодическую очистку.

        Вызывается при shutdown приложения.
        """
        logger.info("Stopping lock watchdog...")
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


class RedisLockWatchdogError(Exception):
    """Исключение при ошибках работы Redis Lock Watchdog."""

    pass


# ============== Helper функции для удобного использования ==============


async def start_lock_watchdog(
    redis_client: Redis, interval_seconds: int = 600
) -> RedisLockWatchdog:
    """
    Создать и запустить watchdog для очистки lock.

    Args:
        redis_client: Redis клиент
        interval_seconds: Интервал очистки в секундах (default: 600)

    Returns:
        Запущенный RedisLockWatchdog экземпляр

    Example:
        redis_client = await get_redis()
        watchdog = await start_lock_watchdog(redis_client, 600)
        # Запущен в background, остановится при shutdown
    """
    watchdog = RedisLockWatchdog(redis_client)
    watchdog._cleanup_task = asyncio.create_task(
        watchdog.run_periodically(interval_seconds)
    )
    return watchdog


async def stop_lock_watchdog(watchdog: RedisLockWatchdog) -> None:
    """
    Остановить watchdog.

    Args:
        watchdog: Экземпляр watchdog для остановки
    """
    watchdog.stop()
    if watchdog._cleanup_task:
        try:
            await watchdog._cleanup_task
        except asyncio.CancelledError:
            pass


async def cleanup_stale_locks_once(redis_client: Redis) -> Dict[str, int]:
    """
    Однократная очистка застрявших lock.

    Args:
        redis_client: Redis клиент

    Returns:
        Статистика очистки (cleaned, skipped, errors)

    Example:
        redis_client = await get_redis()
        stats = await cleanup_stale_locks_once(redis_client)
        print(f"Cleaned {stats['cleaned']} stale locks")
    """
    watchdog = RedisLockWatchdog(redis_client)
    return await watchdog.cleanup_stale_locks()
