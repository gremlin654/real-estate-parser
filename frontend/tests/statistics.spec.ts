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
    // Select использует button с placeholder
    await expect(page.getByRole('button', { name: 'Город' }).or(page.getByText('Минск').first()).first()).toBeVisible();
  });

  test('должна отображать селектор периода', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Период' }).or(page.getByText('1 год').first()).first()).toBeVisible();
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
    const periodButton = page.getByRole('button', { name: 'Период' }).or(page.getByText('1 год').first()).first();
    await periodButton.click();
    await page.getByText('6 месяцев').first().click();
    await expect(page.getByText('6 месяцев').first()).toBeVisible({ timeout: 10000 });

    // Выбираем 24 месяца
    await periodButton.click();
    await page.getByText('2 года').first().click();
    await expect(page.getByText('2 года').first()).toBeVisible({ timeout: 10000 });
  });

  test('должна позволять выбрать город', async ({ page }) => {
    // Выбираем Гомель
    const cityButton = page.getByRole('button', { name: 'Город' }).or(page.getByText('Минск').first()).first();
    await cityButton.click();
    await page.getByText('Гомель').first().click();
    await expect(page.getByText('Гомель').first()).toBeVisible({ timeout: 10000 });

    // Выбираем Брест
    await cityButton.click();
    await page.getByText('Брест').first().click();
    await expect(page.getByText('Брест').first()).toBeVisible({ timeout: 10000 });
  });

  test('должна отображать все доступные периоды', async ({ page }) => {
    const periodButton = page.getByRole('button', { name: 'Период' }).or(page.getByText('1 год').first()).first();
    await periodButton.click();
    await expect(page.getByText('6 месяцев').first()).toBeVisible();
    await expect(page.getByText('1 год').first()).toBeVisible();
    await expect(page.getByText('2 года').first()).toBeVisible();
  });

  test('должна отображать все доступные города', async ({ page }) => {
    const cityButton = page.getByRole('button', { name: 'Город' }).or(page.getByText('Минск').first()).first();
    await cityButton.click();
    await expect(page.getByText('Минск').first()).toBeVisible();
    await expect(page.getByText('Могилёв').first()).toBeVisible();
    await expect(page.getByText('Гродно').first()).toBeVisible();
    await expect(page.getByText('Брест').first()).toBeVisible();
    await expect(page.getByText('Гомель').first()).toBeVisible();
    await expect(page.getByText('Витебск').first()).toBeVisible();
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
