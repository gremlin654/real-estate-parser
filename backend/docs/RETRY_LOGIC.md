# Retry Logic Documentation

## Обзор

Реализована **Retry логика с exponential backoff** для HTTP запросов в скрапере Kufar.by. Это повышает надёжность сканирования при временных проблемах с сетью или сервером Kufar.

---

## Реализованные компоненты

### 1. KufarJSONScraper с retry логикой

**Файл:** `backend/app/scraper/kufar_json_scraper.py`

#### Конфигурация

```python
scraper = KufarJSONScraper(
    timeout=30.0,           # Timeout запроса в секундах
    max_retries=3,          # Максимальное количество попыток
    base_delay=1.0,         # Базовая задержка в секундах
    max_delay=60.0,         # Максимальная задержка в секундах
    exponential_base=2.0,   # База экспоненты для backoff
)
```

#### Retryable исключения

Автоматически повторяются при следующих ошибках:

```python
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,      # Превышение времени ожидания
    httpx.ConnectError,          # Ошибка подключения
    httpx.ReadTimeout,           # Timeout чтения
    httpx.WriteTimeout,          # Timeout записи
    httpx.RemoteProtocolError,   # Ошибка протокола
)
```

#### Retryable HTTP статусы

Повторяются при получении следующих статусов:

```python
RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
```

| Код | Описание |
|-----|----------|
| 408 | Request Timeout |
| 425 | Too Early |
| 429 | Too Many Requests (Rate Limit) |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
| 504 | Gateway Timeout |

---

### 2. Exponential Backoff с Jitter

#### Формула расчёта задержки

```python
delay = min(
    base_delay * (exponential_base ** attempt) + jitter,
    max_delay
)
```

где:
- `attempt` — номер попытки (0-based)
- `jitter` — случайная вариация ±10% для предотвращения "thundering herd"

#### Примеры задержек (по умолчанию)

| Попытка | Задержка (сек) |
|---------|----------------|
| 1 → 2   | ~1.0           |
| 2 → 3   | ~2.0           |
| 3 → 4   | ~4.0           |
| 4 → 5   | ~8.0           |
| ...     | ...            |
| N       | ≤60.0 (max)    |

---

### 3. Методы

#### `_fetch_with_retry(url, client)`

Внутренний метод для HTTP запросов с retry логикой.

**Возвращает:**
```python
Tuple[bool, Optional[str], int]  # (success, content, status_code)
```

**Пример использования:**
```python
async with httpx.AsyncClient() as client:
    success, content, status = await scraper._fetch_with_retry(url, client)
    
    if success:
        # Обработать контент
    else:
        # Обработать ошибку
```

#### `scrape_page(url, max_listings)`

Публичный метод для сканирования страницы с retry.

**Возвращает:**
```python
List[dict]  # Список объявлений (пустой если все попытки провалились)
```

---

## Логирование

### Успешный запрос
```
INFO - Fetching https://re.kufar.by/l/minsk... (attempt 1/3)
INFO - Page fetched, size: 245678 bytes
```

### Retry при ошибке
```
WARNING - Network error (attempt 1): TimeoutException: Timeout. Retrying in 1.0s...
WARNING - Network error (attempt 2): TimeoutException: Timeout. Retrying in 2.1s...
INFO - Fetching https://re.kufar.by/l/minsk... (attempt 3/3)
```

### Все попытки исчерпаны
```
ERROR - All 3 attempts failed for https://re.kufar.by/l/minsk. Last error: TimeoutException: Timeout
WARNING - Failed to fetch https://re.kufar.by/l/minsk after 3 attempts. Status: 0
```

### HTTP 503 ошибка
```
WARNING - HTTP 503 for https://re.kufar.by/l/minsk. Retrying in 1.0s...
```

### Non-retryable ошибка (404)
```
ERROR - HTTP error for https://re.kufar.by/l/invalid: 404 - Not Found
```

---

## Тесты

**Файл:** `backend/tests/test_retry_logic.py`

### Запуск тестов

```bash
# В контейнере
docker-compose exec backend python -m pytest tests/test_retry_logic.py -v

# С coverage
docker-compose exec backend python -m pytest tests/test_retry_logic.py --cov=app/scraper/kufar_json_scraper
```

### Покрытие тестами (16 тестов)

