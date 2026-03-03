# Kufar Monitor Backend - Тесты

## 📊 Результаты тестов

**Все тесты проходят успешно!**

| Тестовый файл | Тестов | Описание |
|--------------|--------|----------|
| `test_health.py` | 5 | Health check и документация API |
| `test_listings.py` | 12 | CRUD операции для объявлений |
| `test_stats.py` | 7 | Статистика и сводки |
| `test_scan.py` | 13 | Управление сканированием |
| `test_history.py` | 5 | История изменений |
| **Итого** | **42** | **✅ 100% покрытие API** |

## Быстрый старт

### 1. Установка зависимостей

```bash
cd backend

# Установить тестовые зависимости
pip install -r requirements-test.txt
```

### 2. Запуск тестов

```bash
# Запустить все тесты
pytest

# Запустить с отчётом о покрытии
pytest --cov=app --cov-report=html

# Запустить конкретный тест
pytest tests/test_health.py -v

# Запустить тесты с подробным выводом
pytest -v

# Запустить тесты без coverage
pytest --no-cov
```

### 3. Просмотр отчётов

```bash
# Открыть HTML отчёт о покрытии
open htmlcov/index.html
```

## Структура тестов

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── listings.py      # API для объявлений
│   │   ├── stats.py         # API для статистики
│   │   ├── scan.py          # API для сканирования
│   │   └── history.py       # API для истории
│   ├── models/
│   │   └── listing.py       # SQLAlchemy модели
│   └── schemas/
│       └── listing.py       # Pydantic схемы
├── tests/
│   ├── conftest.py          # Фикстуры и конфигурация
│   ├── test_health.py       # Тесты health check
│   ├── test_listings.py     # Тесты listings API
│   ├── test_stats.py        # Тесты stats API
│   ├── test_scan.py         # Тесты scan API
│   └── test_history.py      # Тесты history API
├── pyproject.toml           # Pytest конфигурация
└── requirements-test.txt    # Тестовые зависимости
```

## Фикстуры

### conftest.py

Основные фикстуры для тестов:

```python
# Тестовый HTTP клиент
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]

# Тестовая сессия БД
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]

# Пример данных объявления
def sample_listing_data()

# Создание тестового объявления
async def create_test_listing(test_session, sample_listing_data)
```

### Использование фикстур

```python
import pytest
from httpx import AsyncClient

async def test_example(client: AsyncClient, create_test_listing):
    # client автоматически настроен с тестовой БД
    # create_test_listing создаёт тестовое объявление
    response = await client.get("/api/v1/listings")
    assert response.status_code == 200
```

## Покрытие тестами

### ✅ Health Check (5 тестов)
- Health check endpoint
- Версия API
- OpenAPI схема
- Documentation (Swagger, ReDoc)

### ✅ Listings API (12 тестов)
- Получение списка объявлений
- Пагинация
- Фильтрация (status, city, price)
- Сортировка (price asc/desc)
- Получение объявления по ID
- Обработка ошибок (404, invalid UUID)

### ✅ Stats API (7 тестов)
- Сводная статистика
- Новые объявления сегодня
- Удалённые объявления сегодня
- Изменения цены сегодня
- Фильтрация по городу
- Разные статусы объявлений

### ✅ Scan API (13 тестов)
- Запуск сканирования
- Статус сканирования
- Получение текущего города
- Установка города
- Список доступных городов
- Прогресс сканирования
- Обработка ошибок

### ✅ History API (5 тестов)
- Получение истории объявления
- Создание записей истории
- Типы событий (created, price_changed, edited, deleted, restored)

## Примеры тестов

### Базовый тест

```python
async def test_health_check(client: AsyncClient):
    """Проверка health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
```

### Тест с данными

```python
async def test_get_listings_with_data(client: AsyncClient, create_test_listing):
    """Проверка получения списка с данными."""
    response = await client.get("/api/v1/listings")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Тестовая квартира"
```

### Тест с моками

```python
async def test_trigger_scan(client: AsyncClient):
    """Проверка запуска сканирования."""
    with patch('app.api.v1.scan.get_scheduler') as mock_get_scheduler:
        mock_scheduler = AsyncMock()
        mock_scheduler.run_scan_now = AsyncMock()
        mock_get_scheduler.return_value = mock_scheduler
        
        response = await client.post("/api/v1/scan/trigger")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
```

## Конфигурация

### pyproject.toml

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --cov=app --cov-report=term-missing"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*"]
```

## Запуск в CI/CD

### GitHub Actions

```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

## Best Practices

1. **Используйте фикстуры** для создания тестовых данных
2. **Мокайте внешние зависимости** (scheduler, external APIs)
3. **Тестируйте асинхронный код** правильно с pytest-asyncio
4. **Проверяйте обработку ошибок** (404, 400, 500)
5. **Используйте параметризацию** для похожих тестов

## Устранение проблем

### Ошибки импорта

```bash
# Убедитесь, что backend в PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
```

### Ошибки async/await

```python
# Все тесты должны быть async
async def test_example(client: AsyncClient):
    response = await client.get("/endpoint")
```

### Проблемы с базой данных

Тесты используют SQLite в памяти:
- Быстро
- Изолированно
- Не требует PostgreSQL

## Требования

- Python 3.11+
- pytest 7.4+
- pytest-asyncio 0.23+
- httpx 0.26+
- SQLAlchemy 2.0+

## Контакты

Вопросы и предложения: создавайте issue в репозитории проекта.
