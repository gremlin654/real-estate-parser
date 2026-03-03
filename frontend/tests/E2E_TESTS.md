# Kufar Monitor - E2E Тесты (Playwright)

## 📊 Обзор тестов

### Количество тестов: 11 наборов

| Набор тестов | Файл | Количество | Статус |
|-------------|------|------------|--------|
| **Dashboard** | `dashboard.spec.ts` | 3 | ✅ |
| **Dashboard Extended** | `dashboard-extended.spec.ts` | 7 | ✅ |
| **Listings** | `listings.spec.ts` | 4 | ✅ |
| **Listing Detail** | `listing-detail.spec.ts` | 5 | ✅ |
| **Listings Filters** | `listings-filters.spec.ts` | 18 | ✅ |
| **Mobile Responsive** | `mobile.spec.ts` | 3 | ✅ |
| **Scanning** | `scanning.spec.ts` | 2 | ✅ |
| **API Integration** | `api-integration.spec.ts` | 2 | ✅ |
| **Settings** | `settings.spec.ts` | 11 | ✅ |
| **Statistics** | `statistics.spec.ts` | 18 | ✅ |
| **Navigation** | `navigation.spec.ts` | 11 | ✅ |
| **UI Components** | `ui-components.spec.ts` | 16 | ✅ |
| **API Endpoints** | `api-endpoints.spec.ts` | 18 | ✅ |
| **ИТОГО** | **13 файлов** | **118 тестов** | **✅** |

## 🎯 Покрытие функционала

### ✅ Dashboard (Главная страница)
- Загрузка главной страницы
- Отображение карточек статистики (Новых сегодня, Удалено сегодня, Изменилась цена, Активных всего)
- Ссылка на Listings
- История сканирований
- Быстрые действия
- Смена города

### ✅ Listings (Список объявлений)
- Загрузка страницы объявлений
- Отображение списка объявлений
- Открытие детальной страницы
- Кнопка сканирования
- **Фильтры и сортировка:**
  - Фильтр по городу
  - Фильтр по статусу
  - Фильтр по валюте
  - Сортировка по цене (возрастание/убывание)
  - Фильтр по диапазону цен
  - Фильтр по количеству комнат
  - Сброс всех фильтров
  - Пагинация
  - Empty state

### ✅ Listing Detail (Детальная страница)
- Загрузка детальной страницы
- Галерея изображений
- Цена и статус
- Ссылка на Kufar
- Кнопка "Назад"

### ✅ Settings (Настройки)
- Загрузка страницы настроек
- Выбор города сканирования
- Переключение автоматического сканирования
- Изменение интервала сканирования
- Сохранение настроек
- Валидация интервала (5-1440 минут)
- Отображение текущих настроек
- Обработка ошибок

### ✅ Statistics (Статистика)
- Загрузка страницы статистики
- Селектор города
- Селектор периода (6, 12, 24 месяца)
- Табы комнат (1, 2, 3, 4 комнатные)
- Переключение между табами
- Отображение графиков
- Данные о количестве месяцев

### ✅ Navigation (Навигация)
- Переход Dashboard → Listings
- Переход Dashboard → Settings
- Переход Dashboard → Statistics
- Переход Listings → Dashboard
- Переход Settings → Dashboard
- Переход Statistics → Dashboard
- Навигация через боковую панель
- Открытие ListingDetail из Listings
- Возврат с ListingDetail на Listings
- Сохранение состояния при обновлении
- Прямой переход по URL

### ✅ UI Components (UI компоненты)
- Тёмная тема
- Логотип/название приложения
- Иконки в навигации
- Footer
- Переключатель сворачивания sidebar
- Loading состояния
- Карточки с тенями
- Hover эффекты на кнопках
- Селекторы с выпадающими списками
- Input поля
- Switch переключатели
- Alert сообщения
- Отступы и padding
- Responsive дизайн

