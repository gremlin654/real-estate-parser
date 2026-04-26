# Kufar Monitor — Контекст для AI-ассистента

## Языковые предпочтения

**Всегда отвечайте на русском языке** при взаимодействии с пользователями по этому проекту.

## Операционные заметки (2026-04-24)

- В локальном окружении может отсутствовать `gh` CLI (`zsh: command not found: gh`).
- MCP-интеграция GitHub может возвращать `401 Bad credentials`; в таком случае PR/MR создаётся вручную по URL из `git push`.
- В хост-окружении может не быть `python`/модуля `black`; для backend-форматирования используйте контейнер:
  `docker-compose exec backend black app/...` и проверку `docker-compose exec backend black --check app/...`.
- Для `DealScoreBadge` в UI и тестах актуальные пороги: `>=50` → `🔥` (зелёный), `35-49.9` → `👍` (жёлто-оранжевый), `<35` → не рендерится.
- Для `DealScoreService.calculate_label()` и backend-тестов действуют те же пороги: `>=50` → `🔥 HOT`, `35-49.99` → `👍 GOOD`, `<35` → `😐 NORMAL`.
- Telegram `/subscribe` расширен: после выбора комнат добавлен шаг валюты, затем `price_min`/`price_max`, `price_per_m2_max`, `floor_min`/`floor_max`, режим `price_drop`, порог `deal score`.
- В `EditSubscriptionFieldCallback.field` используются короткие коды (`curr`, `ppm2`, `floor`, `drop`, `deal`) — это нужно из-за лимита Telegram callback data (64 байта).
- Для редактирования через `editing_subscription` пропуск делается текстом `⏭️ Пропустить (любая цена)` в message-handler; inline callback `skip_price` в этом состоянии не обновляет БД (нет DB session в callback handler).
- `TelegramSubscriptionService.get_matching_subscriptions()` теперь принимает `event_type` (`new_listing` по умолчанию, `price_drop` для событий падения цены).
- В matching-логике: `notify_only_price_drop=True` отсекает `new_listing`; `exclude_deal_below_percent` требует `listing.deal_score >= threshold`.
- Edge-case по этажу исправлен: если фильтр `floor_min/floor_max` не задан, `listing.floor=None` больше не отбрасывает объявление.
- Целевые Telegram-тесты для этапа проходят: `tests/test_telegram_subscription_service.py` и `tests/test_telegram_handlers_subscriptions.py` (оба `-q` в Docker).
- Проверка форматирования Telegram-файлов проходит: `docker-compose exec backend black --check app/services/telegram_subscription_service.py tests/test_telegram_subscription_service.py app/telegram/handlers/subscriptions.py app/telegram/keyboards/inline.py tests/test_telegram_handlers_subscriptions.py`.
- `TelegramNotificationService` стал event-aware: добавлен общий приватный поток `_send_listings_notifications(...)` и публичный `send_price_drop_notifications(...)`; в matching передаётся `event_type`.
- `ScraperScheduler._send_telegram_notifications(...)` теперь разделяет отправку на `new_listing` и `price_drop`: новые объявления берутся по `first_seen_at >= scan_started_at`, события падения цены — по `ListingHistory` (`price_before > price_after`) за текущее сканирование.
- Для price-drop уведомлений `drop_percent` прокидывается в объект `Listing` динамически из истории (используется в message builder).
- Целевые тесты этапа: `tests/test_telegram_notification_service.py` и `tests/test_telegram_scheduler_integration.py` проходят (`-q` в Docker); в интеграционных тестах есть известные warning про `AsyncMock ... was never awaited` в старых lifespan-ветках.
- `TelegramMessageBuilder.build_listing_message()` получил параметр `event_type` (`new_listing` | `price_drop`): для `price_drop` — заголовок "📉 Цена снизилась", показывается `price_drop_percent` вместо `deal_percent`; для `new_listing` — заголовок "🏠 Новая квартира", показывается `deal_percent`.
- `TelegramNotificationService.send_listing_to_user()` и `_format_listing_message()` теперь принимают `event_type` и пробрасывают его в message builder.
- Тесты `tests/test_telegram_message_builder.py` обновлены: добавлены тесты `event_type=price_drop` и `event_type=new_listing`, `test_build_listing_message_full` больше не ожидает `📉 Цена упала` (т.к. по умолчанию `event_type=new_listing`), `test_build_listing_message_with_price_drop_only` использует `event_type="price_drop"`.
- **Дедупликация уведомлений**: добавлен `event_type` в `TelegramNotificationLog` + partial unique index `idx_telegram_notification_log_dedup` на (user_id, listing_id, subscription_id, event_type); новый метод `_is_duplicate_notification()` проверяет перед отправкой; `send_listing_to_user()` возвращает `duplicate` если уже отправлено; stats включают `duplicate` count. Миграция: `019_add_event_type_to_notification_log.py`.
- **Per-user rate limiting**: добавлен `_check_user_rate_limit()` — Redis как primary storage (`telegram:ratelimit:user:{user_id}:{YYYYMMDDHH}`, INCR + TTL 3900s), PostgreSQL fallback (COUNT за последний час); `TELEGRAM_USER_RATE_LIMIT_PER_HOUR=20` в config; stats включают `ratelimited_user`.
- **Phase 7: Graceful shutdown scheduler**: `scheduler.stop()` теперь `shutdown(wait=False)` (не блокирует shutdown event loop); добавлен `wait_for_running_jobs(timeout=30.0)` который ждёт завершения active jobs перед остановкой; main.py lifespan вызывает `await scheduler.wait_for_running_jobs()` перед `scheduler.stop()`.
- **Phase 8: Cleanup старых TelegramNotificationLog**: добавлен `TELEGRAM_NOTIFICATION_LOG_RETENTION_DAYS=30` в config; `cleanup_old_logs(retention_days)` в notification service (DELETE по cutoff date); ежедневный scheduled job `_run_notification_log_cleanup()` в APScheduler; миграция не нужна — cleanup по sent_at без схемы.
- **Phase 9: Docker/Env фикс**: исправлен `.env` для контейнера — лишние env vars (`CONTEXT7_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`) вызывали ошибку `Extra inputs are not permitted`; создан отдельный `backend/.env` с корректными переменными; убран root-level volume mount `./.env:/app/.env:ro` который перезаписывал env vars; `TELEGRAM_USER_RATE_LIMIT_PER_HOUR=300` подтверждён.
- **Deploy на Render**: бэкенд задеплоен на https://real-estate-parser.onrender.com (бесплатный план, может spin down при inactivity).
- **Telegram Web App**: https://gremlin654.github.io/real-estate-parser/telegram-webapp/ + бэкенд на Render (API: https://real-estate-parser.onrender.com/api/v1).

