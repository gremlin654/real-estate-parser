"""Тестовый скрипт для проверки подключения к Redis"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.core.redis_client import get_redis, health_check_redis, close_redis


async def test_redis():
    """Тест подключения к Redis"""
    print("=" * 50)
    print("Тест подключения к Redis")
    print("=" * 50)
    
    try:
        # Получаем подключение
        redis = await get_redis()
        print(f"✓ Connected to Redis: {redis}")
        
        # Health check
        result = await health_check_redis()
        print(f"✓ Health check: {result}")
        
        # SET test
        await redis.set('test_key', 'hello_from_backend')
        print("✓ SET test_key = 'hello_from_backend'")
        
        # GET test
        val = await redis.get('test_key')
        print(f"✓ GET test_key: {val}")
        
        # SETEX test (TTL)
        await redis.setex('test_key_ttl', 60, 'value_with_ttl')
        ttl = await redis.ttl('test_key_ttl')
        print(f"✓ SETEX test_key_ttl (TTL={ttl}s)")
        
        # EXISTS test
        exists = await redis.exists('test_key')
        print(f"✓ EXISTS test_key: {exists == 1}")
        
        # DELETE test
        await redis.delete('test_key')
        exists_after = await redis.exists('test_key')
        print(f"✓ DELETE test_key, EXISTS after: {exists_after == 0}")
        
        print("=" * 50)
        print("Все тесты пройдены успешно!")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await close_redis()
        print("✓ Redis connection closed")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_redis())
    sys.exit(0 if success else 1)