### ✅ API Endpoints (API тесты)
- Health endpoint
- Список городов
- Расписание сканирования
- Текущий город
- Статус сканирования
- Прогресс сканирования
- Summary статистика
- Список объявлений
- История объявления
- Обновление расписания
- Обновление города
- Запуск сканирования
- Price trends
- Обработка ошибок
- CORS заголовки
- Content-Type
- Время ответа API

### ✅ Mobile Responsive (Адаптивность)
- Мобильная версия (375x667)
- Планшетная версия (768x1024)
- Desktop версия (1920x1080)

### ✅ Scanning (Сканирование)
- Кнопка сканирования
- Запуск сканирования

### ✅ API Integration (Интеграция с API)
- Загрузка данных с backend
- Запрос к API статистики

## 🚀 Быстрый старт

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

# Запустить конкретный набор тестов
npx playwright test -g "Settings"
npx playwright test -g "Statistics"
npx playwright test -g "Navigation"

# Запустить на мобильном устройстве
npx playwright test --project="Mobile Chrome"
npx playwright test --project="iPad"
```

### 3. Coverage (покрытие кода)

```bash
# Запустить все тесты с покрытием (Unit + E2E)
npm run coverage

# Запустить E2E тесты с покрытием и генерацией отчёта
npm run test:e2e:coverage

# Показать HTML отчёт coverage
npm run coverage:show
```

**Отчёты о покрытии:**
- `playwright-report/index.html` — HTML отчёт тестов
- `playwright-report/coverage/index.html` — E2E coverage отчёт
- `coverage/vitest/index.html` — Unit coverage отчёт

## 📁 Структура тестов

```
frontend/tests/
├── fixtures.ts                    # Фикстуры с coverage
├── pages/                         # Page Object модели
│   ├── DashboardPage.tsx
│   ├── ListingsPage.tsx
│   ├── SettingsPage.tsx
│   ├── StatisticsPage.tsx
│   └── index.ts
├── dashboard.spec.ts              # Dashboard тесты (3)
├── dashboard-extended.spec.ts     # Dashboard расширенные (7)
├── listings.spec.ts               # Listings тесты (4)
├── listing-detail.spec.ts         # Listing Detail тесты (5)
├── listings-filters.spec.ts       # Filters & Sorting тесты (18)
├── mobile.spec.ts                 # Mobile Responsive тесты (3)
├── scanning.spec.ts               # Scanning тесты (2)
├── api-integration.spec.ts        # API Integration тесты (2)
├── settings.spec.ts               # Settings тесты (11)
├── statistics.spec.ts             # Statistics тесты (18)
├── navigation.spec.ts             # Navigation тесты (11)
├── ui-components.spec.ts          # UI Components тесты (16)
├── api-endpoints.spec.ts          # API Endpoints тесты (18)
├── TESTS.md                       # Документация
└── E2E_TESTS.md                   # Этот файл
```

## 🧩 Page Objects

### DashboardPage
```typescript
import { DashboardPage } from './pages/index';

const dashboard = new DashboardPage(page);
await dashboard.goto();
await dashboard.waitForLoad();
await dashboard.selectCity('Минск');
```

### ListingsPage
```typescript
import { ListingsPage } from './pages/index';

const listings = new ListingsPage(page);
await listings.goto();
await listings.selectCity('Могилёв');
await listings.selectStatus('Активные');
await listings.setPriceRange('100000', '500000');
```

### SettingsPage
```typescript
import { SettingsPage } from './pages/index';

const settings = new SettingsPage(page);
await settings.goto();
await settings.selectCity('Гомель');
await settings.setInterval('60');
await settings.save();
```

### StatisticsPage
```typescript
import { StatisticsPage } from './pages/index';

const statistics = new StatisticsPage(page);
await statistics.goto();
await statistics.selectCity('Брест');
await statistics.selectPeriod('12 месяцев');
await statistics.selectRoomTab('2');
```

## ⚙️ Конфигурация

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
    ['json', { outputFile: 'test-results.json' }],
    ['monocart-reporter', {
      name: 'Kufar Monitor - Test Report',
      coverage: { outputDir: './monocart-report/coverage' },
    }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
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
    timeout: 60000,
  },
});
```

