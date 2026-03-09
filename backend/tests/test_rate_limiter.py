"""
Tests for Token Bucket Rate Limiter.

Unit тесты:
- test_rate_limiter_acquire_success — успешный захват токенов
- test_rate_limiter_acquire_wait — ожидание при нехватке токенов
- test_rate_limiter_refill — пополнение токенов со временем
- test_rate_limiter_capacity_limit — ограничение capacity
- test_rate_limiter_multiple_identifiers — разные идентификаторы
- test_rate_limiter_get_tokens — получение количества токенов
- test_rate_limiter_ttl_set — проверка TTL ключей
- test_rate_limiter_wait_and_acquire — wait_and_acquire()

Integration тесты:
- test_scraper_uses_rate_limiter — scraper использует rate limiter
- test_rate_limiter_concurrent_requests — конкурентные запросы
- test_rate_limiter_burst_allowed — burst запросы разрешены
- test_rate_limiter_sustained_rate — устойчивая частота
"""

import pytest
import asyncio
import time
import redis.asyncio as redis
from app.core.rate_limiter import TokenBucketRateLimiter, get_rate_limiter
from app.config import settings


@pytest.fixture
async def redis_client():
    """Fixture для Redis клиента (использует тестовую БД)."""
    client = redis.from_url(
        settings.REDIS_TEST_URL,
        encoding="utf-8",
        decode_responses=True
    )
    await client.ping()
    yield client
    # Очистка ключей rate limiter после теста
    keys = await client.keys("ratelimit:test:*")
    if keys:
        await client.delete(*keys)
    await client.close()


@pytest.fixture
async def rate_limiter(redis_client):
    """Fixture для rate limiter с тестовыми параметрами."""
    limiter = await get_rate_limiter(
        redis_client,
        key_prefix="ratelimit:test",
        capacity=5,        # 5 токенов для тестов
        refill_rate=2.0    # 2 токена в секунду для быстрых тестов
    )
    yield limiter
    # Сброс после теста
    await limiter.reset("default")


