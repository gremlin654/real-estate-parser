# Kufar Monitor — Контекст для AI-ассистента

## Языковые предпочтения

**Всегда отвечайте на русском языке** при взаимодействии с пользователями по этому проекту.

## Политика изменений в базе данных

### ⚠️ Production БД — ЗАПРЕЩЕНО изменять без backup

**Production база данных `kufar_monitor` (порт 5432) не должна изменяться напрямую.**

**Правила работы с production БД:**

1. **⛔ Запрещено выполнять изменения без подтверждения:**
   - Запуск миграций (`alembic upgrade/downgrade`)
   - SQL-команды (INSERT, UPDATE, DELETE, TRUNCATE)
   - Очистку таблиц или данных
   - Изменение схемы
   - Любые деструктивные операции

2. **✅ Обязательно создавать backup перед изменениями:**
   ```bash
   # Создать дамп production БД
   docker-compose exec db pg_dump -U postgres kufar_monitor > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # Или создать snapshot через pg_dumpall
   docker-compose exec db pg_dumpall -U postgres > full_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **✅ Использовать тестовую БД для экспериментов:**
   ```bash
   # Тестовая БД (порт 5433) — безопасна для изменений
   docker-compose exec db_test psql -U postgres -d kufar_monitor_test
   ```

4. **✅ Восстановление из backup:**
   ```bash
   # Восстановить из дампа
   cat backup_20250101_120000.sql | docker-compose exec -T db psql -U postgres -d kufar_monitor
   ```

**Всегда уточняйте у пользователя перед выполнением команд, изменяющих production БД.**

## Обзор проекта

**Kufar Monitor** — автоматизированная система мониторинга недвижимости для портала [Kufar.by](https://re.kufar.by) (белорусский портал недвижимости). Система сканирует выбранные города, сохраняет объявления в базу данных и отслеживает изменения цен и статусов.

### Ключевые возможности

- **Автоматическое сканирование** — плановый парсинг каждые 30 минут
- **Ручное сканирование** — сканирование по требованию через веб-интерфейс
- **Две валюты** — цены в BYN и USD с переключателем
- **Отслеживание изменений** — фиксация изменений цены, статуса, удаления объявлений
- **Фильтрация** — по городу, статусу, цене, валюте, сортировке
- **История изменений** — полная история всех событий по каждому объявлению
- **История сканирований** — отслеживание запусков сканера, статистика, ошибки
- **Мультигород** — поддержка 6 городов (Минск, Могилёв, Гродно, Брест, Гомель, Витебск)
- **Real-time прогресс** — отображение прогресса сканирования в реальном времени с прогресс-баром
- **Галерея изображений** — полноразмерные изображения с CDN Kufar
- **Тёмная тема** — современный дизайн в тёмных тонах
- **Admin-панель** — боковая навигация
- **📊 Графики и аналитика** — динамика цен, распределение по комнатам, активность по дням (v2.0)
- **📤 Экспорт данных** — выгрузка в CSV, XLSX, JSON (v2.0)
- **🔄 CI/CD** — автоматические тесты и deployment (v2.0)

## Архитектура

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Frontend   │─────▶│   Backend    │─────▶│  PostgreSQL │
│ React + TS  │      │  FastAPI     │      │  Database   │
│ TailwindCSS │◀─────│  SQLAlchemy  │◀─────│             │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Kufar.by    │
                     │  Scraper     │
                     └──────────────┘
```

## Технологический стек

| Компонент | Технологии |
|-----------|------------|
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS 4, React Router, Zustand, TanStack Query, shadcn/ui, lucide-react, recharts, **Playwright (E2E - 118 тестов)**, **Vitest (Unit - 326 тестов)**, **monocart-coverage-reports (66.12% coverage)** |
| **Backend** | FastAPI, SQLAlchemy (async), Pydantic, APScheduler, **pytest (API тесты - 201 тест)**, pandas, openpyxl |
| **Database** | PostgreSQL 16, Alembic (миграции) |
| **Scraper** | Playwright (Chromium), BeautifulSoup4, aiohttp |
| **Infrastructure** | Docker, Docker Compose, **GitHub Actions (CI/CD)** |
| **Testing** | Playwright (E2E - 118 тестов), Vitest (Unit - 326 тестов, 66.12% coverage), pytest (API - 201 тест, 55% coverage), monocart-coverage-reports, istanbul/v8, @testing-library/react |
| **Analytics** | Recharts (графики и диаграммы) |

## Структура проекта

