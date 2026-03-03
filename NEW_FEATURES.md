# Kufar Monitor — Новые функции

## 📤 Экспорт данных (Export)

### Backend API

#### Экспорт объявлений
```
GET /api/v1/export/listings?format=csv&city=minsk&status=active&price_from=50000&price_to=150000&rooms=1&rooms=2
```

**Параметры:**
- `format` — формат экспорта: `csv`, `xlsx`, `json` (по умолчанию: csv)
- `city` — фильтр по городу
- `status` — фильтр по статусу
- `price_from` — минимальная цена
- `price_to` — максимальная цена
- `rooms` — количество комнат (можно указать несколько)

**Пример ответа (CSV):**
```csv
id,kufar_id,title,price_byn,price_usd,currency,city,address,rooms,area,floor,url,status,first_seen_at,last_seen_at
uuid,12345,2-комн квартира,125000,38000,BYN,minsk,пр. Независимости,2,54.5,3/9,https://...,active,2026-03-01,2026-03-03
```

#### Экспорт сводки
```
GET /api/v1/export/summary?format=xlsx
```

**Форматы:**
- CSV — Excel CSV с UTF-8 кодировкой
- XLSX — Excel файл с авто-шириной колонок
- JSON — JSON массив объектов

### Frontend UI

**Кнопка "Экспорт"** находится на странице **Listings** рядом с кнопкой "Сканировать".

**Использование:**
1. Нажмите кнопку "Экспорт"
2. Выберите формат: CSV, XLSX или JSON
3. Файл автоматически загрузится с применёнными фильтрами

**Применяемые фильтры:**
- Город
- Статус
- Диапазон цен
- Количество комнат

---

## 📊 Графики на Dashboard

### 1. Динамика цен (Line Chart)

**Endpoint:** `GET /api/v1/stats/price-trends?city=minsk&rooms=2&period_months=12`

**Описание:**
- Показывает среднюю цену в USD по месяцам
- Данные для 2-комнатных квартир
- Период: 12 месяцев
- Использует цену из snapshot события "created" для исторической точности

**Визуализация:**
- Линейный график (Recharts LineChart)
- Ось X: месяцы (1-12)
- Ось Y: цена в USD (формат $Xk)
- Tooltip с детальной информацией

### 2. Распределение по комнатам (Pie Chart)

**Endpoint:** `GET /api/v1/stats/room-distribution?city=minsk`

**Описание:**
- Показывает распределение квартир по количеству комнат
- Только активные объявления
- Группы: 1, 2, 3, 4 комнаты

**Визуализация:**
- Круговая диаграмма (Recharts PieChart)
- Цвета: синий, зелёный, жёлтый, красный
- Подписи: "X комн: YY%"
- Tooltip с количеством и процентом

**Пример ответа:**
```json
{
  "city": "minsk",
  "data": [
    {"rooms": 1, "count": 150, "percentage": 25.0, "avg_price_usd": 35000},
    {"rooms": 2, "count": 300, "percentage": 50.0, "avg_price_usd": 45000},
    {"rooms": 3, "count": 120, "percentage": 20.0, "avg_price_usd": 60000},
    {"rooms": 4, "count": 30, "percentage": 5.0, "avg_price_usd": 80000}
  ]
}
```

### 3. Активность по дням (Bar Chart)

**Endpoint:** `GET /api/v1/stats/daily-activity?city=minsk&period_days=30`

**Описание:**
- Показывает ежедневную активность
- Три метрики: новые, удалённые, изменения цены
- Период: 30 дней

**Визуализация:**
- Столбчатая диаграмма (Recharts BarChart)
- Цвета:
  - Зелёный: новые объявления
  - Красный: удалённые объявления
  - Жёлтый: изменения цены
- Tooltip с детализацией по каждому дню

**Пример ответа:**
```json
{
  "city": "minsk",
  "period_days": 30,
  "data": [
    {"date": "2026-02-01", "new_listings": 15, "deleted_listings": 8, "price_changes": 5},
    {"date": "2026-02-02", "new_listings": 22, "deleted_listings": 12, "price_changes": 10}
  ]
}
```

---

## 🔧 CI/CD Pipeline

### GitHub Actions Workflow

**Файл:** `.github/workflows/ci.yml`

### Этапы pipeline:

#### 1. Lint Backend
- Проверка flake8 (ошибки и стиль)
- Проверка black (форматирование)
- Проверка mypy (типы)

#### 2. Test Backend
- Запуск pytest тестов
- Покрытие кода (coverage)
- Загрузка отчёта в Codecov
- Артефакт: HTML отчёт coverage

