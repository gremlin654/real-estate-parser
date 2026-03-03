# Kufar Monitor - Playwright E2E Тесты

## ✅ Результаты тестов

**Все 118 тестов пройдено успешно!**

| Набор тестов | Количество | Статус |
|-------------|------------|--------|
| Dashboard | 3 | ✅ |
| Dashboard Extended | 7 | ✅ |
| API Integration | 2 | ✅ |
| Listing Detail | 5 | ✅ |
| Listings | 4 | ✅ |
| Listings Filters | 18 | ✅ |
| Mobile Responsive | 3 | ✅ |
| Scanning | 2 | ✅ |
| Settings | 11 | ✅ NEW |
| Statistics | 18 | ✅ NEW |
| Navigation | 11 | ✅ NEW |
| UI Components | 16 | ✅ NEW |
| API Endpoints | 18 | ✅ NEW |
| **Итого** | **118** | **✅ 100%** |

## Быстрый старт

### 1. Установка зависимостей

```bash
cd frontend

# Установить зависимости
npm install

# Установить браузеры Playwright
npx playwright install chromium
```

### 2. Запуск тестов

```bash
# Запустить все тесты
npm run test:e2e

# Запустить в режиме браузера (headed)
npm run test:e2e:headed

# Запустить UI режим для интерактивной отладки
npm run test:e2e:ui

# Запустить конкретный тест
npx playwright test -g "Dashboard"

# Запустить на мобильном устройстве
npx playwright test --project="Mobile Chrome"
```

### 3. Coverage (покрытие кода)

```bash
# Запустить все тесты с покрытием (Unit + E2E)
npm run coverage

# Запустить только Unit тесты с покрытием
npm run test:unit:coverage

# Запустить Unit тесты в режиме наблюдения
npm run test:unit:watch

# Запустить E2E тесты с покрытием и генерацией отчёта
npm run test:e2e:coverage

# Показать HTML отчёт coverage
npm run coverage:show
```

**Отчёты о покрытии сохраняются в:**
- `coverage/vitest/index.html` — HTML отчёт (Unit тесты через Vitest)
- `coverage/vitest/lcov.info` — LCOV формат (для CI/CD)
- `playwright-report/coverage/index.html` — HTML отчёт (E2E тесты Playwright)
- `playwright-report/index.html` — HTML отчёт тестов

**Примечание:** E2E coverage через Playwright требует дополнительной настройки source maps в Vite для точного покрытия. Unit тесты через Vitest предоставляют более точные данные покрытия.

**Текущее покрытие:** 66.12% ✅ (цель: 65%)

### 4. Просмотр отчётов

```bash
# Показать HTML отчёт
npm run test:e2e:report

# Или напрямую
npx playwright show-report
```

## Структура тестов

```
frontend/
├── tests/
│   ├── dashboard.spec.ts           # Тесты главной страницы (3)
│   ├── dashboard-extended.spec.ts  # Расширенные тесты Dashboard (7)
│   ├── listings.spec.ts            # Тесты списка объявлений (4)
│   ├── listing-detail.spec.ts      # Тесты детальной страницы (5)
│   ├── listings-filters.spec.ts    # Тесты фильтров и сортировки (18)
│   ├── mobile.spec.ts              # Тесты адаптивности (3)
│   ├── scanning.spec.ts            # Тесты сканирования (2)
│   ├── api-integration.spec.ts     # Тесты API интеграции (2)
│   ├── settings.spec.ts            # Тесты настроек (11) NEW
│   ├── statistics.spec.ts          # Тесты статистики (18) NEW
│   ├── navigation.spec.ts          # Тесты навигации (11) NEW
│   ├── ui-components.spec.ts       # Тесты UI компонентов (16) NEW
│   ├── api-endpoints.spec.ts       # Тесты API endpoints (18) NEW
│   └── pages/
│       ├── DashboardPage.tsx
│       ├── ListingsPage.tsx
│       ├── SettingsPage.tsx        # NEW
│       ├── StatisticsPage.tsx      # NEW
│       └── index.ts                # Page Object модели
├── playwright.config.ts            # Конфигурация Playwright
├── TESTS.md                        # Этот файл
└── E2E_TESTS.md                    # Подробная документация E2E
```

## Покрытие тестами

### ✅ Dashboard (10 тестов)
- Загрузка главной страницы
- Отображение карточек статистики
- Ссылка на Listings
- История сканирований
- Быстрые действия
- Смена города

### ✅ Listings (22 теста)
- Загрузка страницы объявлений
- Отображение списка объявлений
- Открытие детальной страницы
- Кнопка сканирования
- **Фильтры и сортировка:**
  - Фильтр по городу
  - Фильтр по статусу
  - Фильтр по валюте
  - Сортировка по цене
  - Фильтр по диапазону цен
  - Фильтр по комнатам
  - Сброс фильтров
  - Пагинация
  - Empty state

### ✅ Listing Detail (5 тестов)
- Загрузка детальной страницы
- Галерея изображений
- Цена и статус
- Ссылка на Kufar
- Кнопка назад

### ✅ Settings (11 тестов) NEW
- Загрузка страницы настроек
- Выбор города сканирования
- Переключение автосканирования
- Изменение интервала сканирования
- Сохранение настроек
- Валидация интервала
- Отображение текущих настроек
- Обработка ошибок