```
web/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # API маршруты (listings, history, stats, scan, export)
│   │   ├── core/             # Ядро приложения (logging_config.py)
│   │   ├── db/               # Подключение к БД и миграции
│   │   ├── models/           # SQLAlchemy модели (Listing, ListingHistory, ScanHistory)
│   │   ├── schemas/          # Pydantic схемы
│   │   ├── scraper/          # Логика скрапера (scheduler, parser, kufar_*.py)
│   │   ├── services/         # Бизнес-логика (listing_service.py, scan_history_service.py)
│   │   ├── config.py         # Конфигурация
│   │   └── main.py           # FastAPI приложение
│   ├── tests/                # Pytest тесты (201 тест)
│   │   ├── conftest.py       # Фикстуры
│   │   ├── test_health.py
│   │   ├── test_listings.py
│   │   ├── test_stats.py     # Тесты статистики (обновлено v2.0)
│   │   ├── test_scan.py
│   │   ├── test_scan_history.py
│   │   ├── test_history.py
│   │   ├── test_logging.py
│   │   ├── test_retry_logic.py
│   │   ├── test_listing_service.py
│   │   ├── test_kufar_client.py
│   │   ├── test_scheduler.py
│   │   └── test_export.py    # Тесты экспорта (11 тестов, v2.0)
│   ├── docs/
│   │   ├── LOGGING.md
│   │   ├── SCAN_HISTORY.md
│   │   └── TESTS.md
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-test.txt
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── api/              # API хуки (TanStack Query)
│   │   ├── api/listings.test.tsx
│   │   ├── components/
│   │   │   ├── ui/           # shadcn/ui компоненты
│   │   │   ├── charts/       # Компоненты графиков (v2.0)
│   │   │   │   ├── PriceTrendChart.tsx
│   │   │   │   └── PriceTrendChart.test.tsx
│   │   │   ├── listing/
│   │   │   │   ├── ListingInfoCard.test.tsx
│   │   │   │   └── HistoryTimeline.test.tsx
│   │   │   ├── Layout.test.tsx
│   │   │   └── AppLayout.test.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx # Обновлён: графики (v2.0)
│   │   │   ├── Listings.tsx  # Обновлён: экспорт (v2.0)
│   │   │   ├── ListingDetail.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── Statistics.tsx
│   │   ├── store/
│   │   │   └── filterStore.test.ts
│   │   ├── hooks/
│   │   │   └── use-mobile.test.ts
│   │   ├── lib/
│   │   │   └── utils.test.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── tests/                # Playwright E2E тесты (118 тестов)
│   │   ├── fixtures.ts
│   │   ├── dashboard.spec.ts
│   │   ├── listings.spec.ts
│   │   ├── listing-detail.spec.ts
│   │   ├── mobile.spec.ts
│   │   ├── api-integration.spec.ts
│   │   ├── scanning.spec.ts
│   │   ├── pages/
│   │   └── TESTS.md
│   ├── Dockerfile
│   ├── package.json
│   ├── playwright.config.ts
│   ├── vite.config.ts
│   ├── generate-coverage.js
│   └── tsconfig.json
│
├── .github/
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline (v2.0)
│
├── codecov.yml               # Codecov конфигурация (v2.0)
├── docker-compose.yml
├── README.md
└── QWEN.md
```

## Сборка и запуск

### Требования

- Docker и Docker Compose
- 2 GB свободной памяти
- Порты 3000, 8000, 5432 свободны (или измените docker-compose.yml)

### Быстрый старт

```bash
# Перейти в проект
cd /path/to/web

# Запустить все сервисы
docker-compose up --build

# Остановить сервисы
docker-compose down

# Перезапустить с пересборкой
docker-compose up --build --force-recreate
```

### Точки доступа

| Сервис | URL | Описание |
|--------|-----|----------|
| **Frontend** | http://localhost:3000 | Веб-интерфейс |
| **Backend API** | http://localhost:8000 | API сервер |
| **API Docs** | http://localhost:8000/docs | Swagger документация |
| **PostgreSQL** | localhost:5432 | База данных |

### Команды разработки

#### Backend

```bash
cd backend

# Установить зависимости
pip install -r requirements.txt

# Установить тестовые зависимости
pip install -r requirements-test.txt

# Запустить dev-сервер (требуется PostgreSQL)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запустить миграции
alembic upgrade head

# Создать новую миграцию
alembic revision --autogenerate -m "Description"

# Тестировать API
curl http://localhost:8000/health

# Запустить тесты
docker-compose exec backend python -m pytest tests/ -v

# Запустить тесты с coverage
docker-compose exec backend python -m pytest tests/ --cov=app
```

#### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev-сервер
npm run dev

# Запустить тесты
npm run test:e2e                    # E2E тесты (Playwright)
npm run test:unit                   # Unit тесты (Vitest) - 96 тестов

