# Real Estate Parser — Система мониторинга недвижимости Kufar.by

Автоматизированная система для отслеживания объявлений о продаже недвижимости на портале [Kufar.by](https://re.kufar.by).

[![CI/CD](https://github.com/gremlin654/real-estate-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/gremlin654/real-estate-parser/actions/workflows/ci.yml)

## 🚀 Быстрый старт

```bash
# Клонирование
git clone https://github.com/gremlin654/real-estate-parser.git
cd real-estate-parser

# Запуск
docker-compose up --build
```

## 📋 Возможности

- ✅ Автоматическое сканирование объявлений
- ✅ Отслеживание изменений цен (BYN и USD)
- ✅ История сканирований
- ✅ Экспорт данных (CSV, XLSX, JSON)
- ✅ Графики и аналитика
- ✅ CI/CD pipeline
- ✅ Тесты (E2E + Unit + API)
- ✅ Redis integration (кэширование, distributed locking, rate limiting)

## 🔗 Доступ к сервисам

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## 🛠 Технологии

### Frontend
- React 19, TypeScript, Vite
- TailwindCSS, shadcn/ui
- TanStack Query, Zustand
- Playwright (E2E), Vitest (Unit)

### Backend
- FastAPI, SQLAlchemy, PostgreSQL
- Alembic (миграции)
- Pytest (API тесты)
- APScheduler (планировщик)
- Redis (кэширование, distributed locking, rate limiting)

### Infrastructure
- Docker, Docker Compose
- GitHub Actions (CI/CD)
- Redis

## 📖 Использование

### 1. Запуск проекта

```bash
docker-compose up --build
```

### 2. Откройте веб-интерфейс

Перейдите на http://localhost:3000

### 3. Выберите город

На странице Dashboard или Listings выберите город из списка:
- Минск
- Могилёв
- Гродно
- Брест
- Гомель
- Витебск

### 4. Запустите сканирование

Нажмите кнопку **"🔄 Сканировать"** на странице Listings

## 📊 API Endpoints

### Health Check
```bash
GET /health
```

### Listings
```bash
GET /api/v1/listings?page=1&size=20&city=minsk
GET /api/v1/listings/{id}
GET /api/v1/history/{id}
```

### Stats
```bash
GET /api/v1/stats/summary?city=minsk
GET /api/v1/stats/price-trends?city=minsk&rooms=2
GET /api/v1/stats/room-distribution?city=minsk
```

### Export
```bash
GET /api/v1/export/listings?format=csv&city=minsk
GET /api/v1/export/listings?format=json
GET /api/v1/export/summary?format=xlsx
```

### Scan Management
```bash
POST /api/v1/scan/trigger
GET /api/v1/scan/progress
GET /api/v1/scan/schedule
PUT /api/v1/scan/schedule
```

### Monitoring
```bash
GET /monitoring/redis
GET /monitoring/redis/keys?pattern=cache:*
GET /monitoring/redis/slowlog
```

## 🧪 Тестирование

### Backend
```bash
cd backend
pip install -r requirements-test.txt
python -m pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm install
npm run test:e2e        # E2E тесты
npm run test:unit       # Unit тесты
npm run coverage        # Все тесты с coverage
```

## 📁 Структура проекта

```
real-estate-parser/
├── backend/
│   ├── app/
│   │   ├── api/v1/       # API endpoints
│   │   ├── db/           # Database config
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── scraper/      # Scraper logic
│   │   └── services/     # Business logic
│   ├── tests/            # Pytest tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/          # API hooks
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   └── store/        # Zustand store
│   ├── tests/            # Playwright tests
│   └── package.json
├── docker-compose.yml
└── README.md
```

## ⚙️ Настройка

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Backend
DATABASE_URL=postgresql+asyncpg://postgres:secret@db/kufar_monitor
KUFAR_CITY=mogilev

# Database
POSTGRES_DB=kufar_monitor
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
```

## 🔴 Redis Integration

Проект использует Redis для кэширования, distributed locking, state management и rate limiting.

### Архитектура

```
Frontend ↔ Backend (FastAPI) ↔ Redis
                          ↓
                      PostgreSQL
```

### Компоненты

| Компонент | Описание | TTL |
|-----------|----------|-----|
| **Кэширование API** | Stats и Listings endpoints | 30-300 сек |
| **Distributed Lock** | Блокировка сканирования городов | 3600 сек |
| **WebSocket State** | Прогресс сканирования (Hash + Pub/Sub) | 7200 сек |
| **Rate Limiting** | Token Bucket для scraper | 3600 сек |

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

# Статистика
docker-compose exec redis redis-cli INFO stats
```

### Конфигурация

| Переменная | Значение | Описание |
|------------|----------|----------|
| `REDIS_URL` | `redis://redis:6379/0` | Production БД |
| `REDIS_TEST_URL` | `redis://redis:6379/1` | Test БД |
| `CACHE_TTL_STATS_SUMMARY` | 60 | Кэш сводной статистики |
| `CACHE_TTL_STATS_OTHER` | 300 | Кэш остальной статистики |
| `CACHE_TTL_LISTINGS` | 30 | Кэш объявлений |
| `SCAN_LOCK_TIMEOUT` | 3600 | Блокировка сканирования |
| `RATE_LIMIT_CAPACITY` | 10 | Burst запросов |
| `RATE_LIMIT_REFILL_RATE` | 10.0 | Токенов/секунду |

### Мониторинг

```bash
# Health check
curl http://localhost:8000/monitoring/redis

# Список ключей
curl "http://localhost:8000/monitoring/redis/keys?pattern=cache:*"

# Slowlog
curl "http://localhost:8000/monitoring/redis/slowlog"
```

### Документация

- [Redis Keys Reference](docs/REDIS_KEYS.md) — полная документация ключей
- [Redis Dashboard](docs/REDIS_DASHBOARD.md) — мониторинг и метрики

## 📝 Лицензия

MIT

## 👨‍💻 Автор

Andrey Sidelnikov (@gremlin654)
