# Kufar Monitor — Быстрый старт новых функций

## 🚀 Установка и запуск

### 1. Обновите зависимости

```bash
# Backend
cd backend
pip install pandas==2.2.0 openpyxl==3.1.2

# Frontend (уже установлено)
cd frontend
npm install
```

### 2. Запустите проект

```bash
# Из корня проекта
docker-compose up --build
```

### 3. Проверьте новые функции

#### Экспорт данных
1. Откройте http://localhost:3000/listings
2. Примените фильтры (город, цена, комнаты)
3. Нажмите кнопку **"Экспорт"** рядом с "Сканировать"
4. Выберите формат: CSV, XLSX или JSON
5. Файл автоматически загрузится

#### Графики на Dashboard
1. Откройте http://localhost:3000/dashboard
2. Выберите город в селекторе
3. Просмотрите 3 графика:
   - **Динамика цен** (2-комн, 12 месяцев)
   - **Распределение по комнатам**
   - **Активность по дням** (30 дней)

---

## 📋 API Endpoints

### Экспорт

```bash
# Экспорт объявлений (CSV)
curl -O -J "http://localhost:8000/api/v1/export/listings?format=csv&city=minsk"

# Экспорт объявлений (XLSX)
curl -O -J "http://localhost:8000/api/v1/export/listings?format=xlsx&price_from=50000&price_to=150000"

# Экспорт сводки (JSON)
curl "http://localhost:8000/api/v1/export/summary?format=json"
```

### Статистика

```bash
# Динамика цен
curl "http://localhost:8000/api/v1/stats/price-trends?city=minsk&rooms=2&period_months=12"

# Распределение по комнатам
curl "http://localhost:8000/api/v1/stats/room-distribution?city=minsk"

# Ежедневная активность
curl "http://localhost:8000/api/v1/stats/daily-activity?city=minsk&period_days=30"

# Сравнение городов
curl "http://localhost:8000/api/v1/stats/city-comparison"
```

---

## 🧪 Тестирование

### Backend тесты

```bash
cd backend

# Тесты экспорта
python -m pytest tests/test_export.py -v

# Тесты статистики
python -m pytest tests/test_stats.py -v

# Все тесты с coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### Frontend тесты

```bash
cd frontend

# Unit тесты
npm run test:unit

# E2E тесты
npm run test:e2e:chromium

# Все тесты с coverage
npm run coverage
```

---

## 🔧 CI/CD Настройка

### 1. GitHub Actions

Автоматически запускается при:
- Push в ветки `main` или `develop`
- Pull Request в `main`

**Этапы:**
1. ✅ Lint Backend (flake8, black, mypy)
2. ✅ Test Backend (pytest + coverage)
3. ✅ Lint Frontend (ESLint, TypeScript)
4. ✅ Test Frontend Unit (Vitest + coverage)
5. ✅ Test Frontend E2E (Playwright)
6. ✅ Build Frontend (Vite)
7. ✅ Build Backend (импорты)

### 2. Codecov

Для включения Codecov:

1. Зарегистрируйтесь на [codecov.io](https://codecov.io)
2. Добавьте репозиторий
3. GitHub будет автоматически загружать отчёты

**Проверка локально:**
```bash
# Backend
cd backend
python -m pytest tests/ --cov=app --cov-report=xml

# Frontend
cd frontend
npm run test:unit:coverage
```

---

## 📊 Структура изменений

```
web/
├── backend/
│   ├── app/
│   │   └── api/v1/
│   │       ├── export.py        # Новый: Export endpoints
│   │       └── stats.py         # Обновлён: Stats endpoints
│   └── tests/
│       ├── test_export.py       # Новый: Export tests (11 тестов)
│       └── test_stats.py        # Обновлён: Stats tests (18 тестов)
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── listings.ts      # Обновлён: Export + Stats hooks
│   │   └── pages/
│   │       ├── Dashboard.tsx    # Обновлён: 3 графика
│   │       └── Listings.tsx     # Обновлён: Кнопка экспорта
│   └── package.json             # Зависимости (recharts уже есть)
│
├── .github/
│   └── workflows/
│       └── ci.yml               # Новый: CI/CD pipeline
│
├── codecov.yml                  # Новый: Codecov конфигурация
├── NEW_FEATURES.md              # Новый: Документация функций
├── CHANGELOG_2.0.md             # Новый: Changelog
└── QUICKSTART.md                # Новый: Этот файл
```

---

## 🐛 Troubleshooting

### Экспорт не работает

**Ошибка:** `ModuleNotFoundError: No module named 'pandas'`

**Решение:**
```bash
cd backend
pip install pandas==2.2.0 openpyxl==3.1.2
docker-compose restart backend
```

### Графики не отображаются

**Причина 1:** Нет данных в базе  
**Решение:** Запустите сканирование

**Причина 2:** Ошибка в консоли  
**Решение:** Проверьте DevTools → Console

### CI/CD не запускается

**Причина:** Неправильная ветка  
**Решение:** Workflow настроен только для `main` и `develop`

**Причина:** Ошибка в YAML  
**Решение:** Проверьте `.github/workflows/ci.yml` через YAML линтер

---

## 📈 Метрики

### Текущее покрытие
- Backend: ~29% → цель 40%
- Frontend Unit: ~1% → цель 40%
- Frontend E2E: 19 тестов

### Новые тесты
- Export API: 11 тестов
- Stats API: 18 тестов
- **Всего:** 29 новых тестов

---

## 🎯 Следующие шаги

1. **Настройте CI/CD**
   - Добавьте репозиторий на GitHub
   - Включите Codecov

2. **Запустите тесты**
   - Убедитесь, что все тесты проходят
   - Проверьте coverage отчёты

3. **Протестируйте функции**
   - Экспорт в разных форматах
   - Графики для разных городов
   - Фильтрацию данных

4. **Задокументируйте для команды**
   - Поделитесь `NEW_FEATURES.md`
   - Проведите демо новых функций

---

## 📞 Поддержка

- **Документация:** `NEW_FEATURES.md`
- **Changelog:** `CHANGELOG_2.0.md`
- **API Docs:** http://localhost:8000/docs

---

**Версия:** 2.0.0  
**Дата:** 2026-03-03  
**Статус:** ✅ Готово к использованию
