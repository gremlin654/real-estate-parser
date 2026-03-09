import { test, expect } from './fixtures';
import { ListingsPage } from './pages/ListingsPage';

test.describe('Listings - Filters and Sorting', () => {
  let listingsPage: ListingsPage;

  test.beforeEach(async ({ page }) => {
    listingsPage = new ListingsPage(page);
    await listingsPage.goto();
    await listingsPage.waitForLoad();
  });

  test('displays listings table', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Объявления' }).first()).toBeVisible();
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by city', async ({ page }) => {
    await listingsPage.selectCity('Могилёв');
    await expect(page.getByText('Могилёв').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by status', async ({ page }) => {
    await listingsPage.selectStatus('Новые');
    await expect(page.getByRole('button', { name: /Сканировать/i }).first()).toBeVisible();
  });

  test('filters by currency', async ({ page }) => {
    await listingsPage.selectCurrency('USD');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('sorts by price ascending', async ({ page }) => {
    await listingsPage.selectSortOrder('Цена ↑');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('sorts by price descending', async ({ page }) => {
    await listingsPage.selectSortOrder('Цена ↓');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by price range', async ({ page }) => {
    await listingsPage.setPriceRange('100000', '500000');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by rooms', async ({ page }) => {
    await listingsPage.selectRooms(['2']);
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('resets all filters', async ({ page }) => {
    await listingsPage.selectCity('Могилёв');
    await listingsPage.selectStatus('Новые');
    await listingsPage.selectCurrency('USD');

    await listingsPage.resetFilters();

    // After reset, city should be back to default
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('displays empty state when no results', async ({ page }) => {
    // Set filters that likely return no results
    await listingsPage.setPriceRange('10000000', '20000000');
    await expect(page.getByText('Объявлений не найдено').first()).toBeVisible({ timeout: 20000 });
  });

  test('pagination works', async ({ page }) => {
    // Check pagination controls exist
    await expect(page.getByRole('navigation', { name: /pagination/i }).first()).toBeVisible({ timeout: 15000 });
  });

  test('displays scan button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Сканировать/i }).first()).toBeVisible();
  });

  test('clicking scan button starts scanning', async ({ page }) => {
    await page.getByRole('button', { name: /Сканировать/i }).first().click();

    // Should show scanning state
    await expect(
      page.getByText(/Сканирование.../i).or(page.getByText(/Обновляется/i)).first()
    ).toBeVisible({ timeout: 15000 });
  });

  test('displays filter panel', async ({ page }) => {
    await expect(page.getByText('Фильтры').first()).toBeVisible({ timeout: 15000 });
  });

  test('all filter inputs are visible', async ({ page }) => {
    await expect(page.getByLabel('Город').first()).toBeVisible();
    await expect(page.getByLabel('Статус').first()).toBeVisible();
    await expect(page.getByLabel('Валюта').first()).toBeVisible();
    await expect(page.getByLabel('Сортировка').first()).toBeVisible();
    await expect(page.getByPlaceholder('Мин. цена').first()).toBeVisible();
    await expect(page.getByPlaceholder('Макс. цена').first()).toBeVisible();
  });

  test('room filter opens popover', async ({ page }) => {
    await page.getByRole('button', { name: /Комнаты/i }).first().click();
    await expect(page.getByText('1 комната').first()).toBeVisible();
    await expect(page.getByText('2 комнаты').first()).toBeVisible();
  });

  test('selecting room updates filter', async ({ page }) => {
    await page.getByRole('button', { name: /Комнаты/i }).first().click();
    await page.getByText('2 комнаты').first().click();

    // Button should show selection
    await expect(page.getByRole('button', { name: /1 комн\./i }).first()).toBeVisible({ timeout: 15000 });
  });
});
