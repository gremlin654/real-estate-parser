"""
Rate Limiter implementation using Token Bucket algorithm with Redis.

Алгоритм Token Bucket:
- Ковш ёмкостью `capacity` токенов
- Токены добавляются со скоростью `refill_rate` в секунду
- Каждый запрос потребляет 1 токен
- Если токенов нет — ждём пока добавятся

Преимущества:
- Плавное ограничение средней частоты
- Позволяет кратковременные всплески (burst)
- Распределённое хранение в Redis
"""

import redis.asyncio as redis
import time
import asyncio
from typing import Optional
from loguru import logger


class TokenBucketRateLimiter:
    """
    Rate limiter implementation using Token Bucket algorithm.

    Attributes:
        redis: Redis client instance
        key_prefix: Prefix for Redis keys
        capacity: Maximum number of tokens in the bucket
        refill_rate: Number of tokens added per second
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        key_prefix: str = "ratelimit",
        capacity: int = 10,  # Максимум токенов
        refill_rate: float = 10.0,  # Токенов в секунду
    ):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.refill_rate = refill_rate

    def _get_keys(self, identifier: str) -> tuple[str, str]:
        """
        Получение ключей для токенов и последнего обновления.

        Args:
            identifier: Уникальный идентификатор (например, "city:minsk")

        Returns:
            Кортеж (tokens_key, last_update_key)
        """
        base_key = f"{self.key_prefix}:{identifier}"
        return f"{base_key}:tokens", f"{base_key}:last_update"

    async def acquire(self, identifier: str, tokens: int = 1) -> float:
        """
        Запрос токенов.

        Args:
            identifier: Уникальный идентификатор (например, "kufar:minsk")
            tokens: Количество требуемых токенов

        Returns:
            Время ожидания в секундах (0 если токены доступны сразу)
        """
        tokens_key, last_update_key = self._get_keys(identifier)
        now = time.time()

        # Используем Lua скрипт для атомарности
        lua_script = """
        local tokens_key = KEYS[1]
        local last_update_key = KEYS[2]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = tonumber(ARGV[4])

        -- Получаем текущее количество токенов
        local tokens = tonumber(redis.call('GET', tokens_key))
        local last_update = tonumber(redis.call('GET', last_update_key))

        -- Если ключей нет, инициализируем
        if tokens == nil then
            tokens = capacity
        end
        if last_update == nil then
            last_update = now
        end

        -- Рассчитываем сколько токенов добавилось с последнего обновления
        local elapsed = now - last_update
        local refill = elapsed * refill_rate
        tokens = math.min(capacity, tokens + refill)

        -- Проверяем хватает ли токенов
        local wait_time = 0
        if tokens < requested then
            -- Рассчитываем время ожидания
            local needed = requested - tokens
            wait_time = needed / refill_rate
            -- НЕ обновляем last_update если ждём - это позволит токенкам пополниться
        else
            -- Потребляем токены
            tokens = tokens - requested
            redis.call('SET', tokens_key, tokens)
            redis.call('SET', last_update_key, now)
        end

        -- Устанавливаем TTL (1 час бездействия)
        redis.call('EXPIRE', tokens_key, 3600)
        redis.call('EXPIRE', last_update_key, 3600)

        -- Возвращаем строку вместо числа (redis-py округляет float до int)
        return tostring(wait_time)
        """

        result = await self.redis.eval(
            lua_script,
            2,  # Количество ключей
            tokens_key,
            last_update_key,
            self.capacity,
            self.refill_rate,
            now,
            tokens,
        )

        # Парсим результат (строка или bytes)
        if isinstance(result, bytes):
            wait_time = float(result.decode())
        elif isinstance(result, str):
            wait_time = float(result)
        else:
            wait_time = float(result) if result else 0.0

        if wait_time > 0:
            logger.debug(
                f"Rate limit: identifier={identifier}, wait_time={wait_time:.3f}s"
            )

        return wait_time

    async def wait_and_acquire(self, identifier: str, tokens: int = 1):
        """
        Запрос токенов с ожиданием.

        Args:
            identifier: Уникальный идентификатор
            tokens: Количество требуемых токенов
        """
        wait_time = await self.acquire(identifier, tokens)

        if wait_time > 0:
            logger.debug(
                f"Rate limit wait: identifier={identifier}, waiting {wait_time:.3f}s"
            )
            await asyncio.sleep(wait_time)

    async def get_tokens(self, identifier: str) -> float:
        """
        Получение текущего количества доступных токенов.

        Args:
            identifier: Уникальный идентификатор

        Returns:
            Количество доступных токенов
        """
        tokens_key, last_update_key = self._get_keys(identifier)

        tokens = await self.redis.get(tokens_key)
        last_update = await self.redis.get(last_update_key)

        if tokens is None:
            return float(self.capacity)

        now = time.time()
        tokens = float(tokens)
        last_update = float(last_update) if last_update else now

        # Рассчитываем добавленные токены
        elapsed = now - last_update
        refill = elapsed * self.refill_rate
        tokens = min(self.capacity, tokens + refill)

        return tokens

    async def reset(self, identifier: str):
        """
        Сброс токенов для идентификатора (для тестов).

        Args:
            identifier: Уникальный идентификатор
        """
        tokens_key, last_update_key = self._get_keys(identifier)
        await self.redis.delete(tokens_key, last_update_key)
        logger.debug(f"Rate limit reset: identifier={identifier}")


async def get_rate_limiter(
    redis_client: redis.Redis,
    key_prefix: str = "ratelimit",
    capacity: int = 10,
    refill_rate: float = 10.0,
) -> TokenBucketRateLimiter:
    """
    Получение экземпляра RateLimiter.

    Args:
        redis_client: Redis client instance
        key_prefix: Prefix for Redis keys
        capacity: Maximum number of tokens
        refill_rate: Tokens per second

    Returns:
        TokenBucketRateLimiter instance
    """
    return TokenBucketRateLimiter(redis_client, key_prefix, capacity, refill_rate)