# Запустить тесты с покрытием
npm run coverage                    # Все тесты (Unit + E2E)
npm run test:unit:coverage          # Только Unit тесты с coverage
npm run test:e2e:coverage           # E2E тесты с coverage + генерация отчёта

# Просмотреть отчёт о покрытии
npm run coverage:show               # Открыть HTML отчёт coverage
open coverage/vitest/index.html     # HTML отчёт (Unit)
npx playwright show-report          # HTML отчёт (E2E)
```

# Собрать продакшн
npm run build

# Линтинг
npm run lint

# Тесты
npm run test:e2e           # Запустить все E2E тесты
npm run test:e2e:headed    # Запустить в режиме браузера
npm run test:e2e:ui        # Запустить UI режим
npm run test:e2e:report    # Показать HTML отчёт
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Listings
```bash
GET /api/v1/listings?page=1&size=20&status=active&city=minsk
GET /api/v1/listings/{id}
GET /api/v1/history/{id}  # История изменений объявления
```

### Stats
```bash
# Получить сводную статистику (можно фильтровать по городу)
GET /api/v1/stats/summary?city=minsk

# Динамика цен по месяцам (для конкретной комнаты)
GET /api/v1/stats/price-trends?city=minsk&rooms=1&period_months=12

# Распределение по комнатам
GET /api/v1/stats/room-distribution?city=minsk

# Ежедневная активность (новые, удалённые, изменения цены)
GET /api/v1/stats/daily-activity?city=minsk&period_days=30

# Сравнение городов
GET /api/v1/stats/city-comparison
```

**Пример ответа `/api/v1/stats/price-trends`:**
```json
{
  "city": "minsk",
  "rooms": 1,
  "period_months": 12,
  "data": [
    { "year": 2024, "month": 1, "avg_price_usd": 85000, "listings_count": 150 },
    { "year": 2024, "month": 2, "avg_price_usd": 87500, "listings_count": 165 }
  ]
}
```

**Логика подсчета средней цены:**
- Используется цена из `snapshot` события `created` в таблице `listing_history`
- Это гарантирует, что берется цена на момент первого появления объявления
- Если цена объявления изменилась, в статистике за прошлые месяцы остается оригинальная цена
- Группировка по месяцам производится по `first_seen_at` (дата первого обнаружения)
- Фильтр: `price_usd > 0` в snapshot, статусы `active`, `new`, `updated`
- В ответе: средняя цена (округленная до 2 знаков) и количество объявлений за месяц

### Scan Management
```bash
POST /api/v1/scan/trigger      # Ручное сканирование
GET /api/v1/scan/status        # Статус сканирования
GET /api/v1/scan/progress      # Real-time прогресс
GET /api/v1/scan/city          # Текущий город
POST /api/v1/scan/city         # Изменить город
GET /api/v1/scan/cities        # Доступные города
GET /api/v1/scan/schedule      # Настройки расписания
PUT /api/v1/scan/schedule      # Обновить настройки расписания
```

**Пример ответа `/api/v1/scan/schedule`:**
```json
{
  "scan_interval_minutes": 30,
  "enabled": true,
  "updated_at": "2026-03-01T20:00:00"
}
```

**Пример запроса `PUT /api/v1/scan/schedule`:**
```json
{
  "scan_interval_minutes": 60,
  "enabled": true
}
```

**Валидация:**
- `scan_interval_minutes`: 5-1440 минут (от 5 мин до 24 часов)
- `enabled`: boolean (включить/выключить автоматическое сканирование)

### Scan History
```bash
GET /api/v1/scan/history              # История сканирований (paginated)
GET /api/v1/scan/history/{scan_id}    # Детали конкретного сканирования
GET /api/v1/scan/history/summary      # Сводная статистика по сканированиям
```

**Пример ответа `/api/v1/scan/history`:**
```json
{
  "items": [
    {
      "id": "uuid-string",
      "started_at": "2026-03-01T19:00:00",
      "completed_at": "2026-03-01T19:01:00",
      "city": "minsk",
      "city_name": "Минск",
      "status": "completed",
      "trigger_type": "manual",
      "listings_fetched": 540,
      "listings_created": 15,
      "listings_updated": 520,
      "listings_deleted": 5,
      "pages_scraped": 18,
      "duration_seconds": 53,
      "error_message": null
    }
  ],
  "total": 150
}
```

**Пример ответа `/api/v1/scan/history/summary`:**
```json
{
  "total_scans": 150,
  "completed_scans": 145,
  "failed_scans": 3,
  "running_scans": 2,
  "total_listings_fetched": 75000,
  "total_listings_created": 1500,
  "total_listings_updated": 72000,
  "total_listings_deleted": 1500,
  "avg_duration_seconds": 52
}
```

### Export (v2.0)
```bash
# Экспорт объявлений в CSV/XLSX/JSON
GET /api/v1/export/listings?format=csv&city=minsk&status=active&price_from=50000&price_to=150000&rooms=1&rooms=2

