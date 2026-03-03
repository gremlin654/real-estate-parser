# Kufar Monitor — Changelog

## Версия 2.0.0 (2026-03-03)

### 🎉 Новые функции

#### 1. Экспорт данных (Export)

**Backend:**
- ✅ `GET /api/v1/export/listings` — экспорт объявлений в CSV, XLSX, JSON
- ✅ `GET /api/v1/export/summary` — экспорт сводной статистики
- ✅ Фильтрация: город, статус, цена, комнаты
- ✅ Авто-генерация имён файлов с timestamp
- ✅ XLSX с авто-шириной колонок
- ✅ CSV с UTF-8 кодировкой для Excel

**Frontend:**
- ✅ Кнопка "Экспорт" на странице Listings
- ✅ Выпадающее меню с выбором формата
- ✅ Применение текущих фильтров при экспорте
- ✅ Индикатор загрузки при экспорте

**Файлы:**
- `backend/app/api/v1/export.py` — новый API router
- `frontend/src/api/listings.ts` — `downloadExport()`, `downloadSummaryExport()`
- `frontend/src/pages/Listings.tsx` — кнопка экспорта

---

#### 2. Графики на Dashboard

**Backend API:**
- ✅ `GET /api/v1/stats/price-trends` — динамика цен по месяцам
- ✅ `GET /api/v1/stats/room-distribution` — распределение по комнатам
- ✅ `GET /api/v1/stats/daily-activity` — ежедневная активность
- ✅ `GET /api/v1/stats/city-comparison` — сравнение городов

**Frontend:**
- ✅ **Line Chart** — динамика цен (2-комн, 12 месяцев)
- ✅ **Pie Chart** — распределение по комнатам (1-4)
- ✅ **Bar Chart** — активность по дням (30 дней)
- ✅ Тёмная тема для всех графиков
- ✅ Responsive дизайн
- ✅ Tooltip с детальной информацией
- ✅ Заглушки при отсутствии данных

**Файлы:**
- `backend/app/api/v1/stats.py` — новые endpoints
- `frontend/src/api/listings.ts` — `useRoomDistribution`, `useDailyActivity`, `usePriceTrends`
- `frontend/src/pages/Dashboard.tsx` — 3 новых секции с графиками

---

#### 3. CI/CD Pipeline

**GitHub Actions:**
- ✅ `.github/workflows/ci.yml` — полный pipeline
- ✅ **Lint Backend** — flake8, black, mypy
- ✅ **Test Backend** — pytest с coverage
- ✅ **Lint Frontend** — ESLint, TypeScript
- ✅ **Test Frontend Unit** — Vitest с coverage
- ✅ **Test Frontend E2E** — Playwright
- ✅ **Build Frontend** — Vite production сборка
- ✅ **Build Backend** — валидация импортов
- ✅ **Codecov** — загрузка отчётов о покрытии

**Codecov:**
- ✅ `codecov.yml` — конфигурация
- ✅ Target: 40% (project), 60% (patch)
- ✅ Флаги: backend, frontend-unit
- ✅ Игнорирование тестовых файлов

---

### 📦 Зависимости

**Backend:**
```txt
pandas==2.2.0
openpyxl==3.1.2
```

**Frontend:**
- Уже установлены: `recharts` (используется для графиков)

---

### 🧪 Тесты

**Backend:**
- ✅ `backend/tests/test_export.py` — 11 тестов
- ✅ `backend/tests/test_stats.py` — 18 тестов (обновлён)

**Запуск:**
```bash
cd backend
python -m pytest tests/test_export.py -v
python -m pytest tests/test_stats.py -v
```

---

### 📚 Документация

- ✅ `NEW_FEATURES.md` — описание новых функций
- ✅ `CHANGELOG_2.0.md` — этот файл
- ✅ `.github/workflows/ci.yml` — CI/CD документация

---

### 🔄 Breaking Changes

**Нет** — все изменения обратно совместимы.

---

### 🐛 Исправления

- Нет (эта версия фокусируется на новых функциях)

---

## Миграция

### Backend

```bash
cd backend

# Установить новые зависимости
pip install pandas==2.2.0 openpyxl==3.1.2

# Перезапустить backend
docker-compose restart backend
```

### Frontend

```bash
cd frontend

# Перезапустить dev сервер
npm run dev
```

### Проверка

1. **Экспорт:**
   - Откройте http://localhost:3000/listings
   - Нажмите "Экспорт" → выберите CSV
   - Файл должен загрузиться

2. **Графики:**
   - Откройте http://localhost:3000/dashboard
   - Выберите город
   - Проверьте отображение 3 графиков

3. **CI/CD:**
   - Запушьте изменения в GitHub
   - Проверьте Actions tab
   - Все jobs должны быть зелёными

---

## Известные проблемы

### 1. Графики не отображаются
**Причина:** Нет данных в базе  
**Решение:** Запустите сканирование для накопления данных

### 2. Экспорт пустой
**Причина:** Применены строгие фильтры  
**Решение:** Проверьте фильтры или сбросьте их

### 3. Codecov не загружает отчёты
**Причина:** Не настроен Codecov  
**Решение:** Зарегистрируйте репозиторий на codecov.io

---

## Планы на версию 2.1.0

- [ ] Уведомления (Telegram, Email)
- [ ] Избранные объявления
- [ ] Сравнение объявлений
- [ ] Поиск по тексту
- [ ] Улучшение покрытия тестов до 60%

---

## Авторы

- Backend API
- Frontend UI
- CI/CD Pipeline
- Документация

---

## Лицензия

Как и основной проект, эти изменения распространяются под той же лицензией.
