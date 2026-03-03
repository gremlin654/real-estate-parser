# План разработки мониторинга объявлений Kufar.by

## Архитектура системы

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React + TS    │────▶│   FastAPI (Py)   │────▶│   PostgreSQL    │
│   Frontend      │     │   Backend + API  │     │   Database      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                         ┌──────▼───────┐
                         │  Scheduler   │
                         │ (APScheduler │
                         │  / Celery)   │
                         └──────────────┘
```

---

## Стек технологий

| Слой | Технологии |
|------|-----------|
| **Frontend** | React, TypeScript, Vite, TanStack Query, Zustand, Tailwind CSS, Recharts |
| **Backend** | FastAPI, SQLAlchemy 2.0, Alembic, APScheduler / Celery + Redis |
| **Парсинг** | httpx, BeautifulSoup / Playwright |
| **База данных** | PostgreSQL |
| **Инфраструктура** | Docker Compose |

---

## Структура базы данных

### Таблица `listings` — актуальное состояние

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Primary Key |
| `kufar_id` | VARCHAR | Уникальный ID с Kufar |
| `url` | TEXT | Ссылка на объявление |
| `title` | TEXT | Заголовок |
| `price` | INTEGER | Текущая цена (USD) |
| `currency` | VARCHAR | Валюта |
| `address` | TEXT | Адрес |
| `rooms` | INTEGER | Кол-во комнат |
| `area` | FLOAT | Площадь м² |
| `floor` | INTEGER | Этаж |
| `category` | VARCHAR | Квартиры / дома / земля |
| `images` | JSONB | Массив URL фотографий |
| `raw_data` | JSONB | Полный снапшот ответа API |
| `status` | ENUM | `active` / `deleted` / `archived` |
| `first_seen_at` | TIMESTAMP | Когда впервые увидели |
| `last_seen_at` | TIMESTAMP | Последняя успешная проверка |
| `deleted_at` | TIMESTAMP | Когда объявление исчезло |

### Таблица `listing_history` — история изменений

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Primary Key |
| `listing_id` | UUID | FK → listings |
| `event_type` | ENUM | `created` / `price_changed` / `edited` / `deleted` / `restored` |
| `price_before` | INTEGER | Цена до изменения |
| `price_after` | INTEGER | Цена после изменения |
| `changed_fields` | JSONB | `{"title": ["было", "стало"], "area": [45, 47]}` |
| `snapshot` | JSONB | Полный снапшот объявления на момент события |
| `created_at` | TIMESTAMP | Время фиксации события |

---

## Backend — структура проекта

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── listings.py       # CRUD + фильтрация
│   │       ├── history.py        # История изменений
│   │       └── stats.py          # Статистика для дашборда
│   ├── scraper/
│   │   ├── kufar_client.py       # HTTP-клиент к Kufar API
│   │   ├── parser.py             # Парсинг и маппинг данных
│   │   └── scheduler.py          # Задачи APScheduler
│   ├── services/
│   │   └── listing_service.py    # Бизнес-логика: diff, upsert
│   ├── models/                   # SQLAlchemy модели
│   ├── schemas/                  # Pydantic схемы
│   └── db/
│       └── migrations/           # Alembic миграции
├── Dockerfile
└── requirements.txt
```

### Ключевая логика — `listing_service.py`

```python
async def upsert_listing(new_data: dict):
    existing = await get_by_kufar_id(new_data["kufar_id"])

    if not existing:
        # Создать запись + событие created
        await create_listing(new_data)
        await add_event(listing_id, event_type="created", snapshot=new_data)
    else:
        diff = compute_diff(existing, new_data)

        if diff.price_changed:
            await add_event(
                listing_id,
                event_type="price_changed",
                price_before=diff.price_before,
                price_after=diff.price_after,
            )

        if diff.fields_changed:
            await add_event(
                listing_id,
                event_type="edited",
                changed_fields=diff.fields,
            )

        await update_listing(existing.id, new_data)  # обновить last_seen_at


async def mark_deleted(active_kufar_ids: set[str]):
    # Все активные объявления, которых нет в текущем скане → удалены
    missing = await get_active_not_in(active_kufar_ids)
    for listing in missing:
        await set_status(listing.id, "deleted")
        await add_event(listing.id, event_type="deleted")
```

---

## Парсинг Kufar

Kufar имеет **внутренний JSON API** — браузер не нужен для листинга:

