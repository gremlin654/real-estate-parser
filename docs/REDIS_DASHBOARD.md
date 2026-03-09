# Redis Monitoring Dashboard

## Health Check

### Basic Health Check

```bash
curl http://localhost:8000/monitoring/redis
```

**Пример ответа:**
```json
{
  "status": "healthy",
  "connected": true,
  "version": "7.2.4",
  "dbsize": 42,
  "cache": {
    "hits": 15234,
    "misses": 892,
    "total_ops": 16126,
    "hit_rate_percent": 94.48
  },
  "memory": {
    "used_bytes": 2411724,
    "used_mb": "2.3M",
    "peak_bytes": 3145728,
    "peak_mb": "3.0M",
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
```

### Detailed Endpoints

```bash
# Список ключей
curl "http://localhost:8000/monitoring/redis/keys?pattern=cache:*&limit=50"

# Slowlog
curl "http://localhost:8000/monitoring/redis/slowlog?limit=20"

# Память
curl "http://localhost:8000/monitoring/redis/memory"

# Статистика
curl "http://localhost:8000/monitoring/redis/stats"
```

## Ключевые метрики

### Таблица метрик

| Метрика | Норма | Критично | Описание |
|---------|-------|----------|----------|
| **Cache Hit Rate** | >90% | <50% | Процент попаданий в кэш |
| **Memory Usage** | <100MB | >500MB | Использование памяти |
| **Connected Clients** | <50 | >100 | Подключенные клиенты |
| **Keys Count** | <10000 | >50000 | Общее количество ключей |
| **Memory Fragmentation** | <1.5 | >2.0 | Фрагментация памяти |
| **Commands/sec** | <1000 | >5000 | Операций в секунду |
| **Uptime** | >1 day | <1 hour | Время без перезапуска |

### Интерпретация метрик

#### Cache Hit Rate

**Формула:**
```
hit_rate = keyspace_hits / (keyspace_hits + keyspace_misses) * 100
```

**Значения:**
- **>90%** — Отлично, кэш работает эффективно
- **70-90%** — Нормально, можно оптимизировать
- **50-70%** — Плохо, проверьте TTL и ключи
- **<50%** — Критично, кэш почти не работает

#### Memory Usage

**Нормальные значения:**
- Development: <50MB
- Production (small): <100MB
- Production (large): <500MB

**Если память растёт:**
1. Проверьте количество ключей
2. Проверьте TTL у ключей
3. Очистите старый кэш

#### Connected Clients

**Нормальные значения:**
- Development: 2-5
- Production: 10-50

**Если клиентов много:**
1. Проверьте утечки подключений
2. Проверьте WebSocket подключения
3. Проверьте connection pool

## Alerts

### 🚨 Cache Hit Rate < 50%

**Причина:** Мало кэшируется или частая инвалидация

**Диагностика:**
```bash
# Проверить статистику
curl http://localhost:8000/monitoring/redis/stats

# Проверить ключи
curl "http://localhost:8000/monitoring/redis/keys?pattern=cache:*"
```

**Решение:**
1. Проверить частоту инвалидации кэша
2. Увеличить TTL
3. Проверить корректность ключей
4. Добавить кэширование в missing endpoints

---

### 🚨 Memory Usage > 500MB

**Причина:** Накопление ключей, утечка памяти

**Диагностика:**
```bash
# Проверить использование памяти
curl http://localhost:8000/monitoring/redis/memory

# Проверить ключи
curl "http://localhost:8000/monitoring/redis/keys?pattern=*&limit=100"

# Проверить статистику
curl http://localhost:8000/monitoring/redis/stats
```

**Решение:**
```bash
# Очистить кэш
curl -X POST "http://localhost:8000/api/v1/cache/clear/all"

# Или по шаблону
curl -X DELETE "http://localhost:8000/api/v1/cache/invalidate?pattern=cache:stats:*"

# Проверить ключи после очистки
curl "http://localhost:8000/monitoring/redis/keys?pattern=cache:*"
```

---

### 🚨 Connected Clients > 100

**Причина:** Утечка подключений, много WebSocket клиентов