# Экспорт сводной статистики
GET /api/v1/export/summary?format=xlsx
```

**Параметры экспорта:**
- `format`: `csv`, `xlsx`, `json` (по умолчанию: csv)
- `city`: фильтр по городу
- `status`: фильтр по статусу
- `price_from`: минимальная цена
- `price_to`: максимальная цена
- `rooms`: количество комнат (можно указать несколько)

**Пример CSV:**
```csv
id,kufar_id,title,price_byn,price_usd,currency,city,address,rooms,area,floor,url,status,first_seen_at,last_seen_at
uuid,12345,2-комн квартира,125000,38000,BYN,minsk,пр. Независимости,2,54.5,3/9,https://...,active,2026-03-01,2026-03-03
```

### Пример ответа `/api/v1/scan/progress`:
```json
{
  "is_scanning": true,
  "city": "mogilev",
  "city_name": "Могилёв",
  "stage": "parsing",
  "pages_scraped": 18,
  "listings_fetched": 540,
  "listings_processed": 200,
  "is_stable": false,
  "elapsed_seconds": 45
}
```

**Поля ответа:**
- `is_scanning` — backend сканирует в данный момент
- `stage` — текущая стадия (fetching, parsing, upserting, etc.)
- `pages_scraped` — количество спарсенных страниц
- `listings_fetched` — количество найденных объявлений
- `listings_processed` — количество обработанных объявлений
- `is_stable` — данные стабильны (не меняются)
- `elapsed_seconds` — время выполнения в секундах

## Схема базы данных

### Таблица `listings`

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `kufar_id` | String | ID объявления на Kufar (уникальный) |
| `url` | Text | Ссылка на объявление |
| `title` | Text | Заголовок |
| `price` | Integer | Цена в BYN |
| `price_usd` | Integer | Цена в USD (опционально) |
| `currency` | String | Валюта: BYN или USD |
| `city` | String | Код города |
| `address` | Text | Адрес/местоположение |
| `rooms` | Integer | Количество комнат |
| `area` | Float | Площадь (м²) |
| `floor` | Integer | Этаж |
| `total_floors` | Integer | Этажность дома |
| `category` | String | Категория |
| `description` | Text | Описание объявления |
| `district` | String | Район города |
| `metro` | String | Станция метро |
| `house_year` | Integer | Год постройки |
| `images` | JSONB | Массив URL изображений |
| `raw_data` | JSONB | Исходные данные |
| `status` | Enum | Статус (new, active, updated, deleted, archived) |
| `first_seen_at` | DateTime | Первое обнаружение |
| `last_seen_at` | DateTime | Последнее обнаружение |
| `deleted_at` | DateTime | Дата удаления |

### Таблица `listing_history`

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `listing_id` | UUID | Внешний ключ на listings |
| `event_type` | Enum | Тип события (created, price_changed, edited, deleted, restored) |
| `price_before` | Integer | Цена до изменения |
| `price_after` | Integer | Цена после изменения |
| `changed_fields` | JSONB | Изменённые поля |
| `snapshot` | JSONB | Снимок данных на момент события |
| `created_at` | DateTime | Время события |

### Таблица `scan_history`

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `started_at` | DateTime | Время начала сканирования |
| `completed_at` | DateTime | Время завершения (NULL если ещё сканирует) |
| `city` | String | Код города (minsk, mogilev, etc.) |
| `city_name` | String | Название города на русском |
| `status` | String | Статус: running, completed, error |
| `trigger_type` | String | Тип запуска: manual, scheduled |
| `listings_fetched` | Integer | Количество найденных объявлений |
| `listings_created` | Integer | Количество созданных записей |
| `listings_updated` | Integer | Количество обновленных записей |
| `listings_deleted` | Integer | Количество помеченных как удаленные |
| `pages_scraped` | Integer | Количество спарсенных страниц |
| `errors` | JSONB | Массив сообщений об ошибках |
| `duration_seconds` | Integer | Продолжительность в секундах |
| `error_message` | Text | Сообщение об ошибке если status=error |

**Индексы:**
- `ix_scan_history_city` на колонке `city`

### Таблица `scan_settings`

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | Integer | Первичный ключ (всегда = 1) |
| `scan_interval_minutes` | Integer | Интервал сканирования в минутах (5-1440) |
| `enabled` | Boolean | Включить/выключить автоматическое сканирование |
| `updated_at` | DateTime | Время последнего обновления настроек |

**Ограничения:**
- `check_min_interval`: scan_interval_minutes >= 5
- `check_max_interval`: scan_interval_minutes <= 1440

**Примечание:** Таблица содержит только одну запись с `id = 1`

## Переменные окружения

Создайте файл `.env` или измените `docker-compose.yml`:

```env
# Backend
DATABASE_URL=postgresql+asyncpg://postgres:secret@db/kufar_monitor
KUFAR_CITY=mogilev
API_PREFIX=/api/v1

