# Real Estate Parser — Система мониторинга недвижимости Kufar.by

Автоматизированная система для отслеживания объявлений о продаже недвижимости на портале [Kufar.by](https://re.kufar.by).

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
- ✅ Отслеживание изменений цен
- ✅ История сканирований
- ✅ Экспорт данных (CSV, XLSX, JSON)
- ✅ Графики и аналитика
- ✅ CI/CD pipeline

## 🔗 Доступ к сервисам

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## 🛠 Технологии

- **Frontend**: React 19, TypeScript, Vite, TailwindCSS, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Testing**: Playwright (E2E), Vitest (Unit), Pytest (API)
