"""
Decorator для кэширования ответов API в Redis.

Обеспечивает прозрачное кэширование результатов async функций с настраиваемым TTL
и гибкой генерацией ключей на основе параметров функции.

Использование:
    @cache_response(prefix="stats:summary", ttl=60, key_params=["city"])
    async def get_stats_summary(city: str = Query(...)):
        # Существующая логика
        return {"data": "..."}
"""

from functools import wraps
from typing import Optional, Callable, Any, Dict, List
import redis.asyncio as redis
from redis.exceptions import RedisError
import json
import hashlib
from loguru import logger

from app.core.redis_client import get_redis


def _generate_cache_key(
    prefix: str,
    endpoint: str,
    params: Dict[str, Any],
    key_params: Optional[List[str]] = None
) -> str:
    """
    Генерирует уникальный ключ кэша на основе параметров.
    
    Args:
        prefix: Префикс ключа (например, "stats", "listings")
        endpoint: Имя endpoint (например, "summary", "price-trends")
        params: Все параметры функции
        key_params: Список параметров для формирования ключа (если None, используются все)
    
    Returns:
        Строка ключа в формате: {prefix}:{endpoint}:{param1}={value1}:{param2}={value2}
    """
    # Если key_params не указан, используем все параметры
    if key_params is None:
        filtered_params = params
    else:
        filtered_params = {k: v for k, v in params.items() if k in key_params}
    
    # Сортируем параметры для консистентности ключей
    sorted_params = sorted(filtered_params.items())
    
    # Формируем строку параметров
    param_str = ":".join(f"{k}={v}" for k, v in sorted_params if v is not None)
    
    # Если параметров нет, добавляем "default"
    if not param_str:
        param_str = "default"
    
    # Формируем итоговый ключ
    key = f"{prefix}:{endpoint}:{param_str}"
    
    return key


async def _get_from_cache(redis_client: redis.Redis, key: str) -> Optional[Any]:
    """
    Получает данные из кэша Redis.

    Args:
        redis_client: Redis клиент
        key: Ключ кэша

    Returns:
        Десериализованные данные или None если ключ не найден
    """
    try:
        cached_data = await redis_client.get(key)
        if cached_data is None:
            return None

        # Десериализация JSON
        deserialized = json.loads(cached_data)
        
        # Возвращаем dict/list - FastAPI сам валидирует через response_model
        # response_model автоматически сконвертирует dict в модель
        return deserialized
    except json.JSONDecodeError as e:
        logger.error(f"Failed to deserialize cache data for key {key}: {e}")
        return None
    except RedisError as e:
        logger.error(f"Redis error getting cache for key {key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting cache for key {key}: {e}")
        return None


async def _set_to_cache(
    redis_client: redis.Redis,
    key: str,
    data: Any,
    ttl: int
) -> bool:
    """
    Сохраняет данные в кэш Redis с указанным TTL.

    Args:
        redis_client: Redis клиент
        key: Ключ кэша
        data: Данные для сохранения (могут быть Pydantic моделью, dict, list)
        ttl: Время жизни кэша в секундах

    Returns:
        True если успешно, иначе False
    """
    try:
        # Сериализация JSON с поддержкой Pydantic моделей
        serialized_data = json.dumps(
            data,
            ensure_ascii=False,
            default=lambda o: o.model_dump() if hasattr(o, 'model_dump') else str(o)
        )

        # Установка с TTL
        await redis_client.setex(key, ttl, serialized_data)
        logger.debug(f"Cached data for key {key} with TTL {ttl}s")
        return True
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize data for cache key {key}: {e}")
        return False
    except RedisError as e:
        logger.error(f"Redis error setting cache for key {key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error setting cache for key {key}: {e}")
        return False


async def _invalidate_cache_pattern(
    redis_client: redis.Redis,
    pattern: str
) -> int:
    """
    Инвалидирует кэш по шаблону.
    
    Args:
        redis_client: Redis клиент
        pattern: Шаблон ключей (например, "stats:*", "listings:*")
    
    Returns:
        Количество удалённых ключей
    """
    try:
        # Поиск ключей по шаблону
        keys = await redis_client.keys(pattern)
        
        if not keys:
            logger.debug(f"No keys found for pattern {pattern}")
            return 0
        
        # Удаление ключей
        if keys:
            deleted_count = await redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted_count} cache keys for pattern {pattern}")
            return deleted_count
        
        return 0
    except RedisError as e:
        logger.error(f"Redis error invalidating cache for pattern {pattern}: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error invalidating cache for pattern {pattern}: {e}")
        return 0


def cache_response(
    prefix: str = "cache",
    ttl: int = 60,
    key_params: Optional[List[str]] = None
) -> Callable:
    """
    Decorator для кэширования ответов API в Redis.
    
    Args:
        prefix: Префикс ключа (например, "stats", "listings")
        ttl: Время жизни кэша в секундах
        key_params: Список параметров для формирования ключа (если None, используются все query params)
    
    Returns:
        Decorator function
    
    Example:
        @router.get("/summary")
        @cache_response(prefix="stats:summary", ttl=60, key_params=["city"])
        async def get_stats_summary(city: str = Query(...)):
            return {"data": "..."}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Извлекаем параметр request из kwargs (FastAPI Request)
            request = kwargs.get("request")
            
            # Получаем Redis клиент
            try:
                redis_client = await get_redis()
                redis_available = True
            except Exception as e:
                logger.warning(f"Redis not available, skipping cache for {func.__name__}: {e}")
                redis_available = False
                redis_client = None
            
            # Формируем ключ кэша
            endpoint_name = func.__name__
            
            # Извлекаем query параметры из request если доступен, иначе из kwargs
            if request and hasattr(request, "query_params"):
                params = dict(request.query_params)
            else:
                # Фильтруем служебные параметры
                params = {
                    k: v for k, v in kwargs.items()
                    if k not in ["db", "request", "skip", "limit"]
                    and v is not None
                }
            
            cache_key = _generate_cache_key(prefix, endpoint_name, params, key_params)
            
            # Попытка получить из кэша
            if redis_available:
                cached_result = await _get_from_cache(redis_client, cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key {cache_key}")
                    return cached_result
            
            # Кэш miss - вызываем функцию
            logger.debug(f"Cache miss for key {cache_key}, calling function")
            result = await func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            if redis_available and result is not None:
                await _set_to_cache(redis_client, cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Экспорт функций для использования в других модулях
__all__ = [
    "cache_response",
    "_generate_cache_key",
    "_get_from_cache",
    "_set_to_cache",
    "_invalidate_cache_pattern",
]