# Database
POSTGRES_DB=kufar_monitor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
```

**Примечание:** `SCAN_INTERVAL_MINUTES` больше не используется — интервал сканирования настраивается через веб-интерфейс (`/settings`) или API (`PUT /api/v1/scan/schedule`).

## Доступные города

| Код | Город |
|-----|-------|
| `minsk` | Минск |
| `mogilev` | Могилёв |
| `grodno` | Гродно |
| `brest` | Брест |
| `gomel` | Гомель |
| `vitebsk` | Витебск |

## Статусы объявлений

| Статус | Описание |
|--------|----------|
| `new` | Новое объявление (первое обнаружение в текущем цикле сканирования) |
| `active` | Активное объявление (без изменений цены или восстановлено после удаления) |
| `updated` | Объявление обновлено — **изменилась цена в долларах (price_usd)** |
| `price_changed_byn` | Изменилась цена в **BYN** (без изменения USD цены) |
| `deleted` | Объявление удалено (исчезло с Kufar.by) — хранится 30 дней |
| `archived` | Архивное объявление — удалено более 30 дней назад (автоматически) |

**Автоматическая архивация:**
- Перед каждым сканированием вызывается `archive_old_deleted_listings(days_threshold=30)`
- Все объявления со статусом `deleted` и `deleted_at < 30 дней` получают статус `archived`
- Архивные объявления скрыты из выдачи по умолчанию
- Для просмотра используйте фильтр `status=archived`

## Соглашения разработки

### Frontend

- **TypeScript** — строгая типизация включена
- **Компоненты** — функциональные компоненты с хуками
- **State Management** — Zustand для фильтров, TanStack Query для API
- **Styling** — TailwindCSS 4 с shadcn/ui компонентами
- **Icons** — lucide-react
- **Именование файлов** — PascalCase для компонентов, camelCase для утилит

### Backend

- **Python** — type hints с Pydantic моделями
- **Async** — Async SQLAlchemy и asyncpg
- **Logging** — loguru для структурированного логирования
- **Error handling** — HTTPException с соответствующими кодами статуса

### Тестирование

#### Frontend (Playwright E2E + Vitest Unit)

```bash
cd frontend

# Установить зависимости
npm install

# Установить браузеры
npx playwright install chromium

# Запустить E2E тесты
npm run test:e2e                    # Все E2E тесты (19 тестов)
npm run test:e2e:chromium           # Только Chromium
npm run test:e2e:ui                 # UI режим для отладки
npm run test:e2e:headed             # В режиме браузера

# Запустить Unit тесты
npm run test:unit                   # Все Unit тесты (251 тест)
npm run test:unit:watch             # Режим наблюдения
npm run test:unit:coverage          # Unit тесты с coverage (55.86%)

# Запустить все тесты с покрытием
npm run coverage                    # Все тесты (Unit + E2E) с coverage
npm run test:e2e:coverage           # E2E тесты с coverage

