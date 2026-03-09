"""
Cache Management API endpoints.

Provides endpoints for cache invalidation and management.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
import redis.asyncio as redis
from loguru import logger

from app.core.redis_client import get_redis
from app.decorators.cache import _invalidate_cache_pattern

router = APIRouter(prefix="/cache", tags=["cache-management"])


@router.delete("/invalidate")
async def invalidate_cache(
    pattern: str = Query(
        ...,
        description="Шаблон ключей для удаления (например, 'stats:*' или 'listings:*')",
    ),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Инвалидация кэша по шаблону.

    Используется после сканирования для обновления данных.

    Args:
        pattern: Шаблон ключей для удаления (например, 'cache:stats:*', 'cache:listings:*')
        redis_client: Redis клиент (dependency injection)

    Returns:
        Количество удалённых ключей

    Example:
        # Инвалидировать весь кэш stats
        DELETE /api/v1/cache/invalidate?pattern=cache:stats:*

        # Инвалидировать кэш для конкретного города
        DELETE /api/v1/cache/invalidate?pattern=cache:stats:summary:city=minsk

        # Инвалидировать весь кэш listings
        DELETE /api/v1/cache/invalidate?pattern=cache:listings:*
    """
    try:
        # Добавляем префикс если его нет в шаблоне
        # Поддерживаем оба формата: "stats:*" и "cache:stats:*"
        if not pattern.startswith("cache:"):
            pattern = f"cache:{pattern}"
        elif pattern.startswith("cache:cache:"):
            # Исправляем дублирование префикса
            pattern = pattern[6:]

        deleted_count = await _invalidate_cache_pattern(redis_client, pattern)

        return {
            "success": True,
            "pattern": pattern,
            "keys_deleted": deleted_count,
            "message": f"Successfully invalidated {deleted_count} cache keys",
        }
    except Exception as e:
        logger.error(f"Cache invalidation error for pattern {pattern}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.get("/stats")
async def get_cache_stats(redis_client: redis.Redis = Depends(get_redis)):
    """
    Получение статистики по кэшу.

    Returns:
        Статистика по использованию кэша
    """
    try:
        # Получаем все ключи с префиксом "cache:"
        all_keys = await redis_client.keys("cache:*")

        # Группируем по префиксам
        stats = {"total_keys": len(all_keys), "by_prefix": {}}

        # Анализируем ключи по префиксам
        for key in all_keys:
            parts = key.split(":")
            if len(parts) >= 2:
                prefix = f"cache:{parts[1]}"
                if prefix not in stats["by_prefix"]:
                    stats["by_prefix"][prefix] = 0
                stats["by_prefix"][prefix] += 1

        # Получаем информацию о памяти (если доступно)
        try:
            info = await redis_client.info("memory")
            stats["memory_used_bytes"] = info.get("used_memory", 0)
        except Exception:
            pass

        return stats
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache stats: {str(e)}"
        )


@router.post("/clear/all")
async def clear_all_cache(redis_client: redis.Redis = Depends(get_redis)):
    """
    Полная очистка всего кэша.

    WARNING: Удаляет ВСЕ ключи с префиксом "cache:".
    Используйте с осторожностью в production!

    Returns:
        Количество удалённых ключей
    """
    try:
        deleted_count = await _invalidate_cache_pattern(redis_client, "cache:*")

        return {
            "success": True,
            "keys_deleted": deleted_count,
            "message": f"Successfully cleared all cache ({deleted_count} keys)",
        }
    except Exception as e:
        logger.error(f"Clear all cache error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