class TestTokenBucketRateLimiter:
    """Unit тесты для TokenBucketRateLimiter."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_success(self, rate_limiter):
        """Успешный захват токенов без ожидания."""
        # Первый запрос должен пройти сразу
        wait_time = await rate_limiter.acquire("default", tokens=1)
        
        assert wait_time == 0.0, "Первый запрос должен пройти без ожидания"
        
        # Проверяем что токены уменьшились
        tokens = await rate_limiter.get_tokens("default")
        assert tokens < 5.0, "Токены должны были уменьшиться"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_wait(self, redis_client):
        """Ожидание при нехватке токенов."""
        # Создаём лимитер с очень медленным пополнением
        limiter = await get_rate_limiter(
            redis_client,
            key_prefix="ratelimit:test:wait",
            capacity=5,
            refill_rate=0.1  # 1 токен за 10 секунд
        )
        
        identifier = "wait_test"
        
        # Потребляем все токены
        for _ in range(5):
            await limiter.acquire(identifier, tokens=1)
        
        # Следующий запрос должен ждать
        wait_time = await limiter.acquire(identifier, tokens=1)
        
        assert wait_time > 0, "Должно быть ожидание при нехватке токенов"
        assert wait_time <= 15.0, f"Время ожидания должно быть разумным: {wait_time}"
        
        # Очистка
        await limiter.reset(identifier)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_refill(self, rate_limiter):
        """Пополнение токенов со временем."""
        identifier = "refill_test"
        
        # Потребляем все токены
        for _ in range(5):
            await rate_limiter.acquire(identifier, tokens=1)
        
        # Ждём 1 секунду (должно добавиться 2 токена при refill_rate=2.0)
        await asyncio.sleep(1.0)
        
        # Проверяем количество токенов
        tokens = await rate_limiter.get_tokens(identifier)
        
        # Должно быть примерно 2 токена (с небольшой погрешностью)
        assert 1.5 <= tokens <= 2.5, f"Ожидаем ~2 токена после 1 секунды, получено: {tokens}"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_capacity_limit(self, rate_limiter):
        """Ограничение capacity (не больше максимального количества)."""
        identifier = "capacity_test"
        
        # Ждём долгое время (токены должны пополниться до capacity)
        await asyncio.sleep(3.0)
        
        tokens = await rate_limiter.get_tokens(identifier)
        
        # Не должно быть больше capacity
        assert tokens <= 5.0, f"Токены не должны превышать capacity: {tokens}"
        assert tokens >= 4.5, f"Токены должны быть близки к capacity после ожидания: {tokens}"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_multiple_identifiers(self, rate_limiter):
        """Разные идентификаторы имеют независимые счётчики."""
        # Потребляем токены для первого идентификатора
        for _ in range(3):
            await rate_limiter.acquire("identifier_1", tokens=1)
        
        # Второй идентификатор должен иметь полные токены
        tokens_1 = await rate_limiter.get_tokens("identifier_1")
        tokens_2 = await rate_limiter.get_tokens("identifier_2")
        
        assert tokens_1 < 5.0, "Первый идентификатор должен иметь меньше токенов"
        assert tokens_2 == 5.0, "Второй идентификатор должен иметь полные токены"
        assert tokens_2 > tokens_1, "Токены должны быть независимыми"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_get_tokens(self, rate_limiter):
        """Получение текущего количества токенов."""
        identifier = "get_tokens_test"
        
        # Начальное состояние
        initial_tokens = await rate_limiter.get_tokens(identifier)
        assert initial_tokens == 5.0, f"Начальное количество токенов должно быть 5: {initial_tokens}"
        
        # Потребляем 2 токена
        await rate_limiter.acquire(identifier, tokens=2)
        
        # Проверяем
        tokens = await rate_limiter.get_tokens(identifier)
        assert 2.5 <= tokens <= 3.5, f"Должно остаться ~3 токена: {tokens}"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_ttl_set(self, redis_client, rate_limiter):
        """Проверка TTL ключей."""
        identifier = "ttl_test"
        
        # Делаем запрос для создания ключей
        await rate_limiter.acquire(identifier, tokens=1)
        
        # Проверяем TTL
        tokens_key = f"ratelimit:test:{identifier}:tokens"
        ttl = await redis_client.ttl(tokens_key)
        
        assert ttl > 0, "TTL должен быть установлен"
        assert ttl <= 3600, f"TTL не должен превышать 1 час: {ttl}"
        assert ttl >= 3590, f"TTL должен быть близок к 1 часу: {ttl}"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_wait_and_acquire(self, redis_client):
        """Тест wait_and_acquire с ожиданием."""
        limiter = await get_rate_limiter(
            redis_client,
            key_prefix="ratelimit:test:wait_acquire",
            capacity=5,
            refill_rate=0.5  # 1 токен за 2 секунды
        )
        
        identifier = "wait_acquire_test"
        
        # Потребляем все токены
        for _ in range(5):
            await limiter.acquire(identifier, tokens=1)
        
        # Замеряем время выполнения wait_and_acquire
        start_time = time.time()
        await limiter.wait_and_acquire(identifier, tokens=1)
        elapsed = time.time() - start_time
        
        # Должно пройти некоторое время (1 токен / 0.5 токена-в-секунду = 2 секунды)
        assert elapsed > 1.5, f"Должно быть ожидание: {elapsed}s"
        assert elapsed < 3.0, f"Ожидание не должно быть слишком долгим: {elapsed}s"
        
        # Очистка
        await limiter.reset(identifier)


class TestRateLimiterIntegration:
    """Integration тесты для rate limiter."""
    
    @pytest.mark.asyncio
    async def test_scraper_uses_rate_limiter(self, redis_client):
        """Scraper использует rate limiter."""
        from app.scraper.kufar_scraper import KufarScraper
        
        scraper = KufarScraper()
        await scraper.initialize(redis_client)
        
        assert scraper.rate_limiter is not None, "Rate limiter должен быть инициализирован"
        assert isinstance(scraper.rate_limiter, TokenBucketRateLimiter), \
            "Rate limiter должен быть правильным типом"
        
        await scraper.close()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent_requests(self, redis_client):
        """Конкурентные запросы корректно обрабатываются."""
        limiter = await get_rate_limiter(
            redis_client,
            key_prefix="ratelimit:test:concurrent",
            capacity=10,
            refill_rate=1.0  # Медленное пополнение для теста
        )
        
        results = []
        
        async def make_request():
            start = time.time()
            await limiter.wait_and_acquire("concurrent_test", tokens=1)
            elapsed = time.time() - start
            results.append(elapsed)
        
        # Запускаем 15 конкурентных запросов
        tasks = [make_request() for _ in range(15)]
        await asyncio.gather(*tasks)
        
        # Первые 10 должны пройти сразу (или с минимальной задержкой)
        # Остальные 5 должны ждать
        immediate_requests = sum(1 for t in results if t < 0.5)
        delayed_requests = sum(1 for t in results if t >= 0.5)
        
        assert immediate_requests >= 9, f"Хотя бы 9 запросов должны пройти сразу: {immediate_requests}"
        assert delayed_requests >= 1, f"Хотя бы 1 запрос должен ждать: {delayed_requests}"
        
        # Очистка
        await limiter.reset("concurrent_test")
    
    @pytest.mark.asyncio
    async def test_rate_limiter_burst_allowed(self, redis_client):
        """Burst запросы разрешены в пределах capacity."""
        limiter = await get_rate_limiter(
            redis_client,
            key_prefix="ratelimit:test:burst",
            capacity=10,
            refill_rate=1.0  # Медленное пополнение
        )
        
        start_time = time.time()
        
        # Быстро потребляем все токены (burst)
        for _ in range(10):
            wait_time = await limiter.acquire("burst_test", tokens=1)
            assert wait_time == 0.0, "Burst запросы должны проходить без ожидания"
        
        elapsed = time.time() - start_time
        
        # Все 10 запросов должны пройти быстро (< 0.5 секунды)
        assert elapsed < 0.5, f"Burst запросы должны быть быстрыми: {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_sustained_rate(self, redis_client):
        """Проверка устойчивой частоты запросов."""
        limiter = await get_rate_limiter(
            redis_client,
            key_prefix="ratelimit:test:sustained",
            capacity=5,
            refill_rate=5.0  # 5 токенов в секунду
        )
        
        # Делаем 10 запросов с ожиданием
        start_time = time.time()
        
        for _ in range(10):
            await limiter.wait_and_acquire("sustained_test", tokens=1)
        
        elapsed = time.time() - start_time
        
        # Первые 5 пройдут сразу, остальные 5 будут ждать
        # Общее время должно быть примерно 1 секунда (5 токенов / 5 токенов-в-секунду)
        assert elapsed >= 0.5, f"Минимальное время для 10 запросов: {elapsed}s"
        assert elapsed <= 3.0, f"Максимальное время для 10 запросов: {elapsed}s"
        
        # Очистка
        await limiter.reset("sustained_test")


class TestRateLimiterEdgeCases:
    """Тесты граничных случаев."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_multiple_tokens(self, rate_limiter):
        """Запрос нескольких токенов одновременно."""
        identifier = "multi_token_test"
        
        # Запрашиваем 3 токена сразу
        wait_time = await rate_limiter.acquire(identifier, tokens=3)
        
        assert wait_time == 0.0, "3 токена должны быть доступны сразу"
        
        tokens = await rate_limiter.get_tokens(identifier)
        assert 1.5 <= tokens <= 2.5, f"Должно остаться ~2 токена: {tokens}"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_reset(self, rate_limiter):
        """Сброс токенов."""
        identifier = "reset_test"
        
        # Потребляем токены
        await rate_limiter.acquire(identifier, tokens=3)
        tokens_before = await rate_limiter.get_tokens(identifier)
        
        # Сбрасываем
        await rate_limiter.reset(identifier)
        tokens_after = await rate_limiter.get_tokens(identifier)
        
        assert tokens_before < 5.0, "До сброса токенов должно быть меньше"
        assert tokens_after == 5.0, f"После сброса должно быть 5 токенов: {tokens_after}"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_atomic_lua_script(self, redis_client):
        """Проверка атомарности Lua скрипта."""
        limiter = await get_rate_limiter(
            redis_client,
            key_prefix="ratelimit:test:atomic",
            capacity=100,
            refill_rate=1.0  # Медленное пополнение
        )
        
        identifier = "atomic_test"
        
        # Делаем много конкурентных запросов
        async def acquire_token():
            return await limiter.acquire(identifier, tokens=1)
        
        tasks = [acquire_token() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Все должны пройти без ожидания
        assert all(r == 0.0 for r in results), "Все запросы должны пройти без ожидания"
        
        # Проверяем что токены корректно уменьшились
        # С учётом небольшого времени выполнения и refill_rate=1.0, должно остаться ~50
        tokens = await limiter.get_tokens(identifier)
        assert 45.0 <= tokens <= 55.0, f"Должно остаться ~50 токенов: {tokens}"
        
        # Очистка
        await limiter.reset(identifier)
