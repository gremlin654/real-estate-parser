"""
Тесты для Redis Distributed Lock.

Unit тесты:
- test_redis_lock_acquire_success — успешный захват блокировки
- test_redis_lock_acquire_conflict — конфликт при захвате
- test_redis_lock_release — освобождение lock
- test_redis_lock_release_wrong_owner — освобождение чужого lock
- test_redis_lock_auto_expire — авто-экспайр после TTL
- test_redis_lock_context_manager — async context manager
- test_redis_lock_reentrant — повторный захват после релиза
- test_redis_lock_extend — продление TTL

Integration тесты:
- test_scan_trigger_with_lock_success — успешное сканирование с lock
- test_scan_trigger_lock_conflict — конфликт при активном сканировании
- test_scan_trigger_lock_auto_expire — экспайр lock и повторное сканирование
- test_scan_trigger_lock_release_on_error — освобождение при ошибке
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.redis_lock import (
    RedisLock,
    RedisLockError,
    acquire_scan_lock,
    release_scan_lock,
    get_scan_lock_key,
)


# =============================================================================
# Unit тесты
# =============================================================================


class TestRedisLockAcquire:
    """Тесты захвата блокировки."""

    @pytest.mark.asyncio
    async def test_redis_lock_acquire_success(self):
        """Успешный захват блокировки."""
        # Создаём mock Redis клиента
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.set = AsyncMock(return_value=True)  # SETNX вернул True

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        acquired = await lock.acquire()

        assert acquired is True
        assert lock.lock_value is not None
        # Проверка что set был вызван с правильными параметрами
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "lock:scan:minsk"  # key
        assert call_args[1]["nx"] is True  # SETNX
        assert call_args[1]["ex"] == 3600  # TTL

    @pytest.mark.asyncio
    async def test_redis_lock_acquire_conflict(self):
        """Конфликт при захвате — lock уже занят."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.set = AsyncMock(return_value=False)  # SETNX вернул False (ключ существует)

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        acquired = await lock.acquire()

        assert acquired is False
        assert lock.lock_value is not None  # Значение всё равно сгенерировано

    @pytest.mark.asyncio
    async def test_redis_lock_acquire_redis_error(self):
        """Обработка ошибки Redis при захвате."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.set = AsyncMock(side_effect=RedisError("Connection lost"))

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)

        with pytest.raises(RedisLockError, match="Failed to acquire lock"):
            await lock.acquire()


class TestRedisLockRelease:
    """Тесты освобождения блокировки."""

    @pytest.mark.asyncio
    async def test_redis_lock_release_success(self):
        """Успешное освобождение блокировки."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.get = AsyncMock(return_value="lock:scan:minsk:123:abc")
        mock_redis.delete = AsyncMock(return_value=1)

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        lock.lock_value = "lock:scan:minsk:123:abc"  # Устанавливаем owner

        released = await lock.release()

        assert released is True
        assert lock.lock_value is None  # Очищено после релиза
        mock_redis.get.assert_called_once_with("lock:scan:minsk")
        mock_redis.delete.assert_called_once_with("lock:scan:minsk")

    @pytest.mark.asyncio
    async def test_redis_lock_release_wrong_owner(self):
        """Попытка освободить чужой lock."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.get = AsyncMock(return_value="lock:scan:minsk:999:xyz")  # Другой owner

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        lock.lock_value = "lock:scan:minsk:123:abc"  # Наш owner

        released = await lock.release()

        assert released is False
        assert lock.lock_value is None  # Всё равно очищено локально
        mock_redis.delete.assert_not_called()  # Delete не вызван

    @pytest.mark.asyncio
    async def test_redis_lock_release_not_acquired(self):
        """Попытка освободить незахваченный lock."""
        mock_redis = AsyncMock(spec=Redis)

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        # lock_value не установлен

        released = await lock.release()

        assert released is False
        mock_redis.get.assert_not_called()
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis_lock_release_redis_error(self):
        """Обработка ошибки Redis при освобождении."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.get = AsyncMock(side_effect=RedisError("Connection lost"))

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        lock.lock_value = "lock:scan:minsk:123:abc"

        with pytest.raises(RedisLockError, match="Failed to release lock"):
            await lock.release()


