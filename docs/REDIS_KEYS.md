# Redis Keys Reference

## Формат ключей

```
{namespace}:{subnamespace}:{identifier}:{field}
```

## Namespaces

### `cache:*` — Кэширование API

| Ключ | Тип | TTL | Описание |
|------|-----|-----|----------|
| `cache:stats:summary:get_summary:city={city}` | String (JSON) | 60 сек | Сводная статистика |
| `cache:stats:price-trends:get_price_trends:city={city}:rooms={rooms}` | String (JSON) | 300 сек | Тренды цен |
| `cache:stats:room-distribution:get_room_distribution:city={city}` | String (JSON) | 300 сек | Распределение по комнатам |
| `cache:stats:daily-activity:get_daily_activity:city={city}:period={period}` | String (JSON) | 300 сек | Дневная активность |
| `cache:listings:get_listings:page={page}:size={size}:...` | String (JSON) | 30 сек | Список объявлений |

**Пример ключа:**
```
cache:stats:summary:get_summary:city=minsk
```

**Значение (JSON):**
```json
{
  "total_listings": 546,
  "active_listings": 489,
  "avg_price": 125000,
  "avg_price_usd": 43500,
  ...
}
```

### `lock:*` — Distributed Locking

| Ключ | Тип | TTL | Описание |
|------|-----|-----|----------|
| `lock:scan:{city}` | String | 3600 сек | Блокировка сканирования города |

**Формат значения:**
```
lock:scan:{city}:{timestamp}:{uuid}
```

**Пример:**
```
lock:scan:minsk:1709923847:a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Использование:**
```python
from app.core.redis_client import get_redis
import redis.asyncio as redis

redis_client = await get_redis()
lock_key = f"lock:scan:{city}"
lock_value = f"lock:scan:{city}:{timestamp}:{uuid}"

# Попытка захватить lock
acquired = await redis_client.set(lock_key, lock_value, nx=True, ex=3600)
if acquired:
    # Сканирование выполняется
    ...
    # Освобождение lock
    await redis_client.delete(lock_key)
```

### `scan:progress:*` — WebSocket State

| Ключ | Тип | TTL | Описание |
|------|-----|-----|----------|
| `scan:progress:{city}` | Hash | 7200 сек | Прогресс сканирования |

**Поля Hash:**
```
city: string
stage: string (starting|fetching|parsing|upserting|done|error)
pages_scraped: int
listings_fetched: int
listings_processed: int
is_stable: bool
elapsed_seconds: float
updated_at: timestamp
error?: string
```

**Пример:**
```
HSET scan:progress:minsk city "minsk" stage "fetching" pages_scraped 5 listings_fetched 250 is_stable false elapsed_seconds 12.5 updated_at 1709923847
```

**Получение прогресса:**
```python
progress = await redis_client.hgetall(f"scan:progress:{city}")
```

### `ratelimit:*` — Rate Limiting

| Ключ | Тип | TTL | Описание |
|------|-----|-----|----------|
| `ratelimit:kufar:city:{city}:tokens` | String (float) | 3600 сек | Доступные токены |
| `ratelimit:kufar:city:{city}:last_update` | String (timestamp) | 3600 сек | Последнее обновление |

**Пример:**
```
ratelimit:kufar:city:minsk:tokens = 7.5
ratelimit:kufar:city:minsk:last_update = 1709923847.123
```

**Алгоритм Token Bucket:**
- Ёмкость: 10 токенов
- Скорость пополнения: 10 токенов/секунду
- При запросе: если токены есть → разрешить, иначе → ждать

## Pub/Sub каналы

| Канал | Описание | Формат сообщения |
|-------|----------|------------------|
| `scan:progress` | Обновления прогресса сканирования | `{"channel": "scan:progress", "city": "...", "stage": "...", ...}` |

**Публикация сообщения:**
```python
await redis_client.publish("scan:progress", json.dumps({
    "channel": "scan:progress",
    "city": "minsk",
    "stage": "fetching",
    "pages_scraped": 5,
    "listings_fetched": 250,
    "is_stable": False,
    "elapsed_seconds": 12.5
}))
```

**Подписка (WebSocket):**
```python
pubsub = redis_client.pubsub()
await pubsub.subscribe("scan:progress")
async for message in pubsub.listen():
    # Отправка клиентам через WebSocket
    ...
```

## Управление кэшем

### Инвалидация

```bash
# Удалить по шаблону
curl -X DELETE "http://localhost:8000/api/v1/cache/invalidate?pattern=cache:stats:*"