## Запуск Telegram бота

### Конфликт Polling
**Проблема:** При запуске локального бота (docker-compose) и на Render одновременно возникает ошибка:
```
TelegramConflictError: Conflict: terminated by other getUpdates request
```

**Решение:**
1. При запуске локально — отключить бота на Render:
   - Render Dashboard → kufar-backend → Settings → Environment Variables
   - `TELEGRAM_BOT_ENABLED = false`
2. При остановке локального бота — вернуть `TELEGRAM_BOT_ENABLED = true` на Render

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
- **🔥 Deal Finder** — поиск квартир ниже рынка (v3.5)
- **📉 Price Drop Tracker** — трекинг падения цены (v3.6)
- **🎯 Deal Score** — скоринг выгодности объявлений (v3.8)
- **🤖 Telegram Bot** — уведомления о новых квартирах (v4.0)

## Архитектура

```
Frontend (React + TS) ↔ Backend (FastAPI) ↔ PostgreSQL ↔ Kufar.by Scraper
```

## Технологический стек

| Компонент    | Технологии                                                                              |
| ------------ | --------------------------------------------------------------------------------------- |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS 4, Zustand, TanStack Query, shadcn/ui, recharts |
| **Backend**  | FastAPI, SQLAlchemy (async), Pydantic, APScheduler, pandas, **Redis 7**, **aiogram 3.x** |
| **Database** | PostgreSQL 16, Alembic, **Redis 7**                                                     |
| **Scraper**  | Playwright, BeautifulSoup4, aiohttp                                                     |
| **Testing**  | Playwright E2E (143), Vitest Unit (326, 66% coverage), pytest API (351, 55%), **pytest Telegram (196)** |

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

### Deal Score (v3.8) — Скоринг выгодности объявлений

```bash
GET /api/v1/deals/score?city=minsk&rooms=2&min_score=70&currency=usd&limit=20&offset=0
GET /api/v1/listings?city=minsk&include_score=true&sort_by_deal_score=true
```

**Параметры `/api/v1/deals/score`:**
- `city` (обязательно) — город для поиска
- `rooms` (опционально) — количество комнат
- `min_score` (по умолчанию 0) — минимальный Deal Score (0-100)
- `currency` (по умолчанию usd) — валюта расчётов (byn/usd)
- `limit` (по умолчанию 20) — максимум результатов (1-100)
- `offset` (по умолчанию 0) — смещение для пагинации

**Response `/api/v1/deals/score`:**
- `items` — список объявлений с Deal Score и breakdown
- `total` — общее количество объявлений
- `avg_score` — средний Deal Score
- `currency` — валюта расчётов
- `limit`, `offset` — параметры пагинации

**Deal Score Listing поля:**
- `deal_score` — общий скоринг (0-100)
- `deal_label` — текстовая метка (🔥 HOT, 👍 GOOD, 😐 NORMAL)
- `deal_score_breakdown` — детализация по 6 факторам:
  - `price_score` (вес 40%) — цена ниже рынка
  - `trend_score` (вес 20%) — динамика падения цены
  - `liquidity_score` (вес 15%) — дней на рынке
  - `freshness_score` (вес 10%) — свежесть объявления
  - `floor_score` (вес 5%) — предпочтительность этажа
  - `bonus_score` (вес 10%) — бонусы (фото, площадь)

**Deal Score Labels:**
- **50+** → 🔥 HOT (зелёный градиент)
- **35-50** → 👍 GOOD (жёлто-оранжевый градиент)
- **<35** → 😐 NORMAL (бейдж не показывается)

### Deal Finder (v3.5) — Поиск выгодных предложений

```bash
GET /api/v1/deals?city=minsk&rooms=2&discount_percent=10&currency=usd&limit=20&offset=0
GET /api/v1/deals/stats?city=minsk&rooms=2&currency=usd  # Статистика deal-предложений
GET /api/v1/listings?city=minsk&include_deal_metrics=true  # deal_percent, avg_price_per_m2
GET /api/v1/stats/summary?city=minsk  # avg_price_per_m2_byn, avg_price_per_m2_usd
```

**Параметры `/api/v1/deals`:**
- `city` (обязательно) — город для поиска
- `rooms` (опционально) — количество комнат
- `discount_percent` (по умолчанию 10) — минимальная выгода в %
- `currency` (по умолчанию usd) — валюта расчётов (byn/usd)
- `limit` (по умолчанию 20) — максимум результатов (1-100)
- `offset` (по умолчанию 0) — смещение для пагинации