# Просмотреть отчёты
npm run coverage:show               # Открыть HTML отчёт coverage
npx playwright show-report          # E2E отчёт тестов
open coverage/vitest/index.html     # Unit coverage отчёт
```

**Покрытие тестами Frontend:**

| Тип тестов | Количество | Coverage |
|------------|------------|----------|
| **E2E (Playwright)** | 118 тестов | ✅ V8 format |
| **Unit (Vitest)** | 326 тестов | 66.12% statements |

**Unit тесты (Vitest) — 326 тестов:**
- ✅ **Store (filterStore.ts)** — 21 тест (86.66% покрытие): фильтры, сортировка, пагинация, persist, manual scanning
- ✅ **Hooks (use-mobile.tsx)** — 9 тестов (90% покрытие): matchMedia mock, resize events
- ✅ **API hooks (listings.ts)** — 16 тестов: useListings, useListing, useSummary, useManualScan, mutations
- ✅ **UI Components** — 200+ тестов (22 файла, 100% покрытие): accordion, alert, avatar, badge, button, card, dialog, input, label, pagination, popover, progress, rooms-filter, select, separator, skeleton, switch, table, tabs, tooltip
- ✅ **Chart Components** — 13 тестов: PriceTrendChart (73.33% покрытие)
- ✅ **Listing Components** — 34 теста: ListingInfoCard (14 тестов, 100%), HistoryTimeline (20 тестов, 82.75%)
- ✅ **Layout Components** — 12 тестов: AppSidebar (100% покрытие)
- ✅ **Pages** — 19 тестов: Settings (11 тестов, 95.65%), Statistics (8 тестов, 91.66%)
- ✅ **Utils (utils.ts)** — 4 теста (100% покрытие): cn

**E2E тесты (Playwright) — 118 тестов:**
- ✅ **Dashboard** — 10 тестов: загрузка, карточки статистики, навигация, смена города
- ✅ **Listings** — 22 теста: загрузка, объявления, фильтры, сортировка, пагинация
- ✅ **Listing Detail** — 5 тестов: галерея, цена, статус, ссылка на Kufar
- ✅ **Settings** — 11 тестов: настройки города, интервала, автосканирование, валидация
- ✅ **Statistics** — 18 тестов: графики, табы комнат, селекторы города/периода
- ✅ **Navigation** — 11 тестов: переходы между страницами, боковая панель
- ✅ **UI Components** — 16 тестов: тёмная тема, иконки, hover эффекты, responsive
- ✅ **API Endpoints** — 18 тестов: health, cities, schedule, stats, listings, history
- ✅ **Mobile Responsive** — 3 теста: мобильная, планшетная, desktop версии
- ✅ **Scanning** — 2 теста: кнопка, запуск сканирования
- ✅ **API Integration** — 2 теста: загрузка данных, запрос к API

**Структура тестов:**
```
frontend/
├── tests/                          # E2E тесты (Playwright, 118 тестов)
│   ├── fixtures.ts                 # Фикстуры с coverage
│   ├── dashboard.spec.ts           # 3 теста
│   ├── dashboard-extended.spec.ts  # 7 тестов
│   ├── listings.spec.ts            # 4 теста
│   ├── listings-filters.spec.ts    # 18 тестов
│   ├── listing-detail.spec.ts      # 5 тестов
│   ├── mobile.spec.ts              # 3 теста
│   ├── scanning.spec.ts            # 2 теста
│   ├── api-integration.spec.ts     # 2 теста
│   ├── settings.spec.ts            # 11 тестов NEW
│   ├── statistics.spec.ts          # 18 тестов NEW
│   ├── navigation.spec.ts          # 11 тестов NEW
│   ├── ui-components.spec.ts       # 16 тестов NEW
│   ├── api-endpoints.spec.ts       # 18 тестов NEW
│   └── pages/                      # Page Object модели
│       ├── DashboardPage.tsx
│       ├── ListingsPage.tsx
│       ├── SettingsPage.tsx        # NEW
│       ├── StatisticsPage.tsx      # NEW
│       └── index.ts
├── src/
│   ├── api/listings.test.ts        # Unit: API hooks (16 тестов)
│   ├── components/
│   │   ├── ui/*.test.tsx           # Unit: UI компоненты (22 файла, 100% покрытие)
│   │   ├── charts/PriceTrendChart.test.tsx  # Unit: график цен (13 тестов)
│   │   ├── listing/                # Unit: listing компоненты
│   │   │   ├── HistoryTimeline.test.tsx  # 20 тестов
│   │   │   └── ListingInfoCard.test.tsx  # 14 тестов
│   │   └── Layout.test.tsx         # Unit: Layout (12 тестов)
│   ├── hooks/use-mobile.test.ts    # Unit: хуки (9 тестов)
│   ├── lib/utils.test.ts           # Unit: утилиты (4 теста)
│   ├── pages/
│   │   ├── Settings.test.tsx       # 11 тестов (95.65%)
│   │   └── Statistics.test.tsx     # 8 тестов (91.66%)
│   └── store/filterStore.test.ts   # Unit: store (21 тест)
├── coverage/vitest/                # Coverage отчёты (Unit, 66.12%)
├── playwright-report/              # E2E отчёты + coverage
└── playwright.config.ts            # Конфигурация
```

**Важно:**
- E2E coverage требует запуска через `npm run test:e2e:coverage` для генерации финального отчёта
- Coverage API работает только в Chromium (не поддерживается в Firefox/WebKit)

#### Backend (Pytest API)

```bash
cd backend

# Установить тестовые зависимости
pip install -r requirements-test.txt

# Запустить все тесты (использует отдельную БД kufar_monitor_test)
docker-compose exec backend python -m pytest tests/ -v

# Запустить с отчётом о покрытии
docker-compose exec backend python -m pytest tests/ --cov=app --cov-report=html

# Запустить конкретный тест
docker-compose exec backend python -m pytest tests/test_health.py -v

# Запустить тесты с пересозданием тестовой БД
docker-compose exec db_test psql -U postgres -c "DROP DATABASE IF EXISTS kufar_monitor_test;"
docker-compose exec db_test psql -U postgres -c "CREATE DATABASE kufar_monitor_test;"
docker-compose exec backend python -m pytest tests/ -v
```

**Покрытие тестами (172 тест):**
- ✅ Health Check (5 тестов)
- ✅ Listings API (17 тестов)
- ✅ Stats API (12 тестов)
- ✅ Scan API (18 тестов)
- ✅ Scan History API (13 тестов)
- ✅ History API (5 тестов)
- ✅ Logging (20 тестов)
- ✅ Retry Logic (16 тестов)
- ✅ **Listing Service (28 тестов)** — upsert, diff, mark_deleted, get_ids
- ✅ **Kufar Client (25 тестов)** — API fetch, scraper, error handling
- ✅ **Scheduler (24 теста)** — progress tracking, status, update schedule

**Структура тестов:**
```
backend/tests/
├── conftest.py                 # Фикстуры (HTTP клиент, БД)
├── test_health.py              # Health check endpoint
├── test_listings.py            # Listings API
├── test_stats.py               # Stats API
├── test_scan.py                # Scan API + schedule
├── test_scan_history.py        # Scan history API
├── test_history.py             # History API
├── test_logging.py             # Logging configuration
├── test_retry_logic.py         # Retry logic for scraper
├── test_listing_service.py     # ListingService unit tests
├── test_kufar_client.py        # KufarAPIClient unit tests
└── test_scheduler.py           # ScraperScheduler unit tests
```

**Важно:**
- Backend тесты используют отдельную БД `kufar_monitor_test` на порту 5433
- Production БД `kufar_monitor` на порту 5432 не используется в тестах
- Каждый тест работает в отдельной транзакции с автооткатом
- **Покрытие:** 55% (цель — 65%)

## Итоговое покрытие тестов

| Проект | Тесты | Покрытие |
|--------|-------|----------|
| **Frontend Unit** | 251 тест | 55.86% statements |
| **Frontend E2E** | 19 тестов | V8 format |
| **Backend API** | 172 тест | 55% statements |
| **ВСЕГО** | **441 тест** | **~55% average** |

## Troubleshooting

**Порт занят:**
```bash
docker-compose down && docker-compose up --build
```

**Проблемы с БД:**
```bash
docker-compose down -v  # ⚠️ Удаляет все данные!
docker-compose up --build
```

**Объявления не загружены:**
- Проверьте доступность Kufar.by
- Проверьте логи: `docker-compose logs backend`

## Ключевые детали реализации

### Компонент History Timeline

Компонент `HistoryTimeline` (`frontend/src/components/listing/HistoryTimeline.tsx`) отображает вертикальную линию времени событий объявления:

- **5 типов событий**: created, price_changed, edited, deleted, restored
- **Цветные badge** для каждого типа события
- **Отображение изменения цены**: показывает старую и новую цену
- **Изменённые поля**: отображение старых и новых значений
- **Русский формат дат** с иконкой календаря

### Тёмная тема

Приложение использует современную тёмную цветовую схему, определённую в `frontend/src/index.css`:

- **Background**: `oklch(0.15 0.01 280)` — тёмно-серый
- **Card**: `oklch(0.2 0.01 280)` — светлее тёмно-серый
- **Text**: `oklch(0.9 0.01 280)` — светлый текст
- **Primary**: `oklch(0.9 0.01 280)` — светлый для контраста

### Боковая навигация

Компонент `AppSidebar` (`frontend/src/components/Layout.tsx`) предоставляет:

- **Сворачиваемая** — кнопка внизу для переключения развёрнуто/свёрнуто
- **Навигация** — ссылки Dashboard и Listings
- **Тёмная тема** — соответствует общему дизайну
- **Адаптивная** — работает на мобильных с Sheet компонентом

### Real-time прогресс сканирования

**Backend (`backend/app/scraper/scheduler.py`):**

- **Флаг `is_stable`** — показывает стабильность данных:
  - `true` — на стадиях `marking_deleted_final`, `done`, `error`
  - `false` — во время `fetching`, `parsing`, `upserting`
- **Оценка количества** — если `listings_fetched = 0`, используется `pages_scraped * 30`

**Frontend (`frontend/src/pages/Listings.tsx`):**

- **Расчёт прогресса по стадиям**:
  - `fetching`: 0-50% на основе страниц
  - `parsing`: 50-80% на основе объявлений
  - `upserting`: 80-100% на основе обработанных
  - `done`: 100%
- **Индикатор "● Обновляется..."** — показывается когда `is_stable = false`
- **Глобальное состояние** — `isManualScanning` в Zustand store для сохранения при навигации

**Стадии сканирования:**
1. `starting` — запуск
2. `marking_deleted` — подготовка базы
3. `fetching` — парсинг страниц Kufar
4. `parsing` — обработка данных
5. `upserting` — сохранение в базу
6. `marking_deleted_final` — финальное обновление статусов
7. `done` — завершено

### Scan History Tracking

**Файлы:**
- `backend/app/models/listing.py` — модель `ScanHistory`
- `backend/app/services/scan_history_service.py` — сервис для управления историей
- `backend/app/scraper/scheduler.py` — интеграция со сканером
- `backend/app/api/v1/scan.py` — API endpoints

**Функционал:**
- Автоматическое создание записи при запуске сканирования (ручного или по расписанию)
- Обновление статистики во время выполнения (listings_fetched, pages_scraped, errors)
- Завершение записи с указанием статуса (completed/error) и продолжительности
- Фильтрация по городу и статусу
- Сводная статистика по всем сканированиям

**Сервис `ScanHistoryService`:**
```python
# Создание записи
scan = await service.create_scan_record(
    city="minsk",
    city_name="Минск",
    trigger_type="manual"  # или "scheduled"
)

# Обновление статистики
await service.update_scan_record(
    scan_id=scan.id,
    listings_fetched=540,
    listings_created=15,
    listings_updated=520,
    listings_deleted=5,
    pages_scraped=18,
    errors=[]
)

# Завершение
await service.complete_scan_record(
    scan_id=scan.id,
    status="completed",  # или "error"
    error_message=None
)

# Получение истории
scans = await service.get_scan_history(limit=50, city="minsk")

# Сводка
summary = await service.get_summary()
```

### Настройка расписания сканирования

**Файлы:**
- `backend/app/models/listing.py` — модель `ScanSettings`
- `backend/app/services/scan_settings_service.py` — сервис для управления настройками
- `backend/app/scraper/scheduler.py` — динамическое обновление расписания
- `backend/app/api/v1/scan.py` — API endpoints (`GET/PUT /api/v1/scan/schedule`)
- `frontend/src/pages/Settings.tsx` — UI компонент настройки
- `frontend/src/api/listings.ts` — API hooks (`useScanSchedule`, `useUpdateScanSchedule`)

**Функционал:**
- Хранение настроек в БД (таблица `scan_settings`)
- Интервал сканирования: 5-1440 минут (от 5 мин до 24 часов)
- Включение/выключение автоматического сканирования
- Динамическое обновление расписания без перезапуска backend
- Настройка через веб-интерфейс (`/settings`) или API

**Сервис `ScanSettingsService`:**
```python
# Получение настроек
settings = await service.get_settings()
# ScanSettings(id=1, scan_interval_minutes=30, enabled=True)

# Обновление интервала
await service.update_settings(scan_interval_minutes=60)

# Отключение сканирования
await service.update_settings(enabled=False)

# Обновление обоих полей
await service.update_settings(
    scan_interval_minutes=45,
    enabled=True
)
```

**API примеры:**
```bash
# Получить настройки
curl http://localhost:8000/api/v1/scan/schedule

# Обновить интервал
curl -X PUT http://localhost:8000/api/v1/scan/schedule \
  -H "Content-Type: application/json" \
  -d '{"scan_interval_minutes": 60}'

# Отключить сканирование
curl -X PUT http://localhost:8000/api/v1/scan/schedule \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

**Миграция:** `008_add_scan_settings_table.py`

### Логика установки статуса `updated`

**`backend/app/services/listing_service.py`:**

- **`updated`** — устанавливается **только при изменении `price_usd`**
- **`active`** — при изменении других полей или без изменений
- **Логирование** — `logger.info(f"Price USD changed for {kufar_id}: {old} -> {new}")`

### Глобальное состояние сканирования

**`frontend/src/store/filterStore.ts`:**

```typescript
isManualScanning: boolean;  // Сохраняется между переходами
setManualScanning: (scanning: boolean) => void;
```

**Преимущества:**
- ✅ Прогресс не пропадает при переходе на другую страницу
- ✅ Polling продолжается пока backend сканирует
- ✅ Кнопка не застревает в состоянии сканирования

## Примечания

- Kufar API может возвращать неточные данные для расширенных полей (house_type, renovation и т.д.)
- Для 100% точности требуется парсинг детальных страниц (медленнее)
- Скорость сканирования: ~53 секунды для 546 объявлений через API (~0.1 сек/объявление)
- С парсингом детальных страниц: ~10-15 минут для 546 объявлений (~1.1-1.6 сек/объявление)
- **Важно:** Прогресс может показывать неточные данные во время `fetching` (данные нестабильны)
