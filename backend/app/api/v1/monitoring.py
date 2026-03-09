"""
Redis Monitoring API endpoints.

Provides endpoints for monitoring Redis health, metrics, and performance.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, List, Any, Optional
import redis.asyncio as redis
from loguru import logger

from app.core.redis_client import get_redis

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/redis")
async def redis_monitoring(
    redis_client: redis.Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Мониторинг Redis: метрики, статистика, использование памяти.

    Возвращает комплексную информацию о состоянии Redis:
    - Статус подключения
    - Количество ключей
    - Cache hit/miss rate
    - Использование памяти
    - Подключенные клиенты
    - Uptime

    Returns:
        Dict с метриками Redis

    Example:
        GET /monitoring/redis

        Response:
        {
            "status": "healthy",
            "connected": true,
            "dbsize": 42,
            "cache": {
                "hits": 15234,
                "misses": 892,
                "hit_rate_percent": 94.48
            },
            "memory": {
                "used_mb": "2.3M",
                "peak_mb": "3.1M",
                "fragmentation": 1.05
            },
            "clients": {
                "connected": 5
            },
            "uptime": {
                "seconds": 86400,
                "days": 1.0
            }
        }
    """
    try:
        # Основная информация
        info = await redis_client.info()

        # Количество ключей
        dbsize = await redis_client.dbsize()

        # Статистика кэша
        stats_info = info.get("stats", {})
        keyspace_hits = stats_info.get("keyspace_hits", 0)
        keyspace_misses = stats_info.get("keyspace_misses", 0)
        total_ops = keyspace_hits + keyspace_misses
        hit_rate = (keyspace_hits / total_ops * 100) if total_ops > 0 else 0

        # Использование памяти
        memory_info = info.get("memory", {})
        memory = {
            "used_bytes": memory_info.get("used_memory", 0),
            "used_mb": memory_info.get("used_memory_human", "N/A"),
            "peak_bytes": memory_info.get("used_memory_peak", 0),
            "peak_mb": memory_info.get("used_memory_peak_human", "N/A"),
            "fragmentation": memory_info.get("mem_fragmentation_ratio", 0),
        }

        # Подключенные клиенты
        clients_info = info.get("clients", {})
        connected_clients = clients_info.get("connected_clients", 0)

        # Uptime
        server_info = info.get("server", {})
        uptime_seconds = server_info.get("uptime_in_seconds", 0)

        # Redis версия
        redis_version = server_info.get("redis_version", "N/A")

        return {
            "status": "healthy",
            "connected": True,
            "version": redis_version,
            "dbsize": dbsize,
            "cache": {
                "hits": keyspace_hits,
                "misses": keyspace_misses,
                "total_ops": total_ops,
                "hit_rate_percent": round(hit_rate, 2),
            },
            "memory": memory,
            "clients": {
                "connected": connected_clients,
            },
            "uptime": {
                "seconds": uptime_seconds,
                "days": round(uptime_seconds / 86400, 2),
            },
        }

    except Exception as e:
        logger.error(f"Redis monitoring error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Redis monitoring data: {str(e)}"
        )