**Response `/api/v1/deals`:**
- `items` — список объявлений с метриками выгоды
- `total` — общее количество найденных объявлений
- `avg_price_per_m2` — средняя цена за м² для выбранных фильтров
- `currency` — валюта расчётов
- `limit`, `offset` — параметры пагинации

**Deal Listing поля:**
- `deal_percent` — процент выгоды (отрицательное значение, например -16.5)
- `avg_price_per_m2` — средняя цена за м² по городу/комнатам
- `price_per_m2_byn`, `price_per_m2_usd` — цена за м² объявления

### Price Drop Tracker (v3.6) — Трекинг падения цены

```bash
GET /api/v1/price-drops?city=minsk&drop_percent=10&currency=usd&limit=20&offset=0
GET /api/v1/price-drops/stats?city=minsk&drop_percent=10  # Статистика падения цен
GET /api/v1/price-drops/listings/{id}/price-history?currency=usd  # История цен объявления
GET /api/v1/listings?city=minsk&include_price_drop=true  # max_price, min_price, drop_percent
```

**Параметры `/api/v1/price-drops`:**
- `city` (обязательно) — город для фильтрации
- `drop_percent` (по умолчанию 10) — минимальный процент падения (0-100)
- `currency` (по умолчанию usd) — валюта расчётов (byn/usd)
- `limit` (по умолчанию 20) — максимум результатов (1-100)
- `offset` (по умолчанию 0) — смещение для пагинации

**Response `/api/v1/price-drops`:**
- `items` — список объявлений с падением цены
- `total` — общее количество объявлений
- `avg_drop_percent` — средний процент падения
- `max_drop_percent` — максимальный процент падения
- `min_drop_percent` — минимальный процент падения
- `currency` — валюта расчётов
- `page`, `size` — параметры пагинации

**Price Drop Listing поля:**
- `max_price` — максимальная цена за историю наблюдений
- `min_price` — минимальная цена за историю наблюдений
- `drop_percent` — процент падения цены ((max - min) / max * 100)
- `current_price` — текущая цена
- `price`, `price_usd` — цена в BYN/USD для совместимости с Listing

### Favorites API (v3.7) — Избранные объявления

```bash
GET /api/v1/favorites?page=1&size=20                          # Список избранных
GET /api/v1/favorites?page=1&size=20&city=minsk               # С фильтром по городу
GET /api/v1/favorites?page=1&size=20&price_from=50000         # С фильтром по цене
GET /api/v1/favorites?page=1&size=20&rooms=1&rooms=2          # С фильтром по комнатам
GET /api/v1/favorites?page=1&size=20&sort=price_asc           # С сортировкой
POST /api/v1/favorites/{listing_id}                           # Добавить в избранное
DELETE /api/v1/favorites/{listing_id}                         # Удалить из избранного
GET /api/v1/favorites/check/{listing_id}                      # Проверить, в избранном ли
```

**Параметры GET `/api/v1/favorites`:**
- `page` (по умолчанию 1) — номер страницы
- `size` (по умолчанию 20) — размер страницы (1-100)
- `city` (опционально) — город для фильтрации
- `price_from` (опционально) — минимальная цена
- `price_to` (опционально) — максимальная цена
- `rooms` (опционально) — количество комнат (можно несколько)
- `rooms_other` (опционально) — включить 5+ комнат
- `sort` (опционально) — сортировка (`created_at_desc`, `created_at_asc`, `price_asc`, `price_desc`, `newest`, `oldest`)

**Response `/api/v1/favorites`:**
- `items` — список избранных объявлений с данными
- `total` — общее количество избранных
- `page` — текущая страница
- `size` — размер страницы

**Favorite Listing поля:**
- `id` — UUID записи в favorites
- `user_id` — UUID пользователя
- `listing_id` — UUID объявления
- `created_at` — дата добавления
- `listing` — полные данные объявления (Listing объект)

### Telegram Bot Commands (v4.0)

**Команды бота:**

```bash
/start        # Регистрация пользователя
/help         # Справка по командам
/stop         # Отписаться от уведомлений
/subscribe    # Создать подписку (FSM wizard)
/settings     # Мои подписки
/unsubscribe  # Удалить все подписки
```

**Flow подписки (/subscribe):**
1. Выбор города (inline keyboard: Минск, Могилёв, Гродно, Брест, Гомель, Витебск)
2. Выбор комнат (1, 2, 3, 4, 5+, Любые)
3. Ввод минимальной цены (BYN)
4. Ввод максимальной цены (BYN)
5. Подтверждение подписки

**Управление подписками (/settings):**
- Просмотр всех активных подписок с деталями
- Редактирование: город, комнаты, цена
- Удаление подписки inline кнопкой
- Добавление новой подписки

**Формат уведомления:**
```
🏠 Новая квартира в {city}!

📍 Адрес: {address}
🚪 Комнат: {rooms}
📐 Площадь: {area} м²
🏢 Этаж: {floor}/{total_floors}
💰 Цена: ${price_usd:,} ({price_byn:,} BYN)
📊 Цена за м²: ${price_per_m2_usd:,}

🔗 {listing.url}
```

**Inline кнопки в уведомлении:**
- 🔗 Открыть объявление (URL)
- ⚙️ Настройки (callback: settings)

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

### telegram_users (v4.0)

- `id` (UUID, PK), `telegram_id` (BigInteger, unique, index), `username`, `first_name`, `last_name`
- `language_code` (default 'ru'), `is_active`, `blocked_by_user`
- `created_at`, `updated_at`

### telegram_subscriptions (v4.0)