## 🔧 Отладка

### Режим отладки

```bash
# Запустить с отладчиком
npx playwright test --debug

# Запустить конкретный тест с отладкой
npx playwright test -g "Settings" --debug
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

## 📝 Примеры тестов

### Базовый тест
```typescript
test('должна загружать страницу настроек', async ({ page }) => {
  const settings = new SettingsPage(page);
  await settings.goto();
  await settings.waitForLoad();
  
  await expect(settings.header).toBeVisible();
});
```

### Тест с взаимодействием
```typescript
test('должна сохранять настройки', async ({ page }) => {
  const settings = new SettingsPage(page);
  await settings.goto();
  await settings.waitForLoad();
  
  await settings.setInterval('45');
  await settings.save();
  
  await expect(settings.successAlert).toBeVisible({ timeout: 5000 });
});
```

### Тест с переключением табов
```typescript
test('должна переключать табы комнат', async ({ page }) => {
  const statistics = new StatisticsPage(page);
  await statistics.goto();
  await statistics.waitForLoad();
  
  await statistics.twoRoomTab.click();
  await expect(statistics.twoRoomTab).toHaveAttribute('data-state', 'active');
});
```

### Тест навигации
```typescript
test('должна навигировать с Dashboard на Listings', async ({ page }) => {
  const dashboard = new DashboardPage(page);
  await dashboard.goto();
  await dashboard.waitForLoad();
  
  const listingsLink = page.getByRole('link', { name: /Объявления/i });
  await listingsLink.click();
  
  await expect(page).toHaveURL('/listings');
});
```

## 🎯 Best Practices

1. **Используйте Page Object Model** - инкапсулируйте логику страниц
2. **Добавляйте data-testid** для стабильных селекторов
3. **Используйте expect с timeout** для асинхронных операций
4. **Делайте тесты независимыми** - каждый тест работает изолированно
5. **Используйте beforeEach** для общей подготовки
6. **Группируйте тесты по функционалу** в describe блоках
7. **Давайте тестам понятные имена** на русском языке
8. **Проверяйте видимые элементы** через `toBeVisible()`
9. **Используйте waitForLoad** для ожидания загрузки страниц
10. **Добавляйте тесты с покрытием всех сценариев** (успех, ошибка, валидация)

## 🐛 Устранение проблем

### Тесты падают по таймауту
- Увеличьте `waitForTimeout`
- Проверьте, что backend запущен
- Используйте `waitForSelector` вместо фиксированных задержек
- Увеличьте `actionTimeout` и `navigationTimeout` в конфиге

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

### Backend не отвечает
- Убедитесь, что backend запущен: `docker-compose up backend`
- Проверьте URL API в тестах
- Используйте mock данные при необходимости

## 📊 Покрытие тестами

### Текущее покрытие
- **E2E тесты:** 118 тестов
- **Unit тесты:** 326 тестов
- **Общее покрытие:** 66.12%

### Целевое покрытие
- **Минимум:** 65%
- **Цель:** 70%
- **Идеал:** 80%

## 🔄 CI/CD Интеграция

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

## 📋 Требования

- Node.js 18+
- npm 9+
- Playwright 1.40+
- Chromium (устанавливается автоматически)
- Backend API (для интеграционных тестов)

## 🎓 Обучение

### Документация
- [Playwright Documentation](https://playwright.dev)
- [Playwright Test](https://playwright.dev/docs/test-intro)
- [Page Object Model](https://playwright.dev/docs/pom)
- [Fixtures](https://playwright.dev/docs/test-fixtures)

### Видео
- [Playwright Tutorial](https://www.youtube.com/results?search_query=playwright+tutorial)
- [E2E Testing Best Practices](https://www.youtube.com/results?search_query=e2e+testing+best+practices)

## 📞 Контакты

Вопросы и предложения: создавайте issue в репозитории проекта.