| Группа тестов | Количество | Описание |
|---------------|------------|----------|
| `TestRetryConfiguration` | 2 | Конфигурация retry параметров |
| `TestCalculateDelay` | 3 | Расчёт exponential backoff delay |
| `TestRetryableStatus` | 2 | Определение retryable статусов |
| `TestFetchWithRetry` | 5 | Тесты `_fetch_with_retry` метода |
| `TestScrapePageWithRetry` | 2 | Тесты `scrape_page` метода |
| `TestRetryableExceptions` | 2 | Тесты retryable исключений |

---

## Настройка

### Через код

```python
# backend/app/scraper/scheduler.py
from app.scraper.kufar_json_scraper import KufarJSONScraper

scraper = KufarJSONScraper(
    max_retries=5,        # Увеличить количество попыток
    base_delay=2.0,       # Увеличить базовую задержку
    max_delay=120.0,      # Увеличить максимальную задержку
)
```

### Через переменные окружения (рекомендуется)

Добавьте в `.env`:

```env
# Retry configuration
SCRAPER_MAX_RETRIES=5
SCRAPER_BASE_DELAY=2.0
SCRAPER_MAX_DELAY=120.0
SCRAPER_TIMEOUT=60.0
```

Обновите `config.py`:

```python
# backend/app/config.py
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Retry configuration
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_BASE_DELAY: float = 1.0
    SCRAPER_MAX_DELAY: float = 60.0
    SCRAPER_TIMEOUT: float = 30.0
```

Используйте в скрапере:

```python
scraper = KufarJSONScraper(
    max_retries=settings.SCRAPER_MAX_RETRIES,
    base_delay=settings.SCRAPER_BASE_DELAY,
    max_delay=settings.SCRAPER_MAX_DELAY,
    timeout=settings.SCRAPER_TIMEOUT,
)
```

---

## Сценарии использования

### 1. Временная недоступность Kufar

**Проблема:** Kufar возвращает 503 ошибку во время технических работ.

**Решение:** Retry логика автоматически повторит запрос до 3 раз с увеличивающимися задержками.

### 2. Rate Limiting (429)

**Проблема:** Kufar ограничивает количество запросов.

**Решение:** При получении 429 статуса запрос будет повторён с задержкой.

### 3. Проблемы с сетью

**Проблема:** Временные проблемы с подключением к интернету.

**Решение:** `ConnectError` и `TimeoutException` автоматически повторяются.

### 4. Thundering Herd

**Проблема:** Множество одновременных запросов после восстановления сервиса.

**Решение:** Jitter (±10% вариация) предотвращает синхронизацию запросов.

---

## Рекомендации

### ✅ Хорошо

- **3-5 попыток** — оптимально для большинства сценариев
- **Exponential backoff** — снижает нагрузку на сервер
- **Jitter** — предотвращает синхронизацию запросов
- **Логирование** — помогает диагностировать проблемы

### ❌ Избегайте

- **Слишком много попыток** (>10) — сканирование займёт слишком много времени
- **Слишком большая задержка** (>300s) — может вызвать таймаут всего сканирования
- **Retry для 4xx ошибок** (кроме 408, 429) — обычно это клиентские ошибки

---

## Метрики и мониторинг

### Логи для анализа

```bash
# Посчитать количество retry
docker-compose logs backend | grep "Retrying in" | wc -l

# Посчитать неудачные сканирования
docker-compose logs backend | grep "All.*attempts failed" | wc -l

# Посмотреть последние ошибки
docker-compose logs backend | grep "ERROR" | tail -50
```

### Alerting

Настройте уведомления при:
- >10 retry за последние 5 минут
- >3 полных неудач сканирования подряд

---

## Будущие улучшения

- [ ] **Динамическая настройка retry** — адаптация на основе истории успехов/неудач
- [ ] **Circuit Breaker** — временная остановка запросов при множественных ошибках
- [ ] **Retry после 404** — для случаев когда страница временно недоступна
- [ ] **Метрики Prometheus** — экспорт статистики retry для мониторинга

---

## Ссылки

- [HTTP Retry Standards](https://tools.ietf.org/html/rfc7231)
- [Exponential Backoff Best Practices](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [httpx Documentation](https://www.python-httpx.org/)