- `id` (UUID, PK), `user_id` (FK → telegram_users, CASCADE), `city` (index), `rooms` (Array[Integer])
- `price_min`, `price_max`, `price_per_m2_max`, `floor_min`, `floor_max`
- `currency` (default 'usd'), `notify_only_price_drop`, `exclude_deal_below_percent`
- `is_active` (index), `created_at`, `updated_at`

### telegram_notification_log (v4.0)

- `id` (UUID, PK), `user_id` (FK → telegram_users, CASCADE), `listing_id` (FK → listings, SET NULL)
- `subscription_id` (FK → telegram_subscriptions, SET NULL), `sent_at` (index)
- `status` (Enum: sent/failed/retry/blocked), `error_message`, `retry_count`, `response_message_id`

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

### v3.4 (текущая — в разработке)

**Price Per M² Analytics:**
- **✅ Новая страница** `/analytics/price-per-m2` с графиками и фильтрами
- **✅ Графики:** динамика цены за м² (LineChart), распределение по диапазонам (BarChart)
- **✅ Фильтры:** город, валюта (USD/BYN), количество комнат
- **✅ API Endpoints:** `/api/v1/stats/price-per-m2*` (summary, trends, distribution)
- **✅ Миграция БД:** `price_per_m2_byn`, `price_per_m2_usd` колонки с индексами
- **✅ E2E тесты:** 17 тестов для Price Per M² аналитики

**Исправления:**
- **🔴 Валидация сканирования** — вызывается ПЕРЕД `mark_deleted` (исправлен баг с удалением объявлений)
- **🔴 Decimal Serialization** — исправлен `TypeError: Object of type Decimal is not JSON serializable`
- **🔴 E2E тесты** — исправлено 60+ failing тестов (70%+ passing, 100+ из 144)
- **🔴 Strict Mode** — исправлены violations в E2E тестах (.first(), data-testid)

**Backend изменения:**
- `backend/app/api/v1/stats.py` — новые endpoints price-per-m2
- `backend/app/services/listing_service.py` — валидация + Decimal serialization
- `backend/app/utils/json_serializer.py` — утилиты `listing_to_dict()`, `serialize_for_snapshot()`
- `backend/app/scraper/scheduler.py` — валидация перед mark_deleted (строка 340-351)
- `backend/app/models/listing.py` — новые колонки `price_per_m2_byn`, `price_per_m2_usd`
- `backend/app/schemas/stats.py` — Pydantic schemas для аналитики

**Frontend изменения:**
- `frontend/src/pages/PricePerM2AnalyticsPage.tsx` — страница аналитики
- `frontend/src/components/stats/PricePerM2TrendChart.tsx` — график динамики
- `frontend/src/components/stats/PricePerM2DistributionChart.tsx` — график распределения
- `frontend/src/api/listings.ts` — API hooks (`usePricePerM2Stats`, `usePricePerM2Trends`, `usePricePerM2Distribution`)
- `frontend/src/shared/types/stats.ts` — TypeScript типы
- `frontend/src/widgets/AppLayout/ui/AppLayout.tsx` — ссылка в навигацию
- `frontend/tests/e2e/price-per-m2-analytics.spec.ts` — 17 E2E тестов

**Тесты:**
- **Backend:** 310 passed, 17 skipped (94.5%)
- **Frontend Unit:** 143 passed (100%)
- **Frontend E2E:** 100+ passed (70%+)
- **Coverage:** Backend 70%, Frontend 66%

**Документация:**
- `PRICE_PER_M2_FEATURE.md` — полное описание фичи
- Обновлён `QWEN.md` — контекст для AI-ассистента

**Code Review:** ✅ APPROVED (8.7/10)

**MR Status:** 🚀 Готов к созданию (коммиты в develop)

### v3.5 (текущая — в разработке)

**Deal Finder — поиск выгодных квартир:**
- **✅ Страница `/deals`** — просмотр всех выгодных предложений со статистикой
- **✅ Фильтр "Только выгодные"** — включение/выключение deal-режима на `/listings`
- **✅ DealBadge** — бейдж с процентом выгоды на карточках (🔥 -16%)
- **✅ DealTooltip** — tooltip с подробной информацией о выгоде
- **✅ API `/api/v1/deals`** — поиск квартир с ценой ниже рынка
- **✅ API `/api/v1/listings`** — параметр `include_deal_metrics` для deal_percent
- **✅ API `/api/v1/stats/summary`** — avg_price_per_m2 для расчёта выгоды

**Backend:**
- `backend/app/services/deal_finder_service.py` — сервис расчёта avg_price_per_m2 и deal_percent
- `backend/app/api/v1/deals.py` — endpoint для deal-предложений
- `backend/app/schemas/deals.py` — Pydantic schemas для Deal Finder
- `backend/app/db/migrations/versions/013_add_deal_finder_indexes.py` — 3 индекса для производительности
- **Redis кэширование** — avg_price_per_m2 (TTL 300 сек), ускорение в 10-20x
- **Валидация** — city, discount_percent (0-50%), currency
- **Пагинация** — limit/offset параметры

**Frontend:**
- `frontend/src/pages/Deals/ui/DealsPage.tsx` — страница deal-предложений
- `frontend/src/components/listing/DealBadge.tsx` — бейдж выгоды с градиентами
- `frontend/src/components/listing/DealTooltip.tsx` — tooltip с информацией о выгоде
- `frontend/src/components/filters/DealFilterToggle.tsx` — переключатель "Только выгодные"
- `frontend/src/api/listings.ts` — hooks `useDealsQuery()`, конвертация page/size → limit/offset
- `frontend/src/shared/types/stats.ts` — типы DealListing, DealsResponse
- **URL params синхронизация** — dealsOnly, discountPercent
- **Статистика** — всего предложений, средняя цена за м², лучшая выгода