### ✅ Statistics (18 тестов) NEW
- Загрузка страницы статистики
- Селектор города и периода
- Табы комнат (1, 2, 3, 4)
- Переключение между табами
- Отображение графиков
- Данные о количестве месяцев

### ✅ Navigation (11 тестов) NEW
- Переходы между всеми страницами
- Навигация через боковую панель
- Открытие ListingDetail
- Возврат назад
- Сохранение состояния

### ✅ UI Components (16 тестов) NEW
- Тёмная тема
- Логотип и иконки
- Переключатель sidebar
- Loading состояния
- Hover эффекты
- Селекторы и input
- Switch и Alert
- Responsive дизайн

### ✅ API Endpoints (18 тестов) NEW
- Health endpoint
- Список городов
- Расписание сканирования
- Статус и прогресс сканирования
- Summary статистика
- Список объявлений
- История объявления
- Price trends
- Обновление настроек
- Запуск сканирования
- CORS и Content-Type
- Время ответа API

### ✅ Mobile Responsive (3 теста)
- Мобильная версия (375x667)
- Планшетная версия (768x1024)
- Desktop версия

### ✅ Scanning (2 теста)
- Кнопка сканирования
- Запуск сканирования

### ✅ API Integration (2 теста)
- Загрузка данных с backend
- Запрос к API статистики

## Page Objects

### DashboardPage
```typescript
import { DashboardPage } from './pages';

const dashboard = new DashboardPage(page);
await dashboard.goto();
await dashboard.waitForLoad();
await expect(dashboard.heading).toBeVisible();
```

### ListingsPage
```typescript
import { ListingsPage } from './pages';

const listings = new ListingsPage(page);
await listings.goto();
await listings.waitForLoad();
const count = await listings.getListingsCount();
```

### ListingDetailPage
```typescript
import { ListingDetailPage } from './pages';

const detail = new ListingDetailPage(page);
await detail.waitForLoad();
const imageCount = await detail.getImageCount();
```

## Конфигурация

### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ['json', { outputFile: 'test-results.json' }]
  ],
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
    { name: 'iPad', use: { ...devices['iPad Pro'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Скрипты npm

```json
{
  "test:e2e": "playwright test",
  "test:e2e:ui": "playwright test --ui",
  "test:e2e:headed": "playwright test --headed",
  "test:e2e:report": "playwright show-report"
}
```

## Отладка

### Режим отладки

```bash
# Запустить с отладчиком
npx playwright test --debug

# Запустить конкретный тест с отладкой
npx playwright test -g "Dashboard" --debug
```

### Trace Viewer

```bash
# Посмотреть trace упавшего теста
npx playwright show-trace test-results/<test-path>/trace.zip
```

### Скриншоты и видео

При падении теста автоматически сохраняются:
- Скриншоты в `test-results/`
- Видео в `test-results/`
- Trace в `test-results/`

## CI/CD Интеграция

### GitHub Actions Example

```yaml
name: Playwright Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run Playwright tests
        run: npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

## Best Practices

1. **Используйте Page Object Model** - инкапсулируйте логику страниц
2. **Добавляйте data-testid** для стабильных селекторов
3. **Используйте expect с timeout** для асинхронных операций
4. **Делайте тесты независимыми** - каждый тест работает изолированно
5. **Очищайте состояние** между тестами при необходимости

## Примеры тестов

### Базовый тест
```typescript
test('должна загружать главную страницу', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Панель управления' }))
    .toBeVisible();
});
```

### Тест с переходом
```typescript
test('должна открывать детальную страницу', async ({ page }) => {
  await page.goto('/listings');
  await page.waitForTimeout(1000);
  
  await page.waitForSelector('a[href^="/listings/"]');
  await page.locator('a[href^="/listings/"]').first().click();
  await page.waitForTimeout(1000);
  
  const currentUrl = page.url();
  expect(currentUrl).toMatch(/\/listings\/[\w-]+/);
});
```

### Тест с проверкой API
```typescript
test('должна загружать данные с backend', async ({ page }) => {
  const [response] = await Promise.all([
    page.waitForResponse(r => 
      r.url().includes('/api/v1/') && r.status() === 200
    ),
    page.goto('/listings'),
  ]);
  
  const data = await response.json();
  expect(data).toBeDefined();
});
```

## Устранение проблем

### Тесты падают по таймауту
- Увеличьте `waitForTimeout`
- Проверьте, что backend запущен
- Используйте `waitForSelector` вместо фиксированных задержек

### Браузер не запускается
```bash
# Переустановите браузеры
npx playwright install --force

# Проверьте зависимости
npx playwright install-deps
```

### Ложные срабатывания
- Добавьте `retries: 2` в конфиге
- Используйте стабильные селекторы
- Избегайте race conditions

## Требования

- Node.js 18+
- npm 9+
- Playwright 1.40+
- Chromium (устанавливается автоматически)

## Запуск в Docker

```bash
# Запустить тесты в Docker контейнере
docker run --rm --network host \
  -v $(pwd):/work/ \
  -w /work/ \
  mcr.microsoft.com/playwright:v1.40.0 \
  npm run test:e2e
```

## Контакты

Вопросы и предложения: создавайте issue в репозитории проекта.