**Диагностика:**
```bash
# Проверить информацию о клиентах
docker-compose exec redis redis-cli CLIENT LIST
```

**Решение:**
1. Проверить WebSocket подключения
2. Проверить закрытие connections в коде
3. Проверить connection pool настройки
4. Перезапустить backend при необходимости

---

### 🚨 Keys Count > 50000

**Причина:** Накопление ключей кэша

**Диагностика:**
```bash
# Посчитать ключи по префиксам
docker-compose exec redis redis-cli KEYS "cache:*" | wc -l
docker-compose exec redis redis-cli KEYS "lock:*" | wc -l
docker-compose exec redis redis-cli KEYS "scan:progress:*" | wc -l
```

**Решение:**
```bash
# Очистить кэш
curl -X POST "http://localhost:8000/api/v1/cache/clear/all"

# Проверить TTL у ключей
curl "http://localhost:8000/monitoring/redis/keys?pattern=cache:*&limit=100"
```

---

### 🚨 Lock не сбрасывается

**Причина:** Сканирование зависло, lock не освобождён

**Диагностика:**
```bash
# Проверить lock ключи
curl "http://localhost:8000/monitoring/redis/keys?pattern=lock:*"

# Проверить через CLI
docker-compose exec redis redis-cli KEYS "lock:*"
```

**Решение:**
```bash
# Принудительно удалить lock
docker-compose exec redis redis-cli DEL lock:scan:minsk

# Или через API (если есть)
curl -X DELETE "http://localhost:8000/api/v1/scan/lock?city=minsk"
```

---

### 🚨 Slowlog показывает медленные запросы

**Причина:** Медленные команды Redis (KEYS, SMEMBERS на больших sets)

**Диагностика:**
```bash
# Проверить slowlog
curl "http://localhost:8000/monitoring/redis/slowlog?limit=20"

# Проверить через CLI
docker-compose exec redis redis-cli SLOWLOG GET 20
```

**Решение:**
1. Избегать команды KEYS в production (использовать SCAN)
2. Оптимизировать запросы к большим sets/hashes
3. Увеличить slowlog-log-slower-than порог

## Grafana Dashboard (опционально)

### Настройка Prometheus + Grafana

Для продакшена рекомендуется настроить мониторинг с Grafana.

#### 1. Redis Exporter

```yaml
# docker-compose.yml
services:
  redis-exporter:
    image: oliver006/redis_exporter:latest
    ports:
      - "9121:9121"
    command:
      - --redis.addr=redis://redis:6379
    restart: unless-stopped
```

#### 2. Prometheus Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### 3. Grafana Dashboard