**Исправления:**
- **🔴 Пагинация** — конвертация page/size в limit/offset для backend
- **🔴 Позиционирование DealBadge** — перемещён в левый угол (top-2 left-2)
- **🔴 Контрастность DealTooltip** — белый текст на тёмном фоне
- **🔴 Дублирование статистики** — изменена карточка "Лучшая выгода"
- **🔴 TypeScript типы** — DealListing совместим с Listing
- **🔴 Storybook** — исключён из компиляции (.stories файлы)
- **🔴 Вертикальный скролл** — убран в миниатюрах на странице объявления

**Тесты:**
- **Backend:** 51 тест (28 unit + 14 integration + 9 regression)
- **Frontend Unit:** 172 теста (100% pass rate)
- **Frontend E2E:** 38 тестов (deals-filter, deals-page, listing-card-deal)
- **Coverage:** Backend 93%, Frontend 66%+

**Производительность:**
- `/api/v1/deals` — ~5-10ms с Redis кэшем (10-20x быстрее)
- `/api/v1/stats/summary` — ~5-6ms с Redis кэшем (20-30x быстрее)
- **3 индекса БД** — idx_listings_city_status_price_m2 (USD/BYN), idx_listings_rooms_price_m2

**Документация:**
- Обновлён `QWEN.md` — контекст для AI-ассистента
- Добавлен раздел Deal Finder в API Endpoints

**Code Review:** ✅ Исправлены все замечания

**MR Status:** ✅ Ветка `develop` актуальна

### v4.0 (завершённая)

**Telegram Bot — уведомления о новых квартирах:**
- **🤖 aiogram 3.x** — библиотека для Telegram Bot API (polling режим)
- **✅ 3 новые таблицы БД:** `telegram_users`, `telegram_subscriptions`, `telegram_notification_log`
- **✅ Миграция 017** — создание таблиц с индексами и FK constraints
- **✅ 3 сервиса:** `TelegramSubscriptionService`, `TelegramNotificationService`, `TelegramMessageBuilder`
- **✅ Bot handlers:** `/start`, `/help`, `/stop`, `/subscribe` (FSM wizard), `/settings`, `/unsubscribe`
- **✅ Inline/Reply клавиатуры** — type-safe CallbackData через aiogram фильтры
- **✅ FSM wizard** — пошаговое создание подписки (город → комнаты → цена → подтверждение)
- **✅ Интеграция со scraper** — авто-отправка уведомлений после каждого сканирования
- **✅ Shared bot pattern** — один instance на всё приложение (предотвращает утечку)
- **✅ IDOR protection** — проверка владельца во всех callback handlers
- **✅ Retry логика** — exponential backoff (5s, 10s, 20s) с cap 60s
- **✅ Graceful shutdown** — корректная остановка бота

**Backend:**
- `backend/app/models/telegram_user.py` — модели: TelegramUser, TelegramSubscription, TelegramNotificationLog
- `backend/app/services/telegram_subscription_service.py` — CRUD подписок + matching logic (15 методов)
- `backend/app/services/telegram_validators.py` — валидация параметров подписок (94% coverage)
- `backend/app/services/telegram_exceptions.py` — 8 кастомных исключений
- `backend/app/services/telegram_notification_service.py` — отправка уведомлений с retry
- `backend/app/services/telegram_message_builder.py` — форматирование сообщений (98% coverage)
- `backend/app/telegram/bot.py` — инициализация бота и dispatcher
- `backend/app/telegram/handlers/commands.py` — /start, /help, /stop
- `backend/app/telegram/handlers/subscriptions.py` — FSM wizard + управление подписками
- `backend/app/telegram/keyboards/inline.py` — inline клавиатуры с CallbackData
- `backend/app/telegram/keyboards/reply.py` — reply клавиатуры
- `backend/app/telegram/middlewares/db_session.py` — middleware для db_session
- `backend/app/scraper/scheduler.py` — интеграция отправки уведомлений
- `backend/app/main.py` — запуск бота в lifespan
- `backend/TELEGRAM_BOT.md` — полная документация

**Тесты:**
- **Backend Telegram:** 196 тестов (100% pass rate)
  - Subscription Service: 92 теста (81% coverage)
  - Validators: 55 тестов (94% coverage)
  - Notification Service: 59 тестов (80% coverage)
  - Message Builder: 98% coverage
  - Scheduler Integration: 10 тестов
  - Bot Handlers: 29 тестов (66-100% coverage)

**Конфигурация:**
```bash
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_ENABLED=false
TELEGRAM_MAX_RETRIES=3
TELEGRAM_RETRY_DELAY_SECONDS=5
TELEGRAM_RATE_LIMIT_PER_MINUTE=20
```

**Формат уведомления:**
```
🏠 Новая квартира в Минск!

📍 Адрес: пр. Независимости, 100
🚪 Комнат: 2
📐 Площадь: 54 м²
🏢 Этаж: 5/9
💰 Цена: $42,500 (123,750 BYN)
📊 Цена за м²: $833

🔗 https://re.kufar.by/vi/minsk/kupit/kvartiru/123456
```

**Code Review:** ✅ APPROVED (7.3/10 → исправлены 4 критических issues)
- 🔴 IDOR уязвимость → owner check во всех handlers
- 🔴 Бесконечный retry → cap 60s + max retries
- 🔴 Утечка Bot instance → shared bot pattern
- 🔴 Миграция не идемпотентна → CREATE TYPE IF NOT EXISTS

