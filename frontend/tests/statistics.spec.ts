import { test, expect } from './fixtures';

test.describe('Kufar Monitor - Statistics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/statistics');
    await page.waitForLoadState('networkidle');
    // Ждем загрузки заголовка страницы
    await expect(page.getByRole('heading', { name: 'Статистика' }).first()).toBeVisible({ timeout: 20000 });
  });

  test('должна загружать страницу статистики', async ({ page }) => {
    await expect(page).toHaveURL('/statistics');
    await expect(page.getByRole('heading', { name: 'Статистика' }).first()).toBeVisible();
  });

  test('должна отображать заголовок и описание', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Статистика' }).first()).toBeVisible();
    await expect(page.getByText('Аналитика рынка недвижимости').first()).toBeVisible({ timeout: 15000 });
  });

  test('должна отображать селектор города', async ({ page }) => {
    await expect(page.getByTestId('statistics-city-select')).toBeVisible();
  });

  test('должна отображать селектор периода', async ({ page }) => {
    await expect(page.getByTestId('statistics-period-select')).toBeVisible();
  });

  test('должна отображать все табы', async ({ page }) => {
    // Ждем появления табов
    await expect(page.getByRole('tablist').first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('tab', { name: 'Динамика цен' }).first()).toBeVisible();
    await expect(page.getByRole('tab', { name: 'По комнатам' }).first()).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Активность' }).first()).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Сравнение' }).first()).toBeVisible();
  });

  test('должна переключать табы', async ({ page }) => {
    // Кликаем на "По комнатам"
    const roomsTab = page.getByRole('tab', { name: 'По комнатам' }).first();
    await roomsTab.click();
    await expect(roomsTab).toHaveAttribute('data-state', 'active');

    // Кликаем на "Активность"
    const activityTab = page.getByRole('tab', { name: 'Активность' }).first();
    await activityTab.click();
    await expect(activityTab).toHaveAttribute('data-state', 'active');
  });

  test('должна отображать график для выбранного таба', async ({ page }) => {
    // Проверяем, что график виден (Recharts использует SVG)
    const chartVisible = await page.locator('svg').first().isVisible();
    expect(chartVisible).toBe(true);
  });

  test('должна отображать карточку с графиком', async ({ page }) => {
    await expect(page.locator('canvas').or(page.locator('svg')).first()).toBeVisible({ timeout: 15000 });
  });

  test('должна отображать заголовок графика', async ({ page }) => {
    await expect(page.getByText(/Динамика цен/).first()).toBeVisible({ timeout: 15000 });
  });

  test('должна отображать описание графика', async ({ page }) => {
    await expect(page.getByText(/Средняя цена/).first()).toBeVisible();
  });

  test('должна позволять выбрать период', async ({ page }) => {
    // Выбираем 6 месяцев
    await page.getByTestId('statistics-period-select').click();
    await page.getByTestId('period-option-6').click();
    await page.waitForTimeout(500);

    // Выбираем 24 месяца
    await page.getByTestId('statistics-period-select').click();
    await page.getByTestId('period-option-24').click();
    await page.waitForTimeout(500);
  });

  test('должна позволять выбрать город', async ({ page }) => {
    // Выбираем Гомель
    await page.getByTestId('statistics-city-select').click();
    await page.getByTestId('city-option-gomel').click();
    await page.waitForTimeout(500);

    // Выбираем Брест
    await page.getByTestId('statistics-city-select').click();
    await page.getByTestId('city-option-brest').click();
    await page.waitForTimeout(500);
  });

  test('должна отображать все доступные периоды', async ({ page }) => {
    await page.getByTestId('statistics-period-select').click();
    await expect(page.getByTestId('period-option-6')).toBeVisible();
    await expect(page.getByTestId('period-option-12')).toBeVisible();
    await expect(page.getByTestId('period-option-24')).toBeVisible();
  });

  test('должна отображать все доступные города', async ({ page }) => {
    await page.getByTestId('statistics-city-select').click();
    await expect(page.getByTestId('city-option-minsk')).toBeVisible();
    await expect(page.getByTestId('city-option-mogilev')).toBeVisible();
    await expect(page.getByTestId('city-option-grodno')).toBeVisible();
    await expect(page.getByTestId('city-option-brest')).toBeVisible();
    await expect(page.getByTestId('city-option-gomel')).toBeVisible();
    await expect(page.getByTestId('city-option-vitebsk')).toBeVisible();
  });

  test('должна показывать информацию о периоде', async ({ page }) => {
    // Проверяем, что есть информация о периоде
    await expect(page.getByText(/1 год/).first()).toBeVisible({ timeout: 15000 });
  });

  test('должна корректно переключаться между табами и отображать график', async ({ page }) => {
    // Проходим по всем табам
    const tabs = [
      page.getByRole('tab', { name: 'Динамика цен' }).first(),
      page.getByRole('tab', { name: 'По комнатам' }).first(),
      page.getByRole('tab', { name: 'Активность' }).first(),
      page.getByRole('tab', { name: 'Сравнение' }).first(),
    ];

    for (const tab of tabs) {
      await tab.click();
      await expect(tab).toHaveAttribute('data-state', 'active');

      // Проверяем, что график остаётся видимым
      const chartVisible = await page.locator('svg').first().isVisible();
      expect(chartVisible).toBe(true);
    }
  });

  test('должна иметь активный таб по умолчанию', async ({ page }) => {
    const activeTab = page.locator('[role="tab"][data-state="active"]').first();
    const isActive = await activeTab.isVisible();
    expect(isActive).toBeTruthy();
  });
});
