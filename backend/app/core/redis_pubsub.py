"""
Redis Pub/Sub для управления состоянием сканирования в Kufar Monitor.

Реализует:
- Хранение состояния сканирования в Redis Hash (scan:progress:{city})
- TTL 2 часа для авто-очистки после завершения
- Pub/Sub для real-time обновлений WebSocket клиентов
- Преобразование типов данных (str → int/float/bool)

Пример использования:
    from app.core.redis_pubsub import RedisScanState
    from app.core.redis_client import get_redis

    redis_client = await get_redis()
    scan_state = RedisScanState(redis_client)

    # Обновление прогресса
    await scan_state.update_progress(
        city="minsk",
        stage="fetching",
        pages_scraped=10,
        listings_fetched=300,
        is_stable=False
    )

    # Получение прогресса
    progress = await scan_state.get_progress("minsk")

    # Подписка на обновления
    async with scan_state.subscribe_progress() as pubsub:
        async for message in pubsub.listen():
            print(message)
"""

import redis.asyncio as redis
import json
import time
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from loguru import logger


class RedisScanState:
    """
    Управление состоянием сканирования в Redis.

    Формат ключа: scan:progress:{city}
    Тип: Hash
    TTL: 7200 секунд (2 часа)

    Attributes:
        redis: Redis клиент
    """

    # Ключи Redis
    PROGRESS_KEY_PREFIX = "scan:progress"
    PUBSUB_CHANNEL = "scan:progress"
    PROGRESS_TTL_SECONDS = 7200  # 2 часа

    def __init__(self, redis_client: redis.Redis):
        """
        Инициализация RedisScanState.

        Args:
            redis_client: Redis клиент (redis.asyncio.Redis)
        """
        self.redis = redis_client

    def _get_progress_key(self, city: str) -> str:
        """
        Получить ключ Redis для прогресса сканирования города.

        Args:
            city: Код города (minsk, mogilev, etc.)

        Returns:
            Ключ в формате "scan:progress:{city}"
        """
        return f"{self.PROGRESS_KEY_PREFIX}:{city}"

    async def update_progress(
        self,
        city: str,
        stage: str,
        pages_scraped: int = 0,
        listings_fetched: int = 0,
        listings_processed: int = 0,
        is_stable: bool = False,
        elapsed_seconds: float = 0.0,
        error: Optional[str] = None,
        city_name: Optional[str] = None,
    ) -> None:
        """
        Обновление прогресса сканирования в Redis Hash.

        Атомарно обновляет hash и публикует обновление через Pub/Sub.

        Args:
            city: Код города
            stage: Стадия сканирования (starting, fetching, parsing, upserting, marking_deleted, done, error)
            pages_scraped: Количество обработанных страниц
            listings_fetched: Количество загруженных объявлений
            listings_processed: Количество обработанных объявлений
            is_stable: Флаг стабильности данных (True на final/done/error)
            elapsed_seconds: Прошло времени с начала сканирования
            error: Текст ошибки (если stage=error)
            city_name: Название города на русском (опционально)

        Example:
            await scan_state.update_progress(
                city="minsk",
                stage="fetching",
                pages_scraped=10,
                listings_fetched=300,
                is_stable=False,
                elapsed_seconds=45.5
            )
        """
        key = self._get_progress_key(city)

        data = {
            "city": city,
            "stage": stage,
            "pages_scraped": str(pages_scraped),
            "listings_fetched": str(listings_fetched),
            "listings_processed": str(listings_processed),
            "is_stable": str(is_stable).lower(),
            "elapsed_seconds": str(elapsed_seconds),
            "updated_at": str(time.time()),
        }

        if city_name:
            data["city_name"] = city_name

        if error:
            data["error"] = error

        try:
            # HSET — атомарное обновление hash
            await self.redis.hset(key, mapping=data)

            # Устанавливаем TTL 2 часа (после завершения сканирования)
            await self.redis.expire(key, self.PROGRESS_TTL_SECONDS)

            # Публикуем обновление через Pub/Sub
            await self.publish_progress(city, data)

            logger.debug(
                f"Scan progress updated for {city}: stage={stage}, "
                f"pages={pages_scraped}, listings={listings_fetched}"
            )

        except Exception as e:
            logger.error(f"Failed to update scan progress for {city}: {e}")
            # Не прерываем сканирование если публикация не удалась

    async def get_progress(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Получение текущего состояния сканирования.

        Args:
            city: Код города

        Returns:
            Dict с прогрессом или None если прогресс не найден

        Example:
            progress = await scan_state.get_progress("minsk")
            if progress:
                print(f"Stage: {progress['stage']}, Pages: {progress['pages_scraped']}")
        """
        key = self._get_progress_key(city)

        try:
            data = await self.redis.hgetall(key)

            if not data:
                return None

            # Преобразуем типы данных
            return {
                "city": data.get("city"),
                "city_name": data.get("city_name"),
                "stage": data.get("stage"),
                "pages_scraped": int(data.get("pages_scraped", 0)),
                "listings_fetched": int(data.get("listings_fetched", 0)),
                "listings_processed": int(data.get("listings_processed", 0)),
                "is_stable": data.get("is_stable") == "true",
                "elapsed_seconds": float(data.get("elapsed_seconds", 0.0)),
                "updated_at": float(data.get("updated_at", 0)),
                "error": data.get("error"),
            }

        except Exception as e:
            logger.error(f"Failed to get scan progress for {city}: {e}")
            return None

    async def get_all_progress(self) -> Dict[str, Dict[str, Any]]:
        """
        Получение прогресса для всех городов.

        Returns:
            Dict {city: progress_data} для всех активных сканирований

        Example:
            all_progress = await scan_state.get_all_progress()
            for city, progress in all_progress.items():
                print(f"{city}: {progress['stage']}")
        """
        result = {}

        try:
            # Ищем все ключи scan:progress:*
            pattern = f"{self.PROGRESS_KEY_PREFIX}:*"
            cursor = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=pattern, count=100
                )

                for key in keys:
                    # Извлекаем city из ключа (ключ может быть bytes или str)
                    if isinstance(key, bytes):
                        city = key.decode().split(":")[-1]
                    else:
                        city = key.split(":")[-1]
                    progress = await self.get_progress(city)

                    if progress:
                        result[city] = progress

                if cursor == 0:
                    break

        except Exception as e:
            logger.error(f"Failed to get all scan progress: {e}")

        return result

    async def clear_progress(self, city: str) -> bool:
        """
        Очистка прогресса сканирования.

        Args:
            city: Код города

        Returns:
            True если прогресс был очищен, False если не существовал

        Example:
            await scan_state.clear_progress("minsk")
        """
        key = self._get_progress_key(city)

        try:
            deleted = await self.redis.delete(key)
            logger.debug(f"Scan progress cleared for {city}: {deleted > 0}")
            return deleted > 0

        except Exception as e:
            logger.error(f"Failed to clear scan progress for {city}: {e}")
            return False

    async def publish_progress(self, city: str, data: Dict[str, Any]) -> None:
        """
        Публикация обновления через Redis Pub/Sub.

        Args:
            city: Код города
            data: Данные прогресса для публикации

        Example:
            await scan_state.publish_progress("minsk", {
                "stage": "fetching",
                "pages_scraped": 10
            })
        """
        try:
            message = json.dumps(
                {
                    "channel": self.PUBSUB_CHANNEL,
                    "city": city,
                    **data,
                },
                ensure_ascii=False,
            )

            await self.redis.publish(self.PUBSUB_CHANNEL, message)

            logger.debug(f"Scan progress published for {city}: {data.get('stage')}")

        except Exception as e:
            logger.error(f"Failed to publish scan progress for {city}: {e}")

    @asynccontextmanager
    async def subscribe_progress(self) -> AsyncGenerator[redis.client.PubSub, None]:
        """
        Контекстный менеджер для подписки на обновления прогресса.

        Yields:
            PubSub объект для получения сообщений

        Example:
            async with scan_state.subscribe_progress() as pubsub:
                async for message in pubsub.listen():
                    data = json.loads(message["data"])
                    print(f"Progress update: {data}")
        """
        pubsub = self.redis.pubsub()

        try:
            await pubsub.subscribe(self.PUBSUB_CHANNEL)
            logger.debug(f"Subscribed to {self.PUBSUB_CHANNEL}")

            yield pubsub

        finally:
            await pubsub.unsubscribe(self.PUBSUB_CHANNEL)
            await pubsub.close()
            logger.debug(f"Unsubscribed from {self.PUBSUB_CHANNEL}")

    async def get_progress_ttl(self, city: str) -> int:
        """
        Получение оставшегося TTL для прогресса сканирования.

        Args:
            city: Код города

        Returns:
            TTL в секундах или -1 если ключ не существует

        Example:
            ttl = await scan_state.get_progress_ttl("minsk")
            if ttl > 0:
                print(f"TTL: {ttl} seconds")
        """
        key = self._get_progress_key(city)

        try:
            return await self.redis.ttl(key)

        except Exception as e:
            logger.error(f"Failed to get TTL for {city}: {e}")
            return -1


# ============== Helper функции для удобного использования ==============


async def get_scan_state(redis_client: redis.Redis) -> RedisScanState:
    """
    Получить экземпляр RedisScanState.

    Args:
        redis_client: Redis клиент

    Returns:
        RedisScanState экземпляр

    Example:
        redis = await get_redis()
        scan_state = await get_scan_state(redis)
    """
    return RedisScanState(redis_client)


async def update_scan_progress(
    redis_client: redis.Redis,
    city: str,
    stage: str,
    pages_scraped: int = 0,
    listings_fetched: int = 0,
    is_stable: bool = False,
    elapsed_seconds: float = 0.0,
    error: Optional[str] = None,
) -> None:
    """
    Helper функция для быстрого обновления прогресса.

    Args:
        redis_client: Redis клиент
        city: Код города
        stage: Стадия сканирования
        pages_scraped: Количество страниц
        listings_fetched: Количество объявлений
        is_stable: Флаг стабильности
        elapsed_seconds: Прошло времени
        error: Текст ошибки

    Example:
        await update_scan_progress(
            redis, "minsk", "fetching",
            pages_scraped=10, is_stable=False
        )
    """
    scan_state = RedisScanState(redis_client)
    await scan_state.update_progress(
        city=city,
        stage=stage,
        pages_scraped=pages_scraped,
        listings_fetched=listings_fetched,
        is_stable=is_stable,
        elapsed_seconds=elapsed_seconds,
        error=error,
    )


async def get_scan_progress(
    redis_client: redis.Redis,
    city: str,
) -> Optional[Dict[str, Any]]:
    """
    Helper функция для получения прогресса сканирования.

    Args:
        redis_client: Redis клиент
        city: Код города

    Returns:
        Dict с прогрессом или None

    Example:
        progress = await get_scan_progress(redis, "minsk")
    """
    scan_state = RedisScanState(redis_client)
    return await scan_state.get_progress(city)