**PR:** #15 (feature/telegram-bot → develop)

### v4.1 (текущая — в разработке)

**Telegram Web App (Mini App) — управление подписками через UI:**

- **✅ Frontend страница** `/telegram-webapp` — React компонент с полным CRUD подписок
- **✅ UI дизайн** — Dark Industrial / Tech Noir стиль (тёмный фон, оранжевые акценты, monospace шрифты)
- **✅ Tab навигация** — Подписки / Статистика
- **✅ API хуки** — `useTelegramSubscriptions`, `useCreateTelegramSubscription`, `useUpdateTelegramSubscription`, `useDeleteTelegramSubscription`, `useTelegramNotificationStats`
- **✅ Backend endpoints:**
  - `GET /api/v1/telegram/subscriptions` — список подписок
  - `POST /api/v1/telegram/subscriptions` — создать подписку
  - `PUT /api/v1/telegram/subscriptions/{id}` — обновить подписку
  - `DELETE /api/v1/telegram/subscriptions/{id}` — удалить подписку
  - `GET /api/v1/telegram/webapp/config` — конфиг для Web App
  - `GET /api/v1/telegram/stats` — статистика уведомлений
- **✅ Telegram WebApp утилиты** — определение окружения, инициализация, форматирование цен/комнат, Haptic Feedback
- **✅ Кнопка Web App в боте** — добавлена в reply keyboard (через `TELEGRAM_WEB_APP_URL` в config)
- **✅ Config параметр** — `TELEGRAM_WEB_APP_URL` для URL Mini App

**Frontend изменения:**
- `frontend/src/pages/TelegramWebApp/ui/TelegramWebApp.tsx` — основной компонент с tab навигацией
- `frontend/src/pages/TelegramWebApp/styles.css` — улучшенные стили (Dark Industrial aesthetic)
- `frontend/src/api/telegram.ts` — API хуки (TanStack Query)
- `frontend/src/shared/types/telegram.ts` — TypeScript типы
- `frontend/src/shared/lib/telegram-webapp.ts` — утилиты для Telegram WebApp

**Backend изменения:**
- `backend/app/api/v1/telegram_webapp.py` — API endpoints с аутентификацией через X-Telegram-User-Id header
- `backend/app/telegram/keyboards/reply.py` — кнопка Web App в main keyboard
- `backend/app/config.py` — добавлен `TELEGRAM_WEB_APP_URL`