Импортируйте dashboard [Redis Dashboard for Prometheus](https://grafana.com/grafana/dashboards/11835-redis-dashboard-for-prometheus/)

### Ключевые метрики для Grafana

```promql
# Cache Hit Rate
redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total) * 100

# Memory Usage
redis_memory_used_bytes

# Connected Clients
redis_connected_clients

# Commands per second
rate(redis_commands_processed_total[1m])

# Keys Count
redis_db0_keys
```

## Monitoring Scripts

### Bash Script для проверки

```bash
#!/bin/bash
# redis_health_check.sh

REDIS_HOST="localhost"
REDIS_PORT="6379"
API_URL="http://localhost:8000"

echo "=== Redis Health Check ==="

# Health check
echo -e "\n📊 Health Status:"
curl -s "$API_URL/monitoring/redis" | jq '.status, .connected, .dbsize'

# Cache hit rate
echo -e "\n💾 Cache Hit Rate:"
curl -s "$API_URL/monitoring/redis" | jq '.cache.hit_rate_percent'

# Memory usage
echo -e "\n🧠 Memory Usage:"
curl -s "$API_URL/monitoring/redis" | jq '.memory.used_mb'

# Connected clients
echo -e "\n👥 Connected Clients:"
curl -s "$API_URL/monitoring/redis" | jq '.clients.connected'

# Keys count
echo -e "\n🔑 Keys Count:"
curl -s "$API_URL/monitoring/redis/keys?pattern=cache:*" | jq '.count'

echo -e "\n=== Health Check Complete ==="
```

### Python Script для мониторинга

```python
#!/usr/bin/env python3
# redis_monitor.py

import requests
import sys
from datetime import datetime

API_URL = "http://localhost:8000"

def check_redis_health():
    """Проверка здоровья Redis."""
    try:
        response = requests.get(f"{API_URL}/monitoring/redis", timeout=5)
        data = response.json()
        
        print(f"[{datetime.now()}] Redis Health Check")
        print(f"  Status: {data['status']}")
        print(f"  Connected: {data['connected']}")
        print(f"  Keys: {data['dbsize']}")
        print(f"  Cache Hit Rate: {data['cache']['hit_rate_percent']}%")
        print(f"  Memory: {data['memory']['used_mb']}")
        print(f"  Clients: {data['clients']['connected']}")
        
        # Alerts
        if data['cache']['hit_rate_percent'] < 50:
            print("  ⚠️ ALERT: Low cache hit rate!")
        
        if 'M' in data['memory']['used_mb'] and int(data['memory']['used_mb'].replace('M', '')) > 500:
            print("  ⚠️ ALERT: High memory usage!")
        
        if data['clients']['connected'] > 100:
            print("  ⚠️ ALERT: Too many connected clients!")
        
        return data['status'] == 'healthy'
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    healthy = check_redis_health()
    sys.exit(0 if healthy else 1)
```

## Troubleshooting

### Redis не отвечает

```bash
# Перезапустить Redis
docker-compose restart redis

# Проверить логи
docker-compose logs redis

# Проверить подключение
docker-compose exec redis redis-cli ping
```

### Кэш не инвалидируется

```bash
# Проверить ключи
docker-compose exec redis redis-cli KEYS "cache:*"

# Удалить вручную
docker-compose exec redis redis-cli KEYS "cache:stats:*" | xargs -I {} docker-compose exec redis redis-cli DEL {}

# Проверить через API
curl "http://localhost:8000/monitoring/redis/keys?pattern=cache:*"
```

### WebSocket не получает обновления

```bash
# Проверить Pub/Sub подписку
docker-compose exec redis redis-cli SUBSCRIBE scan:progress

# В другом терминале опубликовать сообщение
docker-compose exec redis redis-cli PUBLISH scan:progress "test"

# Проверить ключи прогресса
curl "http://localhost:8000/monitoring/redis/keys?pattern=scan:progress:*"
```

### Rate Limiting не работает

```bash
# Проверить ключи rate limiting
curl "http://localhost:8000/monitoring/redis/keys?pattern=ratelimit:*"

# Проверить значения
docker-compose exec redis redis-cli GET ratelimit:kufar:city:minsk:tokens
```

## Best Practices

### 1. Регулярный мониторинг

Настройте cron job для регулярной проверки:

```bash
# /etc/cron.d/redis-monitor
*/5 * * * * root /path/to/redis_health_check.sh >> /var/log/redis_health.log 2>&1
```

### 2. Логирование алертов

Настройте логирование критических событий:

```python
# monitoring/alerts.py
if hit_rate < 50:
    logger.warning(f"Low cache hit rate: {hit_rate}%")
    send_alert("Low cache hit rate", hit_rate)
```

### 3. Автоматическая очистка

Настройте автоматическую очистку при превышении памяти:

```python
# monitoring/auto_clean.py
if memory_used > 400 * 1024 * 1024:  # 400MB
    await redis_client.keys("cache:*")
    # Очистить старый кэш
```

### 4. Dashboard обновления

Обновляйте dashboard каждые 30 секунд:

```javascript
// frontend/src/components/RedisDashboard.tsx
useEffect(() => {
  const interval = setInterval(fetchRedisMetrics, 30000);
  return () => clearInterval(interval);
}, []);
```

## Ссылки

- [Redis Monitoring Documentation](https://redis.io/docs/manual/optimization/)
- [Redis Slowlog](https://redis.io/commands/slowlog/)
- [Redis Memory Optimization](https://redis.io/docs/manual/memory-optimization/)
- [Grafana Redis Dashboard](https://grafana.com/grafana/dashboards/11835-redis-dashboard-for-prometheus/)
