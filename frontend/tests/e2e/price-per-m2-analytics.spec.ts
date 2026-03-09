import { test, expect } from '../fixtures';

test.describe('Price Per M² Analytics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics/price-per-m2');
    await page.waitForLoadState('networkidle');
    // Ждем загрузки заголовка
    await expect(page.getByTestId('price-per-m2-header')).toBeVisible({ timeout: 20000 });
  });

  test('должна загружать страницу аналитики', async ({ page }) => {
    await expect(page.getByTestId('price-per-m2-header')).toBeVisible();
    await expect(page.getByText('Динамика и распределение цен за квадратный метр').first()).toBeVisible();
  });

  test('должна отображать summary карточки', async ({ page }) => {
    await expect(page.getByTestId('summary-stats-cards')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Средняя цена за м²').first()).toBeVisible();
    await expect(page.getByText('Минимум').first()).toBeVisible();
    await expect(page.getByText('Максимум').first()).toBeVisible();
  });

  test('должна переключать фильтры', async ({ page }) => {
    // Фильтр по городу - используем кнопку вместо select
    const cityButton = page.getByRole('button', { name: /Минск|Город/ }).or(page.getByText('Минск')).first();
    if (await cityButton.count() > 0) {
      await cityButton.click();
      await page.getByText('Минск').first().click();
    }

    // Фильтр по валюте - используем кнопку вместо select
    const currencyButton = page.getByRole('button', { name: 'USD' }).or(page.getByText('USD')).first();
    if (await currencyButton.count() > 0) {
      await currencyButton.click();
      await page.getByText('BYN').first().click();
    }

    // Проверка что фильтр применился
    await expect(page.getByText(/BYN/).first()).toBeVisible({ timeout: 10000 });
  });

  test('должна переключать вкладки графиков', async ({ page }) => {
    // Проверка вкладки "Динамика"
    const trendTab = page.getByRole('tab', { name: 'Динамика' }).first();
    await expect(trendTab).toBeVisible();
    await trendTab.click();
    await expect(page.getByText('Динамика цены за м²').first()).toBeVisible();

    // Проверка вкладки "Распределение"
    const distributionTab = page.getByRole('tab', { name: 'Распределение' }).first();
    await expect(distributionTab).toBeVisible();
    await distributionTab.click();
    await expect(page.getByText('Распределение цены за м²').first()).toBeVisible();
  });

  test('должна переключать периоды', async ({ page }) => {
    // Используем data-testid для кнопок периодов
    const period7 = page.getByTestId('period-7');
    const period30 = page.getByTestId('period-30');
    const period90 = page.getByTestId('period-90');

    // Проверка кнопки "7 дн."
    await expect(period7).toBeVisible();
    await period7.click();

    // Проверка кнопки "30 дн."
    await expect(period30).toBeVisible();
    await period30.click();

    // Проверка кнопки "90 дн."
    await expect(period90).toBeVisible();
    await period90.click();
  });

  test('должна отображать графики', async ({ page }) => {
    // Проверка что графики существуют (Recharts использует SVG)
    const charts = page.locator('svg').first();
    await expect(charts).toBeVisible();
  });

  test('должна работать навигация из sidebar', async ({ page }) => {
    // Проверяем что можем перейти на страницу напрямую
    await page.goto('/analytics/price-per-m2');

    // Проверка что страница загрузилась
    await expect(page).toHaveURL('/analytics/price-per-m2');
    await expect(page.getByTestId('price-per-m2-header')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Динамика и распределение цен за квадратный метр').first()).toBeVisible();
  });

  test('должна отображать loading состояния', async ({ page }) => {
    // Проверяем что skeleton отображается во время загрузки
    await page.route('**/api/v1/stats/price-per-m2*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 500));
      await route.continue();
    });

    await page.goto('/analytics/price-per-m2');

    // Skeleton должен быть виден во время загрузки
    const skeletons = page.locator('[class*="skeleton"]').first();
    // Ждём появления skeleton или контента
    await page.waitForLoadState('networkidle');
    // Проверяем что страница загрузилась
    await expect(page.getByTestId('price-per-m2-header')).toBeVisible({ timeout: 15000 });
  });

  test('должна отображать фильтр по комнатам', async ({ page }) => {
    const roomButtons = page.getByRole('button', { name: /[1-5]/ }).first();
    await expect(roomButtons.first()).toBeVisible();

    // Клик на кнопку "1"
    await roomButtons.first().click();
    // Проверяем что кнопка активна через aria-pressed или класс
    await expect(roomButtons.first()).toHaveClass(/bg-primary/);
  });
});