#### 3. Lint Frontend
- ESLint проверка
- TypeScript проверка типов

#### 4. Test Frontend Unit
- Vitest unit тесты
- Покрытие кода
- Загрузка отчёта в Codecov

#### 5. Test Frontend E2E
- Playwright E2E тесты
- Chromium браузер
- Артефакт: HTML отчёт тестов

#### 6. Build Frontend
- Production сборка Vite
- Артефакт: dist/ папка

#### 7. Build Backend
- Проверка импортов
- Валидация сборки

### Codecov интеграция

**Файл:** `codecov.yml`

**Настройки:**
- Target coverage: 40% (project), 60% (patch)
- Флаги: backend, frontend-unit
- Игнорируемые пути: тесты

### Запуск локально

```bash
# Backend тесты
cd backend
python -m pytest tests/ --cov=app

# Frontend тесты
cd frontend
npm run test:unit:coverage
npm run test:e2e:coverage
```

---

## 📋 API Endpoints Summary

### Stats Endpoints

| Endpoint | Описание |
|----------|----------|
| `GET /api/v1/stats/summary` | Сводная статистика по городу |
| `GET /api/v1/stats/price-trends` | Динамика цен по месяцам |
| `GET /api/v1/stats/room-distribution` | Распределение по комнатам |
| `GET /api/v1/stats/daily-activity` | Ежедневная активность |
| `GET /api/v1/stats/city-comparison` | Сравнение городов |

### Export Endpoints

| Endpoint | Описание |
|----------|----------|
| `GET /api/v1/export/listings` | Экспорт объявлений (CSV/XLSX/JSON) |
| `GET /api/v1/export/summary` | Экспорт сводки (CSV/XLSX/JSON) |

---

## 🎨 Компоненты Dashboard

### Новые зависимости
- `recharts` — библиотека графиков (уже установлена)

### Компоненты
- **LineChart** — динамика цен
- **PieChart** — распределение по комнатам
- **BarChart** — активность по дням

### Темная тема
Все графики используют тёмную цветовую схему:
- Фон tooltip: `#1F2937`
- Граница: `#374151`
- Текст: `#F9FAFB`
- Сетка: `#374151`

---

## 🚀 Использование

### 1. Экспорт данных

**Через UI:**
1. Откройте страницу "Объявления"
2. Примените фильтры (город, цена, комнаты)
3. Нажмите "Экспорт" → выберите формат
4. Файл загрузится автоматически

**Через API:**
```bash
# CSV экспорт всех активных объявлений Минска
curl -O -J "http://localhost:8000/api/v1/export/listings?format=csv&city=minsk&status=active"

# XLSX экспорт с фильтром по цене
curl -O -J "http://localhost:8000/api/v1/export/listings?format=xlsx&price_from=50000&price_to=150000"
```

### 2. Просмотр графиков

1. Откройте Dashboard
2. Выберите город в селекторе
3. Графики автоматически обновятся

**Примечание:** Для отображения графиков необходимы данные в базе. Если данных нет, покажутся заглушки.

### 3. CI/CD

**Настройка:**
1. Создайте репозиторий на GitHub
2. Запушьте код
3. Workflow запустится автоматически при push/PR

**Codecov:**
1. Зарегистрируйтесь на [codecov.io](https://codecov.io)
2. Добавьте репозиторий
3. GitHub автоматически будет загружать отчёты

---

## 📊 Метрики качества

### Цели по покрытию
- Backend: 40%+ (текущее: ~29%)
- Frontend Unit: 40%+ (текущее: ~1%)
- Frontend E2E: 19 тестов

### Проверка в CI
-Lint: обязательно
- Тесты: обязательно
- Coverage: warning (не блокирует)

---

## 🔮 Планы развития

### Следующие улучшения:
1. **Уведомления** — Telegram, email алерты
2. **Избранные объявления** — сохранение в закладки
3. **Сравнение объявлений** — side-by-side сравнение
4. **Machine Learning** — оценка справедливой цены
5. **PWA** — мобильное приложение

---

## 📝 Troubleshooting

### Экспорт не работает
```bash
# Проверьте установку зависимостей
cd backend
pip install pandas openpyxl

# Проверьте API
curl http://localhost:8000/api/v1/export/listings?format=csv
```

### Графики не отображаются
```bash
# Проверьте наличие данных
curl http://localhost:8000/api/v1/stats/room-distribution?city=minsk

# Проверьте frontend логи
# Откройте DevTools → Console
```

### CI не запускается
- Проверьте `.github/workflows/ci.yml`
- Убедитесь, что ветка `main` или `develop`
- Проверьте секреты репозитория (для Codecov)
