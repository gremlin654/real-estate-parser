# Kufar Monitor — Контекст для AI-ассистента

## Языковые предпочтения

**Всегда отвечайте на русском языке** при взаимодействии с пользователями по этому проекту.

## Политика изменений в базе данных

### ⚠️ Production БД — ЗАПРЕЩЕНО изменять без backup

**Production база данных `kufar_monitor` (порт 5432) не должна изменяться напрямую.**

**Правила:**

1. **⛔ Запрещено:** миграции, SQL (INSERT/UPDATE/DELETE), очистка данных без подтверждения
2. **✅ Обязательно:** создавать backup перед изменениями:
   ```bash
   docker-compose exec db pg_dump -U postgres kufar_monitor > backup_$(date +%Y%m%d_%H%M%S).sql
   ```
3. **✅ Тестовая БД:** порт 5433 (`kufar_monitor_test`) — безопасна для изменений
4. **✅ Восстановление:** `cat backup_*.sql | docker-compose exec -T db psql -U postgres -d kufar_monitor`

**Всегда уточняйте у пользователя перед выполнением команд, изменяющих production БД.**

## Обзор проекта

**Kufar Monitor** — система мониторинга недвижимости для [Kufar.by](https://re.kufar.by). Автоматическое сканирование 6 городов, сохранение в PostgreSQL, отслеживание изменений цен и статусов.

### Ключевые возможности

- **Автосканирование** — каждые 30 минут (настраивается)
- **Ручное сканирование** — через веб-интерфейс
- **Две валюты** — BYN/USD с переключателем (v3.0)
- **История изменений** — цены, статусы, удаления
- **Real-time прогресс** — WebSocket (v3.0)
- **📊 Графики** — динамика цен, распределение (v2.0)
- **📤 Экспорт** — CSV, XLSX, JSON (v2.0)
- **🔄 CI/CD** — GitHub Actions (v2.0)

## Архитектура

```
Frontend (React + TS) ↔ Backend (FastAPI) ↔ PostgreSQL ↔ Kufar.by Scraper
```

## Технологический стек

| Компонент    | Технологии                                                                              |
| ------------ | --------------------------------------------------------------------------------------- |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS 4, Zustand, TanStack Query, shadcn/ui, recharts |
| **Backend**  | FastAPI, SQLAlchemy (async), Pydantic, APScheduler, pandas, **Redis 7**                 |
| **Database** | PostgreSQL 16, Alembic, **Redis 7**                                                     |
| **Scraper**  | Playwright, BeautifulSoup4, aiohttp                                                     |
| **Testing**  | Playwright E2E (118), Vitest Unit (326, 66% coverage), pytest API (201, 55%)            |

## 🔴 Redis Integration

Проект использует Redis 7 для кэширования, distributed locking, state management и rate limiting.

### Архитектура

```
Frontend (React 19) ↔ Backend (FastAPI) ↔ Redis 7
                              ↓
                        PostgreSQL 16
```

### Компоненты

| Компонент | Описание | TTL | Файл |
|-----------|----------|-----|------|
| **Кэширование API** | Stats и Listings endpoints | 30-300 сек | `decorators/cache.py` |
| **Distributed Lock** | Блокировка сканирования городов | 3600 сек | `core/redis_lock.py` |
| **WebSocket State** | Прогресс сканирования (Hash + Pub/Sub) | 7200 сек | `core/redis_pubsub.py` |
| **Rate Limiting** | Token Bucket для scraper | 3600 сек | `core/rate_limiter.py` |
| **Мониторинг** | Health, memory, stats endpoints | N/A | `api/v1/monitoring.py` |

### Запуск Redis

```bash
docker-compose up -d redis
```

### Проверка подключения

```bash
# Ping Redis
docker-compose exec redis redis-cli ping
# PONG

# Проверка ключей
docker-compose exec redis redis-cli KEYS "*"

# Статистика кэша
docker-compose exec redis redis-cli INFO stats | grep keyspace

# Мониторинг через API
curl http://localhost:8000/monitoring/redis
```

### Конфигурация

| Переменная | Значение | Описание |
|------------|----------|----------|
| `REDIS_URL` | `redis://redis:6379/0` | Production БД |
| `REDIS_TEST_URL` | `redis://redis:6379/1` | Test БД |
| `CACHE_TTL_STATS_SUMMARY` | 60 | Кэш сводной статистики (сек) |
| `CACHE_TTL_STATS_OTHER` | 300 | Кэш остальной статистики (сек) |
| `CACHE_TTL_LISTINGS` | 30 | Кэш объявлений (сек) |
| `SCAN_LOCK_TIMEOUT` | 3600 | Блокировка сканирования (сек) |
| `RATE_LIMIT_CAPACITY` | 10 | Burst запросов (токены) |
| `RATE_LIMIT_REFILL_RATE` | 10.0 | Токенов/секунду |

### API Endpoints

#### Monitoring

```bash
GET /monitoring/redis              # Health, memory, clients, uptime
GET /monitoring/redis/keys         # Список ключей
GET /monitoring/redis/memory       # Детальная информация о памяти
GET /monitoring/redis/stats        # Статистика команд, connections
GET /monitoring/redis/slowlog      # Медленные запросы
```

#### Cache Management

```bash
DELETE /api/v1/cache/invalidate?pattern=cache:*  # Инвалидация по шаблону
GET /api/v1/cache/stats                          # Статистика кэша
POST /api/v1/cache/clear/all                     # Полная очистка
```

### Документация

- **Redis Keys Reference:** `docs/REDIS_KEYS.md` — полный справочник ключей
- **Redis Dashboard:** `docs/REDIS_DASHBOARD.md` — мониторинг и alerts

### Тесты

```bash
# Все Redis тесты
docker-compose exec backend python -m pytest tests/test_redis*.py tests/test_monitoring.py -v

# Coverage
docker-compose exec backend python -m pytest tests/test_redis*.py tests/test_monitoring.py --cov=app/core --cov=app/decorators --cov=app/api/v1/monitoring
```

### Troubleshooting

**Проблема:** Redis не отвечает
```bash
docker-compose restart redis
docker-compose logs redis
```

**Проблема:** Закончилась память
```bash
# Очистить кэш
curl -X POST "http://localhost:8000/api/v1/cache/clear/all"

# Проверить использование памяти
curl http://localhost:8000/monitoring/redis/memory
```

**Проблема:** Lock не сбрасывается
```bash
# Принудительно удалить lock
docker-compose exec redis redis-cli DEL lock:scan:minsk
```

**Проблема:** Кэш не обновляется
```bash
# Проверить ключи
docker-compose exec redis redis-cli KEYS "cache:*"

# Инвалидировать кэш
curl -X DELETE "http://localhost:8000/api/v1/cache/invalidate?pattern=cache:stats:*"
```

### Метрики производительности

| Endpoint | До Redis | После Redis | Улучшение |
|----------|----------|-------------|-----------|
| `/stats/summary` | ~120-170ms | ~5-6ms | **20-30x** 🚀 |
| `/stats/price-trends` | ~200-300ms | ~5-10ms | **20-40x** 🚀 |
| `/stats/room-distribution` | ~150-250ms | ~5-10ms | **20-30x** 🚀 |
| `/listings` | ~100-200ms | ~20-50ms | **5-10x** 🚀 |

### Покрытие тестами

- **Redis Infrastructure:** 94% coverage
- **Redis Lock:** 85% coverage
- **Redis Pub/Sub:** 72% coverage
- **Rate Limiter:** 96% coverage
- **Cache Decorator:** 76% coverage
- **Monitoring:** 77% coverage

**Всего тестов:** 100 (94 passed, 6 skipped)

## Структура проекта

```
web/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # API: listings, stats, scan, export, ws
│   │   ├── models/           # Listing, ListingHistory, ScanHistory
│   │   ├── services/         # listing_service, scan_history_service
│   │   ├── scraper/          # scheduler, parser, kufar_*.py
│   │   └── main.py
│   ├── tests/                # 201 тест
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # TanStack Query, WebSocket hooks
│   │   ├── components/       # shadcn/ui, charts, listing
│   │   ├── pages/            # Dashboard, Listings, Settings
│   │   └── store/            # Zustand (filterStore)
│   ├── tests/                # Playwright E2E (118 тестов)
│   └── package.json
├── docker-compose.yml
└── README.md
```

# Тесты

docker-compose exec backend python -m pytest tests/ -v
docker-compose exec backend python -m pytest tests/ --cov=app

````

### Frontend
```bash
cd frontend
npm install
npm run dev

# Тесты
npm run test:e2e          # Playwright (118 тестов)
npm run test:unit         # Vitest (326 тестов)
npm run test:unit:coverage  # Coverage (66.12%)
npm run coverage          # Все тесты + coverage
````

## 📋 Правила разработки и Workflow

### 1️⃣ Workflow: от задачи до продакшена

**Стандартный pipeline:**

```
Задача → Product Manager (декомпозиция) → Issue → Branch → Development → Tests → Pull Request → Review → Merge → Deploy
```

**Правила:**

- **Каждая задача сначала передаётся `product-manager-agent`** на декомпозицию и создание спецификаций
- Каждая задача → отдельная ветка
- MR (PR) можно создать только если тесты проходят
- MR нельзя смержить без review
- CI должен быть зелёным

---

### 2️⃣ Ветвление (Branching Strategy)

```
main        — production
develop     — staging
feature/*   — новые фичи
fix/*       — баги
```

**Примеры:**

- `feature/price-filter`
- `fix/scan-history-bug`
- `feature/websocket-progress`

---

### 3️⃣ Обязательные тесты перед MR

**Перед созданием MR обязательно:**

```bash
# backend tests
pytest

# frontend tests
npm run test:unit

# e2e tests
npm run test:e2e
```

**⛔ Если хоть один тест падает → MR запрещён.**

---

### 4️⃣ Требования к Merge Request

**MR можно смержить только если:**

- ✔ CI зелёный
- ✔ 1 code review получено
- ✔ нет конфликтов слияния
- ✔ coverage не упал

---

### 5️⃣ Branch Protection (GitHub Settings)

**Для ветки `main` включить:**

- Require pull request before merging
- Require status checks to pass
- Require review
- Require branches to be up to date

**Status checks:**

- `backend-tests`
- `frontend-tests`
- `e2e-tests`
- `lint`

---

### 6️⃣ CI Pipeline (GitHub Actions)

**Файл:** `.github/workflows/ci.yml`

**Jobs:**

- `backend-tests` — pytest для backend
- `frontend-tests` — vitest для frontend
- `e2e-tests` — Playwright для E2E

**Срабатывание:**

- `pull_request` — для всех PR
- `push` — для develop

---

### 7️⃣ Pull Request Template

**Файл:** `.github/pull_request_template.md`

**Чеклист для PR:**

- [ ] Backend тесты проходят
- [ ] Frontend тесты проходят
- [ ] E2E тесты проходят
- [ ] Проверена работа локально
- [ ] Нет console errors
- [ ] Обновлена документация

---

### 8️⃣ Pipeline для AI-ассистентов

**При получении задачи:**

1. **Передать `product-manager-agent`** на декомпозицию и создание спецификаций
2. Запустить backend тесты
3. Запустить frontend unit тесты
4. Запустить Playwright E2E
5. Исправить все ошибки
6. Только после этого создавать PR

---

### 9️⃣ Идеальный Pipeline

```
Задача
   ↓
Product Manager Agent (декомпозиция, спецификации)
   ↓
Developer
   ↓
Feature branch
   ↓
Local tests
   ↓
Pull Request
   ↓
GitHub CI
   ↓
Code Review
   ↓
Merge → develop
   ↓
Staging tests
   ↓
Merge → main
   ↓
Production deploy
```

---

### 🔟 Production БД — Дополнительные правила

**⚠ Любое изменение production DB:**

1. Сделать backup:
   ```bash
   docker-compose exec db pg_dump -U postgres kufar_monitor > backup_$(date +%Y%m%d_%H%M%S).sql
   ```
2. Проверить на test DB (порт 5433)
3. Только потом migration

**Запрещено:**

- Push в `main` напрямую — только через PR
- Изменение production БД без backup
- Миграции без тестирования на staging

---

## API Endpoints

### Listings

```bash
GET /api/v1/listings?page=1&size=20&status=active&city=minsk
GET /api/v1/listings/{id}
GET /api/v1/history/{id}  # История изменений
```

### Stats

```bash
GET /api/v1/stats/summary?city=minsk
GET /api/v1/stats/price-trends?city=minsk&rooms=1
GET /api/v1/stats/room-distribution?city=minsk
GET /api/v1/stats/daily-activity?city=minsk&period_days=30
```

### Scan Management

```bash
POST /api/v1/scan/trigger      # Ручное сканирование
GET /api/v1/scan/status        # Статус
WS /ws/scan/progress           # WebSocket real-time (v3.0)
GET /api/v1/scan/cities        # Доступные города
GET /api/v1/scan/schedule      # Настройки расписания
PUT /api/v1/scan/schedule      # Обновить (interval: 5-1440 мин)
```

### Scan History

```bash
GET /api/v1/scan/history              # История (paginated)
GET /api/v1/scan/history/{scan_id}    # Детали
GET /api/v1/scan/history/summary      # Сводка
```

### Export (v2.0)

```bash
GET /api/v1/export/listings?format=csv&city=minsk&status=active
GET /api/v1/export/summary?format=xlsx
```

## Схема базы данных

### listings

- `id`, `kufar_id`, `url`, `title`, `price` (BYN), `price_usd`, `currency`
- `city`, `address`, `rooms`, `area`, `floor`, `images` (JSONB)
- `status` (new/active/updated/deleted/archived)
- `first_seen_at`, `last_seen_at`, `deleted_at`

### listing_history

- `id`, `listing_id`, `event_type` (created/price_changed/edited/deleted/restored)
- `price_before`, `price_after`, `changed_fields` (JSONB), `snapshot` (JSONB)

### scan_history

- `id`, `started_at`, `completed_at`, `city`, `status`, `trigger_type`
- `listings_fetched/created/updated/changed_byn/deleted/restored/unchanged`
- `pages_scraped`, `duration_seconds`

### scan_settings (1 запись, id=1)

- `scan_interval_minutes` (5-1440), `enabled`, `updated_at`

## Доступные города

| Код       | Город   |
| --------- | ------- |
| `minsk`   | Минск   |
| `mogilev` | Могилёв |
| `grodno`  | Гродно  |
| `brest`   | Брест   |
| `gomel`   | Гомель  |
| `vitebsk` | Витебск |

## Статусы объявлений

| Статус              | Описание                                   |
| ------------------- | ------------------------------------------ |
| `new`               | Первое обнаружение                         |
| `active`            | Активное (без изменений или восстановлено) |
| `updated`           | **Изменилась цена USD** (v3.0)             |
| `price_changed_byn` | Изменилась цена BYN (без изменения USD)    |
| `deleted`           | Удалено (хранится 30 дней)                 |
| `archived`          | Удалено >30 дней назад                     |

**Автоматическая архивация:** перед сканированием `deleted` → `archived` (если >30 дней)

**Восстановление (v3.0):** если `deleted` объявление появилось в API → статус `active`

**Действия upsert (v3.1):**

- `created` — новое объявление
- `updated` — изменена цена USD
- `changed_byn` — изменена цена BYН
- `restored` — восстановлено после удаления
- `unchanged` — без изменений

## Тестирование

### Frontend

```bash
cd frontend
npm run test:e2e                    # Playwright (118 тестов)
npm run test:unit                   # Vitest (129 тестов)
npm run test:unit:coverage          # Coverage (~90%)
npm run coverage                    # Все тесты + coverage
npm run coverage:show               # HTML отчёт
```

**Unit тесты (129):**

- Store (9), Hooks (9), API hooks
- UI Components (100+)
- Charts, Listing, Layout, Pages

**E2E тесты (118):**

- Dashboard, Listings, Listing Detail
- Settings, Statistics, Navigation
- UI Components, API Endpoints, Mobile

### Backend

```bash
cd backend
docker-compose exec backend python -m pytest tests/ -v
docker-compose exec backend python -m pytest tests/ --cov=app  # 52% coverage
```

**Тесты (75 unit + 54 integration):**

- Health (5), Listings, Stats
- Scan, Scan History, Scan Settings
- History, Logging (11)
- Listing Service (13, 90%), Kufar Client (11, 100%)
- Scheduler (22), Parser (18)

**Интеграционные тесты (54):**

- Export, History, Scan History, Scan Settings
- Требуют запущенную тестовую БД (порт 5433)

**Важно:** Backend тесты используют БД `kufar_monitor_test` (порт 5433)

## Ключевые детали реализации

### WebSocket API (v3.0)

**Endpoint:** `WS /ws/scan/progress`

```typescript
const ws = new WebSocket("ws://localhost:8000/ws/scan/progress");
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  // { is_scanning, city, stage, pages_scraped, listings_fetched, is_stable, elapsed_seconds }
};
```

**Frontend hook:** `useScanProgressWebSocket()` в `frontend/src/api/listings.ts`

### Стадии сканирования

1. `starting` → 2. `marking_deleted` → 3. `fetching` → 4. `parsing` → 5. `upserting` → 6. `marking_deleted_final` → 7. `done`

**Прогресс (Frontend):**

- `fetching`: 0-50% (pages_scraped)
- `parsing`: 50-80% (listings_fetched)
- `upserting`: 80-100% (listings_processed)

**Флаг `is_stable`:** `true` на `marking_deleted_final`/`done`/`error`, иначе `false`

### Логика статуса `updated` (v3.0)

```python
# backend/app/services/listing_service.py
old_price_usd = existing.price_usd
# ... обновление полей ...
if was_deleted:
    existing.status = ListingStatus.active  # Восстановление
elif old_price_usd != existing.price_usd:
    existing.status = ListingStatus.updated  # Изменение цены USD
else:
    existing.status = ListingStatus.active
```

### Парсинг данных Kufar (v3.0)

**Цены:** Kufar возвращает в копейках → делим на 100

```python
price = price_raw // 100  # 12,278,675 → 122,786 BYN = $42,500
```

**Ссылки:** `https://re.kufar.by/vi/{city}/kupit/kvartiru/{ad_id}`

**Картинки:** `https://rms.kufar.by/v1/gallery/{path}`

**Парсер:** `backend/app/scraper/kufar_scraper.py`, метод `_parse_ad()`

### Глобальное состояние сканирования

```typescript
// frontend/src/store/filterStore.ts
isManualScanning: boolean; // Сохраняется между переходами
```

**Преимущества:**

- Прогресс не пропадает при навигации
- Кнопка не застревает в состоянии сканирования

## Troubleshooting

```bash
# Порт занят
docker-compose down && docker-compose up --build

# Проблемы с БД (⚠️ удаляет данные!)
docker-compose down -v && docker-compose up --build

# Объявления не загружены
docker-compose logs backend
```

## Примечания

- Kufar API может возвращать неточные расширенные данные (house_type, renovation)
- Скорость сканирования: ~53 сек для 546 объявлений через API (~0.1 сек/объявление)
- **Важно:** Прогресс может показывать неточные данные во время `fetching` (данные нестабильны)

## Версии

### v3.3 (текущая)

- **✅ Запушены изменения в GitHub** — коммит `825ac95` в ветке `main`
- **🔴 Redis Integration (v3.2)** — кэширование, distributed locking, WebSocket state, rate limiting
- **📊 Monitoring API** — 5 endpoints для мониторинга Redis
- **⚡ Ускорение API** — в 20-40 раз для stats endpoints
- **🔒 Distributed Locking** — защита от дублирования сканирования
- **🔄 Rate Limiting** — Token Bucket для scraper (10 запросов/сек)
- **📚 Документация** — REDIS_KEYS.md, REDIS_DASHBOARD.md
- **🧪 Тесты Redis** — 100 тестов, 94% coverage

### v3.2

- **🔴 Redis Integration** — кэширование, distributed locking, WebSocket state, rate limiting
- **📊 Monitoring API** — 5 endpoints для мониторинга Redis
- **⚡ Ускорение API** — в 20-40 раз для stats endpoints
- **🔒 Distributed Locking** — защита от дублирования сканирования
- **🔄 Rate Limiting** — Token Bucket для scraper (10 запросов/сек)
- **📚 Документация** — REDIS_KEYS.md, REDIS_DASHBOARD.md

### v3.1

- **Исправлена статистика сканирования** — точный подсчёт created/updated/changed_byn/deleted/restored/unchanged
- **График распределения по комнатам 1, 2, 3, 4, 5+** — группировка 5+ комнатных, яркие цвета, белый текст
- **Бэкенд отдаёт все комнаты** — API `/stats/room-distribution` возвращает комнаты от 1 и больше
- **TriggerManualScanAlert** — алерт под кнопками на всю ширину
- **Анимация кнопки** — плавная анимация при сканировании

### v3.0

- WebSocket real-time прогресс
- Исправление цен (деление на 100)
- Статус `updated` при изменении `price_usd`
- Восстановление `deleted` объявлений
- Фильтр валюты USD/BYN
- Сортировка: newest, oldest, asc, desc

### v2.0

- Графики и аналитика
- Экспорт (CSV, XLSX, JSON)
- CI/CD pipeline

### v1.0

- Базовое сканирование, REST API, веб-интерфейс

Топ-5 приоритетных фич:

    ┌───────────┬───────────────────────────────────────────┬───────────┬─────────────────────────────────────────────┐
    │ Приоритет │ Фича                                      │ Сложность │ Ценность                                    │
    ├───────────┼───────────────────────────────────────────┼───────────┼─────────────────────────────────────────────┤
    │ P0        │ 📢 Система уведомлений (Telegram)         │ Medium    │ Мгновенное реагирование на новые объявления │
    │ P0        │ ⭐ Избранные объявления                   │ Low       │ Быстрый доступ к выбранным вариантам        │
    │ P1        │ 🔍 Расширенные фильтры (цена за м², этаж) │ Medium    │ Точный поиск по параметрам                  │
    │ P1        │ 📄 Детальная страница объявления          │ Medium    │ История изменений, графики цены             │
    │ P2        │ ⚖️ Сравнение объявлений                   │ High      │ Наглядное сравнение характеристик