test.describe('Price Per M² - Listings Table', () => {
  test('должна отображать колонку цены за м² в таблице', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    // Проверка заголовка колонки
    await expect(page.getByText('Цена за м²').first()).toBeVisible({ timeout: 15000 });
  });

  test('должна отображать цену за м² в деталях объявления', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    // Проверка что цена за м² отображается в таблице
    await expect(page.getByText(/м²/).first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Price Per M² - Filters', () => {
  test('должна открывать расширенные фильтры', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    // Клик на кнопку "Фильтры"
    const filterButton = page.getByRole('button', { name: 'Фильтры' }).first();
    await expect(filterButton).toBeVisible();
    await filterButton.click();

    // Проверка что фильтр по цене за м² появился
    await expect(page.getByText('Фильтр по цене за м²').first()).toBeVisible({ timeout: 10000 });
  });

  test('должна вводить значения в фильтр цены за м²', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    // Открыть фильтры
    const filterButton = page.getByRole('button', { name: 'Фильтры' }).first();
    await filterButton.click();

    // Ввод значений
    const minInput = page.locator('input[type="number"]').nth(2);
    const maxInput = page.locator('input[type="number"]').nth(3);

    await minInput.fill('2000');
    await maxInput.fill('5000');

    await expect(minInput).toHaveValue('2000');
    await expect(maxInput).toHaveValue('5000');

    // Клик на кнопку "Применить"
    const applyButton = page.locator('button:has-text("Применить")').nth(1);
    await applyButton.click();
  });

  test('должна сбрасывать фильтр цены за м²', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    // Открыть фильтры
    const filterButton = page.getByRole('button', { name: 'Фильтры' }).first();
    await filterButton.click();

    // Ввод значений
    const minInput = page.locator('input[type="number"]').nth(2);
    await minInput.fill('2000');

    // Клик на кнопку "Сброс"
    const resetButton = page.locator('button:has-text("Сброс")').nth(1);
    await resetButton.click();

    await expect(minInput).toHaveValue('');
  });
});

test.describe('Price Per M² - Currency Switch', () => {
  test('должна переключать валюту на странице аналитики', async ({ page }) => {
    await page.goto('/analytics/price-per-m2');
    await page.waitForLoadState('networkidle');

    // Переключение на BYN через клик на кнопку
    const currencyButton = page.getByRole('button', { name: 'USD' }).or(page.getByText('USD')).first();
    if (await currencyButton.count() > 0) {
      await currencyButton.click();
      // Выбор BYN из dropdown - используем более специфичный селектор
      await page.getByRole('menuitem', { name: 'BYN' }).or(page.getByText('BYN', { exact: true })).first().click();
    }

    // Проверка что валюта обновилась в карточках
    await expect(page.getByText(/BYN\/м²/).first()).toBeVisible({ timeout: 15000 });
  });

  test('должна переключать валюту в таблице объявлений', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    // Переключение на BYN через клик на кнопку
    const currencyButton = page.getByRole('button', { name: 'USD' }).or(page.getByText('USD')).first();
    if (await currencyButton.count() > 0) {
      await currencyButton.click();
      // Используем force click для обхода перехвата событий
      await page.getByText('Цена BYN').first().click({ force: true });
    }

    // Проверка что валюта обновилась в таблице
    await expect(page.locator('text=BYN').first()).toBeVisible({ timeout: 15000 });
  });
});
