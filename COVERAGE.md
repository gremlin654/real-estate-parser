# Kufar Monitor — Покрытие тестами

## 📊 Общая статистика

| Компонент | Тестов | Coverage | Статус |
|-----------|--------|----------|--------|
| **Backend** | 38 | 29% | ✅ |
| **Frontend E2E** | 19 | N/A | ✅ |
| **Frontend Unit** | 4 | ~1% | ⚠️ |

---

## Backend (Python/FastAPI)

### Запуск тестов

```bash
cd backend

# Все тесты
docker-compose exec backend python -m pytest tests/ -v

# С покрытием
docker-compose exec backend python -m pytest tests/ --cov=app --cov-report=html

# Открыть отчёт
open htmlcov/index.html
```

### Покрытие по модулям

| Модуль | Coverage | Статус |
|--------|----------|--------|
| `app/api/v1/scan.py` | 95% | ✅ |
| `app/schemas/listing.py` | 99% | ✅ |
| `app/models/listing.py` | 98% | ✅ |
| `app/config.py` | 100% | ✅ |
| `app/api/v1/history.py` | 76% | ✅ |
| `app/api/v1/listings.py` | 68% | ⚠️ |
| `app/main.py` | 73% | ⚠️ |
| `app/db/database.py` | 80% | ⚠️ |
| `app/api/v1/stats.py` | 50% | ⚠️ |
| `app/scraper/kufar_client.py` | 21% | ❌ |
| `app/scraper/scheduler.py` | 15% | ❌ |
| `app/services/listing_service.py` | 16% | ❌ |
| `app/scraper/parser.py` | 10% | ❌ |
| `app/scraper/kufar_json_scraper.py` | 6% | ❌ |
| `app/scraper/kufar_http_scraper.py` | 0% | ❌ |

**Среднее покрытие: 29%**

### План улучшения

1. Добавить тесты на scraper модули (интеграционные)
2. Протестировать бизнес-логику в `listing_service.py`
3. Покрыть `scheduler.py` моками

---

## Frontend (React/Playwright/Vitest)

### Запуск тестов

```bash
cd frontend

# E2E тесты (Playwright)
npm run test:e2e
npm run test:e2e:chromium           # Только Chromium
npm run test:e2e:ui                 # UI режим

# Unit тесты (Vitest)
npm run test:unit
npm run test:unit:watch             # Режим наблюдения
npm run test:unit:coverage          # С покрытием

# Все тесты с покрытием
npm run coverage
```

### Отчёты

- **Unit Coverage**: `coverage/vitest/index.html`
- **E2E Report**: `playwright-report/index.html`

### Покрытие по модулям (Unit)

| Модуль | Coverage | Статус |
|--------|----------|--------|
| `src/lib/utils.ts` | 100% | ✅ |
| `src/components/**` | 0% | ❌ |
| `src/pages/**` | 0% | ❌ |
| `src/store/**` | 0% | ❌ |
| `src/hooks/**` | 0% | ❌ |

**Среднее покрытие: ~1%**

### План улучшения

1. Добавить Unit тесты на компоненты:
   - `ListingInfoCard`
   - `HistoryTimeline`
   - `AppSidebar`
2. Протестировать store (`filterStore`)
3. Покрыть хуки (`use-mobile`)

---

## CI/CD Integration

### GitHub Actions пример

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          docker-compose up -d db_test
          docker-compose exec backend python -m pytest tests/ --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run unit tests
        run: cd frontend && npm run test:unit:coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/vitest/lcov.info
          flags: frontend
```

---

## Рекомендации

### Backend

- ✅ Отличное покрытие API endpoints (50-95%)
- ⚠️ Нужно покрыть scraper модули
- ⚠️ Добавить тесты на бизнес-логику

### Frontend

- ✅ E2E тесты покрывают основные сценарии
- ⚠️ Нужно добавить Unit тесты на компоненты
- ⚠️ Покрыть тестами store и хуки

### Цели

| Компонент | Текущее | Цель |
|-----------|---------|------|
| Backend | 29% | 60% |
| Frontend Unit | 1% | 40% |
| Frontend E2E | 19 тестов | 30 тестов |
