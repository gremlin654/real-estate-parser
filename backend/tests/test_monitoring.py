"""
Tests for Redis Monitoring API endpoints.

Unit tests:
- test_redis_monitoring_endpoint — проверка /monitoring/redis
- test_redis_monitoring_structure — структура ответа
- test_redis_keys_endpoint — проверка /monitoring/redis/keys
- test_redis_keys_endpoint_custom_pattern — кастомный шаблон
- test_redis_slowlog_endpoint — проверка /monitoring/redis/slowlog
- test_redis_memory_endpoint — проверка /monitoring/redis/memory
- test_redis_stats_endpoint — проверка /monitoring/redis/stats

Integration tests:
- test_redis_monitoring_integration — integration test с реальным Redis
- test_redis_keys_integration — работа с ключами
- test_redis_monitoring_error_handling — обработка ошибок
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

from app.core.redis_client import get_redis, close_redis


# ============================================================================
# Unit Tests: Mock Redis
# ============================================================================

class TestRedisMonitoringUnit:
    """Unit тесты для Redis monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_redis_monitoring_endpoint(self, client):
        """Проверка endpoint /monitoring/redis."""
        # Мокаем Redis info
        mock_info = {
            "stats": {
                "keyspace_hits": 15234,
                "keyspace_misses": 892,
            },
            "memory": {
                "used_memory": 2411724,
                "used_memory_human": "2.3M",
                "used_memory_peak": 3145728,
                "used_memory_peak_human": "3.0M",
                "mem_fragmentation_ratio": 1.05,
            },
            "clients": {
                "connected_clients": 5,
            },
            "server": {
                "uptime_in_seconds": 86400,
                "redis_version": "7.2.4",
            },
        }

        with patch('app.api.v1.monitoring.redis.Redis.info', new_callable=AsyncMock) as mock_info_method:
            mock_info_method.return_value = mock_info
            
            with patch('app.api.v1.monitoring.redis.Redis.dbsize', new_callable=AsyncMock) as mock_dbsize:
                mock_dbsize.return_value = 42
                
                response = await client.get("/monitoring/redis")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["status"] == "healthy"
                assert data["connected"] is True
                assert data["version"] == "7.2.4"
                assert data["dbsize"] == 42
                assert "cache" in data
                assert "memory" in data
                assert "clients" in data
                assert "uptime" in data

    @pytest.mark.asyncio
    async def test_redis_monitoring_structure(self, client):
        """Проверка структуры ответа /monitoring/redis."""
        mock_info = {
            "stats": {"keyspace_hits": 100, "keyspace_misses": 10},
            "memory": {"used_memory_human": "1M", "used_memory_peak_human": "2M", "mem_fragmentation_ratio": 1.1},
            "clients": {"connected_clients": 3},
            "server": {"uptime_in_seconds": 3600, "redis_version": "7.0.0"},
        }

        with patch('app.api.v1.monitoring.redis.Redis.info', new_callable=AsyncMock, return_value=mock_info):
            with patch('app.api.v1.monitoring.redis.Redis.dbsize', new_callable=AsyncMock, return_value=10):
                response = await client.get("/monitoring/redis")
                data = response.json()
                
                # Проверка структуры
                assert "status" in data
                assert "connected" in data
                assert "version" in data
                assert "dbsize" in data
                
                assert "cache" in data
                assert "hits" in data["cache"]
                assert "misses" in data["cache"]
                assert "total_ops" in data["cache"]
                assert "hit_rate_percent" in data["cache"]
                
                assert "memory" in data
                assert "used_bytes" in data["memory"]
                assert "used_mb" in data["memory"]
                assert "peak_bytes" in data["memory"]
                assert "peak_mb" in data["memory"]
                assert "fragmentation" in data["memory"]
                
                assert "clients" in data
                assert "connected" in data["clients"]
                
                assert "uptime" in data
                assert "seconds" in data["uptime"]
                assert "days" in data["uptime"]

    @pytest.mark.asyncio
    async def test_redis_monitoring_cache_hit_rate_calculation(self, client):
        """Проверка расчёта cache hit rate."""
        mock_info = {
            "stats": {"keyspace_hits": 900, "keyspace_misses": 100},
            "memory": {"used_memory_human": "1M"},
            "clients": {"connected_clients": 1},
            "server": {"uptime_in_seconds": 100, "redis_version": "7.0.0"},
        }

        with patch('app.api.v1.monitoring.redis.Redis.info', new_callable=AsyncMock, return_value=mock_info):
            with patch('app.api.v1.monitoring.redis.Redis.dbsize', new_callable=AsyncMock, return_value=5):
                response = await client.get("/monitoring/redis")
                data = response.json()
                
                # 900 / (900 + 100) * 100 = 90%
                assert data["cache"]["hit_rate_percent"] == 90.0
                assert data["cache"]["hits"] == 900
                assert data["cache"]["misses"] == 100
                assert data["cache"]["total_ops"] == 1000

    @pytest.mark.asyncio
    async def test_redis_keys_endpoint(self, client):
        """Проверка endpoint /monitoring/redis/keys."""
        mock_keys = [
            "cache:stats:summary:get_summary:city=minsk",
            "cache:stats:price-trends:get_price_trends:city=minsk:rooms=2",
            "scan:progress:minsk",
        ]
        
        mock_type = AsyncMock(side_effect=["string", "string", "hash"])
        mock_ttl = AsyncMock(side_effect=[45, 120, 7180])

        with patch('app.api.v1.monitoring.redis.Redis.keys', new_callable=AsyncMock, return_value=mock_keys):
            with patch('app.api.v1.monitoring.redis.Redis.type', mock_type):
                with patch('app.api.v1.monitoring.redis.Redis.ttl', mock_ttl):
                    response = await client.get("/monitoring/redis/keys?pattern=cache:*")
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["count"] == 3
                    assert data["limit"] == 100
                    assert data["pattern"] == "cache:*"
                    assert len(data["keys"]) == 3
                    
                    # Проверка структуры ключа
                    key = data["keys"][0]
                    assert "key" in key
                    assert "type" in key
                    assert "ttl" in key

    @pytest.mark.asyncio
    async def test_redis_keys_endpoint_custom_pattern(self, client):
        """Проверка /monitoring/redis/keys с кастомным шаблоном."""
        mock_keys = ["lock:scan:minsk", "lock:scan:mogilev"]
        
        with patch('app.api.v1.monitoring.redis.Redis.keys', new_callable=AsyncMock, return_value=mock_keys):
            with patch('app.api.v1.monitoring.redis.Redis.type', new_callable=AsyncMock, return_value="string"):
                with patch('app.api.v1.monitoring.redis.Redis.ttl', new_callable=AsyncMock, return_value=3600):
                    response = await client.get("/monitoring/redis/keys?pattern=lock:*&limit=10")
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["pattern"] == "lock:*"
                    assert data["limit"] == 10
                    assert data["count"] == 2

    @pytest.mark.asyncio
    async def test_redis_keys_endpoint_limit(self, client):
        """Проверка ограничения количества ключей."""
        mock_keys = [f"cache:key:{i}" for i in range(200)]
        
        with patch('app.api.v1.monitoring.redis.Redis.keys', new_callable=AsyncMock, return_value=mock_keys):
            with patch('app.api.v1.monitoring.redis.Redis.type', new_callable=AsyncMock, return_value="string"):
                with patch('app.api.v1.monitoring.redis.Redis.ttl', new_callable=AsyncMock, return_value=-1):
                    response = await client.get("/monitoring/redis/keys?pattern=cache:*&limit=50")
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    assert data["count"] == 50
                    assert data["limit"] == 50

    @pytest.mark.asyncio
    async def test_redis_slowlog_endpoint(self, client):
        """Проверка endpoint /monitoring/redis/slowlog."""
        # Формат slowlog: [id, timestamp, duration_us, command, client]
        mock_slowlog = [
            [1234, 1709923847, 15234, ["KEYS", "cache:*"], "127.0.0.1:12345"],
            [1233, 1709923800, 5000, ["GET", "cache:stats:..."], "127.0.0.1:12345"],
        ]

        with patch('app.api.v1.monitoring.redis.Redis.slowlog_get', new_callable=AsyncMock, return_value=mock_slowlog):
            response = await client.get("/monitoring/redis/slowlog?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["count"] == 2
            assert data["limit"] == 10
            assert len(data["entries"]) == 2
            
            # Проверка структуры записи
            entry = data["entries"][0]
            assert entry["id"] == 1234
            assert entry["timestamp"] == 1709923847
            assert entry["duration_us"] == 15234
            assert entry["command"] == ["KEYS", "cache:*"]
            assert entry["client"] == "127.0.0.1:12345"

    @pytest.mark.asyncio
    async def test_redis_memory_endpoint(self, client):
        """Проверка endpoint /monitoring/redis/memory."""
        mock_info = {
            "used_memory": 2411724,
            "used_memory_human": "2.3M",
            "used_memory_rss": 3145728,
            "used_memory_rss_human": "3.0M",
            "used_memory_peak": 3145728,
            "used_memory_peak_human": "3.0M",
            "mem_fragmentation_ratio": 1.05,
            "mem_fragmentation_bytes": 102400,
            "allocator_allocated": 2400000,
            "allocator_active": 2500000,
            "allocator_resident": 3100000,
        }

        with patch('app.api.v1.monitoring.redis.Redis.info', new_callable=AsyncMock, return_value=mock_info):
            response = await client.get("/monitoring/redis/memory")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "used_memory" in data
            assert data["used_memory"]["bytes"] == 2411724
            assert data["used_memory"]["human"] == "2.3M"
            
            assert "peak_memory" in data
            assert data["peak_memory"]["bytes"] == 3145728
            
            assert "fragmentation" in data
            assert data["fragmentation"]["ratio"] == 1.05
            
            assert "allocator" in data

    @pytest.mark.asyncio
    async def test_redis_stats_endpoint(self, client):
        """Проверка endpoint /monitoring/redis/stats."""
        mock_info = {
            "total_commands_processed": 1234567,
            "instantaneous_ops_per_sec": 145,
            "total_connections_received": 2345,
            "rejected_connections": 0,
            "keyspace_hits": 15234,
            "keyspace_misses": 892,
            "expired_keys": 123,
            "evicted_keys": 0,
            "total_net_input_bytes": 12345678,
            "total_net_output_bytes": 87654321,
        }

        with patch('app.api.v1.monitoring.redis.Redis.info', new_callable=AsyncMock, return_value=mock_info):
            response = await client.get("/monitoring/redis/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "commands" in data
            assert data["commands"]["processed"] == 1234567
            assert data["commands"]["per_second"] == 145
            
            assert "connections" in data
            assert data["connections"]["received"] == 2345
            assert data["connections"]["rejected"] == 0
            
            assert "keys" in data
            assert data["keys"]["hits"] == 15234
            assert data["keys"]["misses"] == 892

    @pytest.mark.asyncio
    async def test_redis_monitoring_error_handling(self, client):
        """Проверка обработки ошибок в monitoring endpoints."""
        with patch('app.api.v1.monitoring.redis.Redis.info', new_callable=AsyncMock, side_effect=Exception("Redis error")):
            response = await client.get("/monitoring/redis")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


# ============================================================================
# Integration Tests: Real Redis
# ============================================================================

@pytest.mark.asyncio
class TestRedisMonitoringIntegration:
    """Integration тесты для Redis monitoring endpoints."""

    @pytest.mark.skip(reason="Requires running Redis instance")
    async def test_redis_monitoring_integration(self, client):
        """Integration test с реальным Redis."""
        redis_client = await get_redis()
        
        try:
            # Очистка перед тестом
            await redis_client.flushdb()
            
            # Добавляем тестовые данные
            await redis_client.set("cache:test:key1", "value1")
            await redis_client.set("cache:test:key2", "value2")
            
            # Получаем monitoring данные
            response = await client.get("/monitoring/redis")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["connected"] is True
            assert data["dbsize"] >= 2
            
        finally:
            # Очистка после теста
            await redis_client.flushdb()

    @pytest.mark.skip(reason="Requires running Redis instance")
    async def test_redis_keys_integration(self, client):
        """Integration test для /monitoring/redis/keys."""
        redis_client = await get_redis()
        
        try:
            # Очистка
            await redis_client.flushdb()
            
            # Добавляем тестовые ключи
            await redis_client.setex("cache:test:key1", 300, "value1")
            await redis_client.setex("cache:test:key2", 600, "value2")
            await redis_client.hset("scan:progress:test", mapping={"stage": "fetching"})
            
            # Получаем ключи
            response = await client.get("/monitoring/redis/keys?pattern=cache:test:*")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["count"] == 2
            assert data["pattern"] == "cache:test:*"
            
            # Проверка TTL
            for key in data["keys"]:
                assert key["ttl"] > 0
                
        finally:
            await redis_client.flushdb()

    @pytest.mark.skip(reason="Requires running Redis instance")
    async def test_redis_monitoring_hit_rate_zero_ops(self, client):
        """Проверка hit rate при отсутствии операций."""
        redis_client = await get_redis()
        
        try:
            await redis_client.flushdb()
            
            response = await client.get("/monitoring/redis")
            assert response.status_code == 200
            
            data = response.json()
            # При отсутствии операций hit rate должен быть 0
            assert data["cache"]["hit_rate_percent"] == 0
            
        finally:
            await redis_client.flushdb()