@router.get("/redis/keys")
async def redis_keys(
    pattern: str = Query("*", description="Шаблон ключей (например, 'cache:*', 'lock:*')"),
    limit: int = Query(100, description="Максимум ключей для возврата", ge=1, le=1000),
    redis_client: redis.Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Список ключей Redis по шаблону.

    Возвращает информацию о ключах:
    - Имя ключа
    - Тип ключа (string, hash, list, set, zset)
    - TTL (время жизни в секундах)

    Args:
        pattern: Шаблон для поиска ключей (Redis glob pattern)
        limit: Максимальное количество ключей для возврата
        redis_client: Redis клиент

    Returns:
        Dict со списком ключей и их характеристиками

    Example:
        GET /monitoring/redis/keys?pattern=cache:*&limit=50

        Response:
        {
            "count": 5,
            "limit": 50,
            "pattern": "cache:*",
            "keys": [
                {
                    "key": "cache:stats:summary:get_summary:city=minsk",
                    "type": "string",
                    "ttl": 45
                },
                {
                    "key": "scan:progress:minsk",
                    "type": "hash",
                    "ttl": 7180
                }
            ]
        }
    """
    try:
        # Получаем ключи по шаблону
        keys = await redis_client.keys(pattern)

        # Ограничиваем количество
        keys = keys[:limit]

        # Получаем информацию о каждом ключе
        key_details = []
        for key in keys:
            try:
                key_type = await redis_client.type(key)
                ttl = await redis_client.ttl(key)

                key_details.append({
                    "key": key,
                    "type": key_type,
                    "ttl": ttl if ttl > 0 else -1,  # -1 если нет TTL
                })
            except Exception as e:
                logger.warning(f"Error getting details for key {key}: {e}")
                key_details.append({
                    "key": key,
                    "type": "unknown",
                    "ttl": -1,
                    "error": str(e),
                })

        return {
            "count": len(key_details),
            "limit": limit,
            "pattern": pattern,
            "keys": key_details,
        }

    except Exception as e:
        logger.error(f"Redis keys error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Redis keys: {str(e)}"
        )


@router.get("/redis/slowlog")
async def redis_slowlog(
    limit: int = Query(10, description="Количество записей", ge=1, le=100),
    redis_client: redis.Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Журнал медленных запросов Redis.

    Slowlog записывает запросы, которые выполнялись дольше
    заданного порога (по умолчанию 10ms).

    Args:
        limit: Количество записей для возврата
        redis_client: Redis клиент

    Returns:
        Dict с записями slowlog

    Example:
        GET /monitoring/redis/slowlog?limit=20

        Response:
        {
            "count": 3,
            "limit": 10,
            "entries": [
                {
                    "id": 1234,
                    "timestamp": 1709923847,
                    "duration_us": 15234,
                    "command": ["KEYS", "cache:*"],
                    "client": "127.0.0.1:12345"
                }
            ]
        }
    """
    try:
        # Получаем slowlog записи
        slowlog_data = await redis_client.slowlog_get(limit)
        
        # slowlog_get может возвращать dict или list в зависимости от версии redis-py
        if isinstance(slowlog_data, dict):
            slowlog = slowlog_data.get("value", [])
        else:
            slowlog = slowlog_data if slowlog_data else []

        # Форматируем записи
        entries = []
        for entry in slowlog:
            # entry формат: [id, timestamp, duration_us, command, client, ...]
            if isinstance(entry, (list, tuple)) and len(entry) >= 4:
                formatted_entry = {
                    "id": entry[0],
                    "timestamp": entry[1],
                    "duration_us": entry[2],  # Длительность в микросекундах
                    "command": entry[3] if isinstance(entry[3], list) else str(entry[3]),
                    "client": entry[4] if len(entry) > 4 else "N/A",
                }
                entries.append(formatted_entry)
            elif isinstance(entry, dict):
                # Если entry уже dict (новая версия redis-py)
                entries.append({
                    "id": entry.get("id"),
                    "timestamp": entry.get("start_time"),
                    "duration_us": entry.get("duration_microseconds"),
                    "command": entry.get("command"),
                    "client": entry.get("client_address", "N/A"),
                })

        return {
            "count": len(entries),
            "limit": limit,
            "entries": entries,
        }

    except Exception as e:
        logger.error(f"Redis slowlog error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Redis slowlog: {str(e)}"
        )


@router.get("/redis/memory")
async def redis_memory(
    redis_client: redis.Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Детальная информация об использовании памяти Redis.

    Returns:
        Dict с метриками памяти

    Example:
        GET /monitoring/redis/memory

        Response:
        {
            "used_memory": {
                "bytes": 2411724,
                "human": "2.3M",
                "rss_bytes": 3145728,
                "rss_human": "3.0M"
            },
            "peak_memory": {
                "bytes": 3145728,
                "human": "3.0M"
            },
            "fragmentation": {
                "ratio": 1.05,
                "waste_bytes": 102400
            },
            "allocator": {
                "allocated": 2400000,
                "active": 2500000,
                "resident": 3100000
            }
        }
    """
    try:
        info = await redis_client.info("memory")

        return {
            "used_memory": {
                "bytes": info.get("used_memory", 0),
                "human": info.get("used_memory_human", "N/A"),
                "rss_bytes": info.get("used_memory_rss", 0),
                "rss_human": info.get("used_memory_rss_human", "N/A"),
            },
            "peak_memory": {
                "bytes": info.get("used_memory_peak", 0),
                "human": info.get("used_memory_peak_human", "N/A"),
            },
            "fragmentation": {
                "ratio": info.get("mem_fragmentation_ratio", 0),
                "waste_bytes": info.get("mem_fragmentation_bytes", 0),
            },
            "allocator": {
                "allocated": info.get("allocator_allocated", 0),
                "active": info.get("allocator_active", 0),
                "resident": info.get("allocator_resident", 0),
            },
        }

    except Exception as e:
        logger.error(f"Redis memory error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Redis memory info: {str(e)}"
        )


@router.get("/redis/stats")
async def redis_stats(
    redis_client: redis.Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Статистика операций Redis.

    Returns:
        Dict со статистикой операций

    Example:
        GET /monitoring/redis/stats

        Response:
        {
            "commands": {
                "processed": 1234567,
                "per_second": 145.67
            },
            "connections": {
                "received": 2345,
                "rejected": 0
            },
            "keys": {
                "hits": 15234,
                "misses": 892,
                "expired": 123,
                "evicted": 0
            },
            "network": {
                "input_bytes": 12345678,
                "output_bytes": 87654321
            }
        }
    """
    try:
        info = await redis_client.info("stats")

        return {
            "commands": {
                "processed": info.get("total_commands_processed", 0),
                "per_second": info.get("instantaneous_ops_per_sec", 0),
            },
            "connections": {
                "received": info.get("total_connections_received", 0),
                "rejected": info.get("rejected_connections", 0),
            },
            "keys": {
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "expired": info.get("expired_keys", 0),
                "evicted": info.get("evicted_keys", 0),
            },
            "network": {
                "input_bytes": info.get("total_net_input_bytes", 0),
                "output_bytes": info.get("total_net_output_bytes", 0),
            },
        }

    except Exception as e:
        logger.error(f"Redis stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Redis stats: {str(e)}"
        )