```
GET https://cre.kufar.by/v1/search/rendered-paginated
    ?category=1010    # недвижимость
    &cur=USD
    &lang=ru
    &size=30
    &cursor=...       # токен пагинации
```

Используем **httpx** (async) — быстро и без Selenium. Для детальной страницы конкретного объявления при необходимости — BeautifulSoup.

```python
async def fetch_all_listings() -> list[dict]:
    results = []
    cursor = None
    async with httpx.AsyncClient() as client:
        while True:
            params = {"category": "1010", "cur": "USD", "lang": "ru", "size": 30}
            if cursor:
                params["cursor"] = cursor
            resp = await client.get(BASE_URL, params=params)
            data = resp.json()
            results.extend(data["ads"])
            cursor = data.get("pagination", {}).get("next_cursor")
            if not cursor:
                break
    return results
```

---

## Frontend — структура проекта

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx         # Сводка: новые / удалённые / изменения цен
│   │   ├── Listings.tsx          # Таблица объявлений с фильтрами
│   │   └── ListingDetail.tsx     # Карточка + таймлайн событий
│   ├── components/
│   │   ├── PriceChart.tsx        # График цены во времени (Recharts)
│   │   ├── EventTimeline.tsx     # Вертикальная лента событий
│   │   ├── FilterPanel.tsx       # Фильтры: цена, статус, категория
│   │   └── StatusBadge.tsx       # Бейдж: active / deleted / changed
│   ├── api/                      # TanStack Query хуки
│   └── store/                    # Zustand (фильтры, состояние UI)
├── Dockerfile
└── vite.config.ts
```

### Ключевые экраны

**Dashboard** — плитки с метриками: `+N новых сегодня`, `N удалено`, `N подешевело ↓`, `N подорожало ↑`. Под ними — таблица последних событий по всем объявлениям.

**Listings** — таблица с пагинацией и фильтрами по категории, цене (от/до), статусу, дате. Строки с понижением цены подсвечиваются зелёным, с повышением — красным.

**Detail** — карточка объявления (фото, параметры, ссылка) + вертикальный таймлайн всех событий с диффом изменившихся полей + график цены во времени.

---

## Docker Compose

```yaml
version: "3.9"

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: kufar_monitor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    depends_on: [db]
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:secret@db/kufar_monitor
      SCAN_INTERVAL_MINUTES: 30
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on: [backend]
    ports:
      - "3000:3000"

volumes:
  pgdata:
```

---

## API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/api/v1/listings` | Список объявлений с фильтрами |
| `GET` | `/api/v1/listings/{id}` | Детали объявления |
| `GET` | `/api/v1/listings/{id}/history` | История изменений объявления |
| `GET` | `/api/v1/stats/summary` | Сводка для дашборда |
| `GET` | `/api/v1/stats/price-chart/{id}` | Данные для графика цены |
| `POST` | `/api/v1/scan/trigger` | Запустить скан вручную |

---

## Этапы разработки

### Этап 1 — Инфраструктура (1–2 дня)
- Docker Compose: PostgreSQL + Backend + Frontend
- Alembic: начальная миграция (таблицы `listings`, `listing_history`)
- Базовый FastAPI с health-check эндпоинтом

### Этап 2 — Скрапер (2–3 дня)
- Kufar API клиент с поддержкой пагинации
- Маппинг полей ответа → модель БД
- Логика `upsert` + `compute_diff`
- APScheduler: задача по расписанию (каждые 30–60 мин)
- Логирование и обработка ошибок

### Этап 3 — REST API (1–2 дня)
- Эндпоинты листингов с фильтрацией и пагинацией
- Эндпоинты истории изменений
- Эндпоинты статистики для дашборда

### Этап 4 — Frontend (3–4 дня)
- Dashboard с метриками
- Таблица объявлений с фильтрами
- Детальная страница: карточка + таймлайн + график цен
- TanStack Query для кеширования запросов

### Этап 5 — Полировка и деплой
- Telegram-бот для уведомлений о новых / удалённых / подешевевших
- Экспорт в CSV
- Nginx reverse proxy
- Деплой на VPS / облако

---

## Возможные расширения

- **Фильтры по районам** — парсинг географических меток
- **Сравнение объявлений** — side-by-side два объявления
- **Избранное** — сохранять интересные объявления
- **Telegram-уведомления** — настраиваемые алерты по критериям (цена < X, район Y)
- **Аналитика рынка** — средняя цена по районам, динамика за период
