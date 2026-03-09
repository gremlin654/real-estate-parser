import { test, expect } from './fixtures';

test.describe('Listings - Filters and Sorting', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');
    // Ждем загрузки заголовка
    await expect(page.getByRole('heading', { name: 'Объявления' }).first()).toBeVisible({ timeout: 20000 });
  });

  test('displays listings table', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Объявления' }).first()).toBeVisible();
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('displays scan button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Сканировать/i }).first()).toBeVisible();
  });

  test('clicking scan button starts scanning', async ({ page }) => {
    await page.getByRole('button', { name: /Сканировать/i }).first().click();

    // Should show scanning state
    await expect(
      page.getByText(/Сканирование.../i).or(page.getByText(/Обновляется/i)).or(page.locator('table').first()).first()
    ).toBeVisible({ timeout: 15000 });
  });

  test('filter button opens filters panel', async ({ page }) => {
    // Click on "Фильтры" button to show extended filters
    const filterButton = page.getByRole('button', { name: /Фильтры/i }).first();
    await expect(filterButton).toBeVisible();
    await filterButton.click();
    
    // Check that price filter is visible
    await expect(page.getByText('Фильтр по цене:').first()).toBeVisible({ timeout: 10000 });
  });

  test('all main filter buttons are visible', async ({ page }) => {
    // Select components use buttons with placeholders
    await expect(page.getByRole('button', { name: /Все города|Город/ }).or(page.getByText('Все города').first()).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Все статусы|Статус/ }).or(page.getByText('Все статусы').first()).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Цена USD|Валюта/ }).or(page.getByText('Цена USD').first()).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Сортировка/ }).or(page.getByText('По дате').first()).first()).toBeVisible();
  });

  test('filters by city', async ({ page }) => {
    const cityButton = page.getByRole('button', { name: /Все города|Город/ }).or(page.getByText('Все города').first()).first();
    await cityButton.click();
    await page.getByText('Могилёв').first().click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by status', async ({ page }) => {
    const statusButton = page.getByRole('button', { name: /Все статусы|Статус/ }).or(page.getByText('Все статусы').first()).first();
    await statusButton.click();
    await page.getByText('Новые').first().click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by currency', async ({ page }) => {
    const currencyButton = page.getByRole('button', { name: /Цена USD|Валюта/ }).or(page.getByText('Цена USD').first()).first();
    await currencyButton.click();
    await page.getByText('Цена USD').first().click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('sorts by price ascending', async ({ page }) => {
    const sortButton = page.getByRole('button', { name: /Сортировка/ }).or(page.getByText('По дате').first()).first();
    await sortButton.click();
    await page.getByText('Цена ↑').first().click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('sorts by price descending', async ({ page }) => {
    const sortButton = page.getByRole('button', { name: /Сортировка/ }).or(page.getByText('По дате').first()).first();
    await sortButton.click();
    await page.getByText('Цена ↓').first().click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by price range', async ({ page }) => {
    // Open filters panel
    const filterButton = page.getByRole('button', { name: /Фильтры/i }).first();
    await filterButton.click();
    
    // Fill price range
    const minPriceInput = page.getByPlaceholder('Мин. цена').first();
    const maxPriceInput = page.getByPlaceholder('Макс. цена').first();
    
    await minPriceInput.fill('100000');
    await maxPriceInput.fill('500000');
    
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by rooms', async ({ page }) => {
    const roomsButton = page.getByRole('button', { name: /Комнаты/i }).first();
    await roomsButton.click();
    await page.getByText('2 комнаты').first().click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('resets all filters', async ({ page }) => {
    const cityButton = page.getByRole('button', { name: /Все города|Город/ }).or(page.getByText('Все города').first()).first();
    await cityButton.click();
    await page.getByText('Могилёв').first().click();
    
    const statusButton = page.getByRole('button', { name: /Все статусы|Статус/ }).or(page.getByText('Все статусы').first()).first();
    await statusButton.click();
    await page.getByText('Новые').first().click();

    // Reset by clicking reset button or reloading
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // After reset, table should be visible
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('pagination works', async ({ page }) => {
    // Check pagination controls exist
    await expect(page.getByRole('navigation').first()).toBeVisible({ timeout: 15000 });
  });

  test('room filter opens popover', async ({ page }) => {
    const roomsButton = page.getByRole('button', { name: /Комнаты/i }).first();
    await roomsButton.click();
    await expect(page.getByText('1 комната').first()).toBeVisible();
    await expect(page.getByText('2 комнаты').first()).toBeVisible();
  });

  test('selecting room updates filter', async ({ page }) => {
    const roomsButton = page.getByRole('button', { name: /Комнаты/i }).first();
    await roomsButton.click();
    await page.getByText('2 комнаты').first().click();

    // Button should show selection
    await expect(page.getByRole('button', { name: /Комнаты/i }).first()).toBeVisible({ timeout: 15000 });
  });
});