# Полная очистка
curl -X POST "http://localhost:8000/api/v1/cache/clear/all"
```

**Python API:**
```python
# По шаблону
keys = await redis_client.keys("cache:stats:*")
if keys:
    await redis_client.delete(*keys)

# Полная очистка
await redis_client.flushdb()
```

### Статистика

```bash
curl "http://localhost:8000/api/v1/cache/stats"
```

**Ответ:**
```json
{
  "total_keys": 42,
  "cache_keys": 35,
  "lock_keys": 2,
  "progress_keys": 3,
  "ratelimit_keys": 2,
  "memory_usage": "2.3M"
}
```

## Мониторинг

### Основные метрики

```bash
# Количество ключей
docker-compose exec redis redis-cli DBSIZE

# Использование памяти
docker-compose exec redis redis-cli INFO memory

# Hit rate кэша
docker-compose exec redis redis-cli INFO stats | grep keyspace_hits
```

### Команды Redis CLI

```bash
# Подключение
docker-compose exec redis redis-cli

# Проверка подключения
PING
# PONG

# Количество ключей
DBSIZE
# (integer) 42

# Все ключи
KEYS "*"
# 1) "cache:stats:summary:get_summary:city=minsk"
# 2) "lock:scan:minsk"
# 3) "scan:progress:minsk"

# Ключи по шаблону
KEYS "cache:stats:*"
# 1) "cache:stats:summary:get_summary:city=minsk"
# 2) "cache:stats:price-trends:get_price_trends:city=minsk:rooms=2"

# TTL ключа
TTL cache:stats:summary:get_summary:city=minsk
# (integer) 45

# Тип ключа
TYPE scan:progress:minsk
# hash

# Hash поля
HGETALL scan:progress:minsk
# 1) "city"
# 2) "minsk"
# 3) "stage"
# 4) "fetching"
# ...

# Удаление ключа
DEL lock:scan:minsk
# (integer) 1

# Статистика
INFO stats
# Keyspace hits: 15234
# Keyspace misses: 892

# Использование памяти
INFO memory
# used_memory_human: 2.3M
```

## Troubleshooting

### Проблема: Redis не отвечает

```bash
docker-compose restart redis
docker-compose logs redis
```

### Проблема: Закончилась память

```bash
# Очистить кэш
curl -X POST "http://localhost:8000/api/v1/cache/clear/all"

# Проверить использование памяти
docker-compose exec redis redis-cli INFO memory
```

### Проблема: Lock не сбрасывается

```bash
# Принудительно удалить lock
docker-compose exec redis redis-cli DEL lock:scan:minsk
```

### Проблема: Кэш не инвалидируется

```bash
# Проверить ключи
docker-compose exec redis redis-cli KEYS "cache:*"

# Удалить вручную
docker-compose exec redis redis-cli KEYS "cache:stats:*" | xargs docker-compose exec redis redis-cli DEL
```

### Проблема: WebSocket не получает обновления

```bash
# Проверить Pub/Sub
docker-compose exec redis redis-cli SUBSCRIBE scan:progress

# В другом терминале опубликовать сообщение
docker-compose exec redis redis-cli PUBLISH scan:progress "test"
```

## Best Practices

### 1. Именование ключей

✅ Правильно:
```
cache:stats:summary:get_summary:city=minsk
lock:scan:minsk
scan:progress:minsk
```

❌ Неправильно:
```
minsk_cache
lock_123
progress
```

### 2. TTL для всех ключей

Всегда устанавливайте TTL для ключей:
```python
await redis_client.setex("cache:stats:...", 300, json.dumps(data))
await redis_client.setex("lock:scan:...", 3600, lock_value)
```

### 3. Атомарные операции

Используйте атомарные операции для locks:
```python
# Правильно
acquired = await redis_client.set(lock_key, lock_value, nx=True, ex=3600)

# Неправильно (race condition)
exists = await redis_client.exists(lock_key)
if not exists:
    await redis_client.set(lock_key, lock_value, ex=3600)
```

### 4. Очистка ресурсов

Всегда освобождайте locks после использования:
```python
try:
    # Сканирование
    ...
finally:
    await redis_client.delete(lock_key)
```

### 5. Мониторинг памяти

Регулярно проверяйте использование памяти:
```bash
# Раз в день
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
```

## Ссылки

- [Redis Documentation](https://redis.io/documentation)
- [Redis Commands](https://redis.io/commands/)
- [Redis Best Practices](https://redis.io/docs/manual/best-practices/)
