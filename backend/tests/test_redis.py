"""
Тесты для Redis клиента.

Unit тесты:
- test_redis_client_singleton - проверка singleton паттерна
- test_redis_client_connect - проверка подключения
- test_redis_client_close - проверка закрытия подключения
- test_redis_client_health_check - проверка health check

Integration тесты:
- test_redis_set_get - установка и получение значения
- test_redis_setex - установка значения с TTL
- test_redis_delete - удаление ключа
- test_redis_exists - проверка существования ключа
- test_redis_health_check_integration - integration health check
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from app.core.redis_client import (
    RedisClient,
    get_redis_client,
    get_redis,
    close_redis,
    health_check_redis,
)
from app.config import settings


# =============================================================================
# Unit тесты
# =============================================================================


class TestRedisClientSingleton:
    """Тесты singleton паттерна RedisClient."""

    def test_redis_client_singleton(self):
        """Проверка что RedisClient создаётся только один раз."""
        # Сбрасываем singleton для чистоты теста
        import app.core.redis_client as redis_module
        redis_module._redis_client = None
        
        client1 = get_redis_client()
        client2 = get_redis_client()

        assert client1 is client2
        assert isinstance(client1, RedisClient)

    def test_redis_client_is_connected_initial(self):
        """Проверка начального состояния подключения."""
        # Пропускаем если Redis уже инициализирован фикстурой
        import app.core.redis_client as redis_module
        if redis_module._redis_client is not None:
            pytest.skip("Redis already initialized by fixture")
        
        # Сбрасываем singleton для чистоты теста
        redis_module._redis_client = None

        client = get_redis_client()
        assert client.is_connected is False


@pytest.mark.asyncio
async def test_redis_client_connect_success(init_redis):
    """Проверка успешного подключения к Redis."""
    # Пропускаем если Redis уже инициализирован фикстурой
    import app.core.redis_client as redis_module
    if init_redis is None:
        pytest.skip("Redis not available")
    
    # Пропускаем так как Redis уже подключён фикстурой
    if redis_module._redis_client is not None:
        pytest.skip("Redis already connected by fixture")

    # Сбрасываем singleton
    redis_module._redis_client = None

    client = get_redis_client()

    # Мокаем redis.from_url и ping
    with patch('app.core.redis_client.redis.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_from_url.return_value = mock_redis

        await client.connect(settings.REDIS_URL)

        assert client.is_connected is True
        assert client._redis is not None
        mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_redis_client_connect_failure():
    """Проверка обработки ошибки подключения."""
    # Пропускаем если Redis уже инициализирован фикстурой
    import app.core.redis_client as redis_module
    if redis_module._redis_client is not None:
        pytest.skip("Redis already initialized by fixture")
    
    # Сбрасываем singleton
    redis_module._redis_client = None

    client = get_redis_client()

    # Мокаем redis.from_url с выбрасыванием исключения
    with patch('app.core.redis_client.redis.from_url') as mock_from_url:
        mock_from_url.side_effect = RedisConnectionError("Connection refused")

        with pytest.raises(RedisConnectionError):
            await client.connect(settings.REDIS_URL)

        assert client.is_connected is False


@pytest.mark.asyncio
async def test_redis_client_close():
    """Проверка закрытия подключения."""
    import app.core.redis_client as redis_module

    # Сбрасываем singleton
    redis_module._redis_client = None

    client = get_redis_client()

    # Устанавливаем подключение вручную для теста
    mock_redis = AsyncMock()
    mock_redis.close = AsyncMock()
    client._redis = mock_redis
    client._is_connected = True

    await client.close()

    assert client.is_connected is False
    assert client._redis is None
    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_redis_client_health_check_success():
    """Проверка health check при успешном подключении."""
    import app.core.redis_client as redis_module

    # Сбрасываем singleton
    redis_module._redis_client = None

    client = get_redis_client()

    # Мокаем redis и ping
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    client._redis = mock_redis
    client._is_connected = True

    result = await client.health_check()

    assert result is True
    mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_redis_client_health_check_failure():
    """Проверка health check при неудачном подключении."""
    import app.core.redis_client as redis_module

    # Сбрасываем singleton
    redis_module._redis_client = None

    client = get_redis_client()
    client._redis = None
    client._is_connected = False

    result = await client.health_check()

    assert result is False


@pytest.mark.asyncio
async def test_redis_client_get_client_not_connected():
    """Проверка get_client когда не подключено."""
    import app.core.redis_client as redis_module

    # Сбрасываем singleton
    redis_module._redis_client = None

    client = get_redis_client()
    client._redis = None
    client._is_connected = False

    with pytest.raises(RedisError, match="Redis is not connected"):
        client.get_client()


# =============================================================================
# Integration тесты (требуют запущенный Redis)
# =============================================================================


@pytest.mark.asyncio
async def test_redis_set_get():
    """Integration тест: установка и получение значения."""
    # Пропускаем тест если Redis недоступен
    try:
        redis = await get_redis()
    except Exception:
        pytest.skip("Redis недоступен для integration тестов")

    # SET
    await redis.set("test_key", "test_value")

    # GET
    value = await redis.get("test_key")
    assert value == "test_value"

    # Cleanup
    await redis.delete("test_key")


@pytest.mark.asyncio
async def test_redis_setex():
    """Integration тест: установка значения с TTL."""
    try:
        # Сбрасываем подключение для создания нового в этом тесте
        import app.core.redis_client as redis_module
        redis_module._redis_client = None
        
        redis = await get_redis()
    except Exception:
        pytest.skip("Redis недоступен для integration тестов")

    try:
        # SETEX
        await redis.setex("test_key_ttl", 60, "test_value_ttl")

        # GET
        value = await redis.get("test_key_ttl")
        assert value == "test_value_ttl"

        # Проверка TTL
        ttl = await redis.ttl("test_key_ttl")
        assert 0 < ttl <= 60

        # Cleanup
        await redis.delete("test_key_ttl")
    finally:
        await close_redis()


@pytest.mark.asyncio
async def test_redis_delete():
    """Integration тест: удаление ключа."""
    try:
        # Сбрасываем подключение для создания нового в этом тесте
        import app.core.redis_client as redis_module
        redis_module._redis_client = None
        
        redis = await get_redis()
    except Exception:
        pytest.skip("Redis недоступен для integration тестов")

    try:
        # SET
        await redis.set("test_key_delete", "value")

        # DELETE
        result = await redis.delete("test_key_delete")
        assert result == 1

        # Проверка что ключ удалён
        exists = await redis.exists("test_key_delete")
        assert exists == 0
    finally:
        await close_redis()


@pytest.mark.asyncio
async def test_redis_exists():
    """Integration тест: проверка существования ключа."""
    try:
        # Сбрасываем подключение для создания нового в этом тесте
        import app.core.redis_client as redis_module
        redis_module._redis_client = None
        
        redis = await get_redis()
    except Exception:
        pytest.skip("Redis недоступен для integration тестов")

    try:
        # Проверка несуществующего ключа
        exists = await redis.exists("nonexistent_key")
        assert exists == 0

        # SET
        await redis.set("test_key_exists", "value")

        # Проверка существующего ключа
        exists = await redis.exists("test_key_exists")
        assert exists == 1

        # Cleanup
        await redis.delete("test_key_exists")
    finally:
        await close_redis()


@pytest.mark.asyncio
async def test_redis_health_check_integration():
    """Integration тест: health check Redis."""
    try:
        await get_redis()
    except Exception:
        pytest.skip("Redis недоступен для integration тестов")

    result = await health_check_redis()
    assert result is True


@pytest.mark.asyncio
async def test_redis_get_redis_singleton():
    """Integration тест: проверка что get_redis возвращает singleton."""
    try:
        await get_redis()
    except Exception:
        pytest.skip("Redis недоступен для integration тестов")

    redis1 = await get_redis()
    redis2 = await get_redis()

    # Это один и тот же объект подключения
    assert redis1 is redis2


@pytest.mark.asyncio
async def test_redis_close_integration():
    """Integration тест: graceful shutdown."""
    try:
        await get_redis()
    except Exception:
        pytest.skip("Redis недоступен для integration тестов")

    # Закрываем подключение
    await close_redis()

    # Проверяем что подключение закрыто
    client = get_redis_client()
    # После close_redis() флаг должен быть False
    # Но singleton остаётся, поэтому проверяем _redis
    assert client._redis is None or not client.is_connected