**Дизайн:**
- Тёмный фон (#0a0a0b) с оранжевыми неоновыми акцентами (#ff6b35)
- Monospace шрифты (JetBrains Mono, SF Mono, Fira Code)
- Анимации при загрузке (stagger effects)
- Tab навигация (Подписки / Статистика)
- Статистические карточки с визуальными индикаторами
- Адаптивный дизайн для мобильных устройств
- Bottom sheet для форм редактирования

**Следующие шаги:**
1. Развертывание на публичном URL (ngrok для dev)
2. Настройка TELEGRAM_WEB_APP_URL в .env
3. Аутентификация через Telegram initData (production)
4. Синхронизация с web избранным

### v4.0.1 (текущая — в разработке)

**Исправления Telegram Bot и сканирования:**

**Адрес из Kufar API:**
- **✅ Извлечение адреса** — теперь берётся из `account_parameters` где `p == "address"` (ранее `location.geography.displayName` было пустым)
- **✅ Формат адреса** — "Т.С. Бородина ул, 14, Гомель, Гомельская область"
- **✅ Fallback** — если адрес пустой → "Не указан" в Telegram сообщении
- **✅ Адрес сохраняется в БД** — подтверждено тестированием на Гомеле

**Redis Lock cleanup:**
- **✅ Принудительное удаление lock** — если `lock.release()` не сработал (owner mismatch), вызывается `redis_client.delete(lock_key)`
- **✅ TTL уменьшен** — с 3600 сек (1 час) до 600 сек (10 минут) для авто-очистки stale lock'ов
- **✅ Double cleanup** — сначала пробуем release(), затем принудительно delete() в `finally` блоке

**Manual Scan Telegram интеграция:**
- **✅ Исправлен баг** — `_run_manual_scan` в `scan.py` теперь отправляет Telegram уведомления (ранее только `_run_scheduled_scan` в `scheduler.py`)
- **✅ Фильтрация новых объявлений** — `first_seen_at >= now - 2 минуты` чтобы не спамить старыми
- **✅ Конвертация dict → Listing** — запрос к БД по `kufar_id` для получения SQLAlchemy модели
- **✅ UnboundLocalError fixed** — `timedelta` импортирован на уровне модуля (был локальный импорт внутри функции)

**Backend изменения:**
- `backend/app/scraper/kufar_scraper.py` — извлечение адреса из `account_parameters`
- `backend/app/api/v1/scan.py` — Telegram интеграция в manual scan, lock cleanup, timedelta import
- `backend/app/services/telegram_message_builder.py` — fallback для пустого адреса ("Не указан")
- `backend/app/services/telegram_notification_service.py` — убран нерабочий фильтр `status='new'`

**Тестирование:**
- **Telegram уведомления** — 28 объявлений отправлено, все соответствуют фильтру (gomel, rooms=1)
- **Адреса в БД** — подтверждено: "Чкалова ул, 62, Гомель", "Ленина пр, 63, Гомель" и др.
- **Redis lock cleanup** — lock удаляется автоматически после завершения сканирования

**MR Status:** 🚀 Готов к созданию (ветка `feature/telegram-bot` → `develop`)

### v3.8 (текущая — в разработке)

**Deal Score — скоринг выгодности объявлений:**
- **✅ Страница `/deals/score`** — просмотр объявлений с высоким Deal Score
- **✅ DealScoreBadge** — бейдж с оценкой на карточках (🔥 85, 👍 72)
- **✅ DealScoreTooltip** — tooltip с breakdown по 6 факторам
- **✅ API `/api/v1/deals/score`** — поиск по минимальному Deal Score
- **✅ API `/api/v1/listings`** — параметры `include_score`, `sort_by_deal_score`
- **✅ 6 факторов расчёта:** price (40%), trend (20%), liquidity (15%), freshness (10%), floor (5%), bonus (10%)
- **✅ Redis кэширование** — TTL 300 сек для каждого score
- **✅ Weighted scoring** — взвешенная сумма всех факторов (0-100)
- **✅ Labels:** 🔥 HOT (50+), 👍 GOOD (35-50), 😐 NORMAL (<35)

**Backend:**
- `backend/app/services/deal_score_service.py` — сервис расчёта Deal Score (6 подкомпонентов)
- `backend/app/api/v1/deals.py` — endpoint `/api/v1/deals/score`
- `backend/app/schemas/deals.py` — Pydantic schemas (DealScoreListing, DealsScoreResponse)
- **Redis кэширование** — deal_score:{listing_id} (TTL 300 сек)
- **Валидация** — weights sum = 1.0 (допуск 0.01)
- **Breakdown структура** — score, weight, weighted для каждого фактора

**Frontend:**
- `frontend/src/pages/Deals/ui/DealsScorePage.tsx` — страница Deal Score
- `frontend/src/components/listing/DealScoreBadge.tsx` — бейдж с градиентами
- `frontend/src/components/listing/DealScoreTooltip.tsx` — tooltip с breakdown
- `frontend/src/api/listings.ts` — hooks `useDealsScoreQuery()`, конвертация page/size → limit/offset
- `frontend/src/shared/types/stats.ts` — типы DealScoreListing, DealsScoreResponse, DealScoreBreakdown
- **Интеграция в ListingCard** — DealScoreBadge при score >= 35
- **Интеграция в ListingTable** — колонка "Deal Score"
- **Сортировка** — `sort=deal_score_desc` в URL params

**Тесты:**
- **Backend:** 150+ тестов (deal_score_service + API)
- **Frontend Unit:** DealScoreBadge (12), DealScoreTooltip (7)
- **Frontend E2E:** 25 тестов (deal-score.spec.ts)
- **Coverage:** Backend ~85%, Frontend ~90%

**Производительность:**
- `/api/v1/deals/score` — ~5-10ms с Redis кэшем
- `/api/v1/listings?include_score=true` — ~10-15ms с кэшем
- **Кэш ключ:** `deal_score:{listing_id}`

**Документация:**
- Обновлён `QWEN.md` — контекст для AI-ассистента
- Добавлен раздел Deal Score в API Endpoints

**MR Status:** 🚀 Готов к созданию (ветка `develop`)

### v3.7 (текущая — в разработке)

**Favorites System — система избранных объявлений:**
- **✅ Добавление/удаление** — кнопка FavoriteButton на всех страницах (`/listings`, `/deals`, `/price-drops`, `/favorites`, `/listing/:id`)
- **✅ Синхронизация состояния** — store синхронизируется с сервером при загрузке `/favorites`
- **✅ Автоматическое обновление** — список избранных обновляется при возврате на страницу (`refetchOnMount: 'always'`)
- **✅ Кнопка на странице избранных** — можно удалять объявления прямо из карточки на `/favorites`
- **✅ Фильтры на `/favorites`** — работают фильтры по городу, цене, комнатам, сортировке
- **✅ API фильтрация** — backend поддерживает фильтры для избранных (`city`, `price_from`, `price_to`, `rooms`, `sort`)

**UI/UX улучшения:**
- **✅ Позиционирование PriceDropBadge** — перемещён в правый нижний угол карточки (`bottom-2 right-2`)
- **✅ Позиционирование FavoriteButton** — правый верхний угол (`top-2 right-2`)
- **✅ Позиционирование DealBadge** — левый верхний угол (`top-2 left-2`)
- **✅ Улучшены фильтры на `/favorites`** — использованы shadcn/ui компоненты, иконки, tooltip
- **✅ Исправлено наложение элементов** — Badge и FavoriteButton разнесены по разным позициям

**Исправления:**
- **🔴 FavoriteButton использует UUID** — исправлено с `listing.kufar_id` на `listing.id` (API требует UUID)
- **🔴 Инвалидация кэша** — добавлен `exact: false` для `invalidateQueries(['favorites'])`
- **🔴 Синхронизация store** — при загрузке `/favorites` store обновляется серверными данными
- **🔴 Миграция БД 016** — исправлен тип колонки `favorites.user_id` с `character varying` на `UUID`

**Backend изменения:**
- `backend/app/api/v1/favorites.py` — добавлены query параметры для фильтрации (city, price_from, price_to, rooms, sort)
- `backend/app/services/favorites_service.py` — реализована фильтрация и сортировка избранных
- `backend/app/db/migrations/versions/016_fix_favorites_user_id_type.py` — миграция для типа user_id

**Frontend изменения:**
- `frontend/src/api/listings.ts` — `useFavoritesQuery` поддерживает filters и options (`refetchOnMount`)
- `frontend/src/pages/Favorites/ui/FavoritesPage.tsx` — синхронизация store, refetchOnMount, кнопка на карточках
- `frontend/src/components/listing/FavoriteButton.tsx` — убрано absolute позиционирование (теперь inline-flex)
- `frontend/src/components/listing/PriceDropBadge.tsx` — позиционирование `bottom-2 right-2`
- `frontend/src/widgets/ListingCard/ui/ListingCardWidget.tsx` — обновлено позиционирование кнопок
- `frontend/src/widgets/ListingTable/ui/ListingTable.tsx` — добавлена колонка с FavoriteButton
- `frontend/src/pages/ListingDetail/ui/ListingDetail.tsx` — добавлен FavoriteButton в header
- `frontend/src/features/favorites/ui/FavoritesFilter.tsx` — улучшенный UI с shadcn/ui компонентами

**Тесты:**
- **Frontend Unit:** 261 тест (100% pass rate)
- **PriceDropBadge:** 12 тестов
- **FavoriteButton:** 14 тестов
- **FavoritesFilter:** 27 тестов

**Документация:**
- Обновлён `QWEN.md` — контекст для AI-ассистента

### v3.6 (завершённая)

**Price Drop Tracker — трекинг падения цены:**
- **✅ Страница `/price-drops`** — просмотр всех квартир с падением цены
- **✅ PriceDropBadge** — бейдж "📉 Price Drop -X%" с градиентами
- **✅ PriceDropTooltip** — tooltip с max/min/current ценами и падением
- **✅ PriceHistoryChart** — график истории цен (recharts LineChart)
- **✅ API `/api/v1/price-drops`** — список квартир с падением цены
- **✅ API `/api/v1/price-drops/stats`** — статистика падения (avg/max/min drop)
- **✅ API `/api/v1/price-drops/listings/{id}/price-history`** — история цен объявления

**Backend:**
- `backend/app/services/price_drop_service.py` — сервис расчёта drop_percent через MAX/MIN
- `backend/app/api/v1/price_drop.py` — endpoints для price drop tracker
- `backend/app/schemas/price_drop.py` — Pydantic schemas (PriceDropListing, PriceDropResponse)
- `backend/app/db/migrations/versions/014_add_price_drop_indexes.py` — 5 индексов для listing_history
- **Redis кэширование** — price_drops (TTL 300 сек), price_history (TTL 180 сек), stats (TTL 600 сек)
- **SQL агрегация** — drop_percent = ((MAX(price_before) - MIN(price_after)) / MAX(price_before)) * 100
- **Валидация** — city, drop_percent (0-100), currency

**Frontend:**
- `frontend/src/components/listing/PriceDropBadge.tsx` — бейдж с градиентами (5-10%: жёлтый, 10-20%: оранжевый, 20%+: красный)
- `frontend/src/components/listing/PriceDropTooltip.tsx` — tooltip с деталями падения
- `frontend/src/components/stats/PriceHistoryChart.tsx` — график истории цен (recharts)
- `frontend/src/pages/PriceDrops/ui/PriceDropsPage.tsx` — страница со статистикой и фильтрами
- `frontend/src/api/listings.ts` — hooks `usePriceDropQuery()`, `useListingPriceHistory()`
- `frontend/src/shared/types/stats.ts` — типы PriceDropListing, PriceDropResponse, PriceDropHistoryItem
- **Интеграция в ListingCard** — PriceDropBadge отображается при drop_percent >= 5%
- **Интеграция в ListingDetail** — PriceHistoryChart с историей цен

**Исправления:**
- **🔴 Позиционирование PriceDropBadge** — перемещён в левый угол (top-2 left-2) для избежания наложения
- **🔴 TypeScript дублирование** — удалён дублирующий export type в stats.ts
- **🔴 Backend schema** — добавлены поля price и price_usd для совместимости с Listing
- **🔴 Прогресс сканирования** — исправлена трансляция WebSocket прогресса (pages_scraped, listings_fetched)
- **🔴 Валидация сканирования** — изменён порог с 90% на 50% для гибкости
- **🔴 ListingCardWidget** — защита от undefined price (displayPrice = price ?? 0)
- **🔴 Black formatting** — отформатировано 5 файлов для CI

**Тесты:**
- **Backend:** 50 тестов (27 unit + 23 integration)
- **Frontend Unit:** 196 тестов (PriceDropBadge: 12, PriceDropTooltip: 7, PriceHistoryChart: 5)
- **Frontend E2E:** 20 тестов (price-drop-tracker.spec.ts)
- **Coverage:** Backend 84%, Frontend 86%

**Производительность:**
- `/api/v1/price-drops` — ~5-10ms с Redis кэшем
- `/api/v1/price-drops/stats` — ~5-8ms с Redis кэшем
- **5 индексов БД** — idx_listing_history_listing_event, idx_listing_history_created_at, и другие

**Документация:**
- Обновлён `QWEN.md` — контекст для AI-ассистента
- Добавлен раздел Price Drop Tracker в API Endpoints

**Code Review:** ✅ Исправлены все замечания

**MR Status:** ✅ Ветка `develop` актуальна

### v3.3

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
    │ ✅ P0     │ 🤖 Telegram Bot (MVP)                     │ Medium    │ Мгновенные уведомления о новых квартирах    │
    │ ✅ P0     │ ⭐ Избранные объявления (v3.7)            │ Low       │ Быстрый доступ к выбранным вариантам        │
    │ P1        │ 🔍 Расширенные фильтры (цена за м², этаж) │ Medium    │ Точный поиск по параметрам                  │
    │ P1        │ 📄 Детальная страница объявления          │ Medium    │ История изменений, графики цены             │
    │ P2        │ ⚖️ Сравнение объявлений                   │ High      │ Наглядное сравнение характеристик           │