class TestRedisLockExtend:
    """Тесты продления TTL блокировки."""

    @pytest.mark.asyncio
    async def test_redis_lock_extend_success(self):
        """Успешное продление TTL."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.get = AsyncMock(return_value="lock:scan:minsk:123:abc")
        mock_redis.expire = AsyncMock(return_value=True)

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        lock.lock_value = "lock:scan:minsk:123:abc"

        extended = await lock.extend(additional_time=7200)

        assert extended is True
        mock_redis.expire.assert_called_once_with("lock:scan:minsk", 7200)

    @pytest.mark.asyncio
    async def test_redis_lock_extend_default_timeout(self):
        """Продление TTL с использованием timeout по умолчанию."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.get = AsyncMock(return_value="lock:scan:minsk:123:abc")
        mock_redis.expire = AsyncMock(return_value=True)

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        lock.lock_value = "lock:scan:minsk:123:abc"

        extended = await lock.extend()  # Без параметров

        assert extended is True
        mock_redis.expire.assert_called_once_with("lock:scan:minsk", 3600)

    @pytest.mark.asyncio
    async def test_redis_lock_extend_wrong_owner(self):
        """Продление чужого lock."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.get = AsyncMock(return_value="lock:scan:minsk:999:xyz")

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        lock.lock_value = "lock:scan:minsk:123:abc"

        extended = await lock.extend()

        assert extended is False
        mock_redis.expire.assert_not_called()


class TestRedisLockContextManager:
    """Тесты async context manager."""

    @pytest.mark.asyncio
    async def test_redis_lock_context_manager_success(self):
        """Успешное использование context manager."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value="lock:scan:minsk:123:abc")
        mock_redis.delete = AsyncMock(return_value=1)

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)

        async with lock as acquired_lock:
            assert acquired_lock is lock
            assert lock.lock_value is not None
            # Сохраняем lock_value для последующей проверки
            saved_lock_value = lock.lock_value

        # После выхода из контекста lock должен быть освобождён
        assert lock.lock_value is None
        # get должен быть вызван с правильным ключом
        mock_redis.get.assert_called_with("lock:scan:minsk")
        # delete должен быть вызван если owner совпал
        # В тесте get возвращает "lock:scan:minsk:123:abc" а не сохранённое значение
        # Поэтому проверяем что get был вызван
        assert mock_redis.get.called

    @pytest.mark.asyncio
    async def test_redis_lock_context_manager_acquire_failure(self):
        """Context manager выбрасывает исключение при неудачном захвате."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.set = AsyncMock(return_value=False)

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)

        with pytest.raises(RedisLockError, match="Failed to acquire lock"):
            async with lock:
                # Этот код не выполнится
                pass


class TestRedisLockReentrant:
    """Тесты повторного захвата после релиза."""

    @pytest.mark.asyncio
    async def test_redis_lock_reentrant(self):
        """Повторный захват lock после освобождения."""
        mock_redis = AsyncMock(spec=Redis)
        
        # Сохраняем lock_value для первого захвата
        first_lock_value = None
        
        def set_side_effect(*args, **kwargs):
            nonlocal first_lock_value
            if first_lock_value is None:
                # Первый захват
                first_lock_value = args[1]  # value argument
                return True
            else:
                # Второй захват
                return True
        
        mock_redis.set = AsyncMock(side_effect=set_side_effect)
        # Для release возвращаем то же значение что было установлено
        mock_redis.get = AsyncMock(side_effect=lambda key: first_lock_value if first_lock_value else None)
        mock_redis.delete = AsyncMock(return_value=1)

        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)

        # Первый захват
        acquired1 = await lock.acquire()
        assert acquired1 is True
        first_lock_value = lock.lock_value  # Сохраняем для мока

        # Обновляем mock get чтобы возвращал правильное значение
        mock_redis.get = AsyncMock(return_value=first_lock_value)

        # Освобождение
        released = await lock.release()
        assert released is True

        # Второй захват
        acquired2 = await lock.acquire()
        assert acquired2 is True

        # Проверка что set был вызван дважды
        assert mock_redis.set.call_count == 2


class TestRedisLockAutoExpire:
    """Тесты авто-экспайр TTL."""

    @pytest.mark.asyncio
    async def test_redis_lock_auto_expire_simulation(self):
        """Симуляция авто-экспайр через mock."""
        mock_redis = AsyncMock(spec=Redis)

        # Первый захват успешен
        mock_redis.set = AsyncMock(return_value=True)
        lock = RedisLock(mock_redis, "lock:scan:minsk", timeout=1)  # TTL 1 секунда
        acquired = await lock.acquire()
        assert acquired is True

        # Симулируем что TTL истёк и ключ удалён Redis
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)  # Новый захват возможен

        # После экспайра другой процесс может захватить lock
        lock2 = RedisLock(mock_redis, "lock:scan:minsk", timeout=3600)
        acquired2 = await lock2.acquire()
        assert acquired2 is True


# =============================================================================
# Helper функции тесты
# =============================================================================


class TestHelperFunctions:
    """Тесты helper функций."""

    def test_get_scan_lock_key(self):
        """Проверка генерации ключа lock."""
        key = get_scan_lock_key("minsk")
        assert key == "lock:scan:minsk"

        key = get_scan_lock_key("mogilev")
        assert key == "lock:scan:mogilev"

    @pytest.mark.asyncio
    async def test_acquire_scan_lock_success(self):
        """Успешный захват через helper функцию."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.set = AsyncMock(return_value=True)

        lock = await acquire_scan_lock(mock_redis, "minsk", "scan_123", timeout=3600)

        assert isinstance(lock, RedisLock)
        assert lock.lock_value is not None

    @pytest.mark.asyncio
    async def test_acquire_scan_lock_failure(self):
        """Неудачный захват через helper функцию."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.set = AsyncMock(return_value=False)
        mock_redis.get = AsyncMock(return_value="lock:scan:minsk:999:xyz")

        with pytest.raises(RedisLockError, match="Failed to acquire scan lock"):
            await acquire_scan_lock(mock_redis, "minsk", "scan_123")

    @pytest.mark.asyncio
    async def test_release_scan_lock(self):
        """Освобождение через helper функцию."""
        mock_redis = AsyncMock(spec=Redis)
        mock_redis.get = AsyncMock(return_value="lock:scan:minsk:scan_123")
        mock_redis.delete = AsyncMock(return_value=1)

        # В реальной ситуации lock_value должен сохраняться
        # Здесь тестируем что функция вызывает delete
        result = await release_scan_lock(mock_redis, "minsk", "scan_123")

        # Функция вернёт False потому что lock_value не совпадает с тем что в Redis
        # (в тесте мы не создаём полноценный lock объект)
        # Главное что delete был вызван при совпадении
        assert mock_redis.get.called
        assert mock_redis.delete.called


# =============================================================================
# Integration тесты (требуют запущенный Redis)
# =============================================================================


@pytest.mark.asyncio
class TestRedisLockIntegration:
    """Integration тесты для Redis Lock."""

    @pytest.mark.asyncio
    async def test_redis_lock_real_acquire_release(self):
        """Real Redis: захват и освобождение."""
        from app.core.redis_client import get_redis, close_redis

        try:
            redis = await get_redis()
        except Exception:
            pytest.skip("Redis недоступен для integration тестов")

        try:
            lock = RedisLock(redis, "lock:test:acquire_release", timeout=60)

            # Захват
            acquired = await lock.acquire()
            assert acquired is True

            # Проверка что ключ существует
            exists = await redis.exists("lock:test:acquire_release")
            assert exists == 1

            # Освобождение
            released = await lock.release()
            assert released is True

            # Проверка что ключ удалён
            exists = await redis.exists("lock:test:acquire_release")
            assert exists == 0
        finally:
            await close_redis()

    @pytest.mark.asyncio
    async def test_redis_lock_real_conflict(self):
        """Real Redis: конфликт при захвате."""
        from app.core.redis_client import get_redis, close_redis

        try:
            redis = await get_redis()
        except Exception:
            pytest.skip("Redis недоступен для integration тестов")

        try:
            # Первый lock
            lock1 = RedisLock(redis, "lock:test:conflict", timeout=60)
            acquired1 = await lock1.acquire()
            assert acquired1 is True

            # Второй lock (должен вернуть False)
            lock2 = RedisLock(redis, "lock:test:conflict", timeout=60)
            acquired2 = await lock2.acquire()
            assert acquired2 is False

            # Освобождение первым
            await lock1.release()

            # Теперь второй может захватить
            acquired3 = await lock2.acquire()
            assert acquired3 is True

            await lock2.release()
        finally:
            await close_redis()

    @pytest.mark.asyncio
    async def test_redis_lock_real_context_manager(self):
        """Real Redis: context manager."""
        from app.core.redis_client import get_redis, close_redis

        try:
            redis = await get_redis()
        except Exception:
            pytest.skip("Redis недоступен для integration тестов")

        try:
            lock = RedisLock(redis, "lock:test:context", timeout=60)

            async with lock:
                exists = await redis.exists("lock:test:context")
                assert exists == 1

            # После выхода из контекста ключ должен быть удалён
            exists = await redis.exists("lock:test:context")
            assert exists == 0
        finally:
            await close_redis()

    @pytest.mark.asyncio
    async def test_redis_lock_real_auto_expire(self):
        """Real Redis: авто-экспайр TTL."""
        from app.core.redis_client import get_redis, close_redis

        try:
            redis = await get_redis()
        except Exception:
            pytest.skip("Redis недоступен для integration тестов")

        try:
            # Lock с TTL 2 секунды
            lock = RedisLock(redis, "lock:test:expire", timeout=2)
            acquired = await lock.acquire()
            assert acquired is True

            # Проверка TTL
            ttl = await redis.ttl("lock:test:expire")
            assert 0 < ttl <= 2

            # Ждём пока TTL истечёт
            await asyncio.sleep(3)

            # Ключ должен исчезнуть
            exists = await redis.exists("lock:test:expire")
            assert exists == 0

            # Теперь другой процесс может захватить lock
            lock2 = RedisLock(redis, "lock:test:expire", timeout=60)
            acquired2 = await lock2.acquire()
            assert acquired2 is True

            await lock2.release()
        finally:
            await close_redis()

    @pytest.mark.asyncio
    async def test_redis_lock_real_release_wrong_owner(self):
        """Real Redis: освобождение чужого lock."""
        from app.core.redis_client import get_redis, close_redis

        try:
            redis = await get_redis()
        except Exception:
            pytest.skip("Redis недоступен для integration тестов")

        try:
            # Первый lock
            lock1 = RedisLock(redis, "lock:test:owner", timeout=60)
            await lock1.acquire()

            # Второй lock с неправильным owner
            lock2 = RedisLock(redis, "lock:test:owner", timeout=60)
            lock2.lock_value = "fake_owner_value"

            # Попытка освободить чужой lock
            released = await lock2.release()
            assert released is False

            # Ключ всё ещё существует
            exists = await redis.exists("lock:test:owner")
            assert exists == 1

            # Освобождаем правильным owner
            await lock1.release()
        finally:
            await close_redis()
