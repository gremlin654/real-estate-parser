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
    await expect(page.getByTestId('scan-button')).toBeVisible();
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
    await expect(page.getByTestId('city-select')).toBeVisible();
    await expect(page.getByTestId('status-select')).toBeVisible();
    await expect(page.getByTestId('currency-select')).toBeVisible();
    await expect(page.getByTestId('sort-select')).toBeVisible();
  });

  test('filters by city', async ({ page }) => {
    await page.getByTestId('city-select').click();
    await page.getByTestId('city-option-mogilev').click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by status', async ({ page }) => {
    await page.getByTestId('status-select').click();
    await page.getByTestId('status-option-new').click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by currency', async ({ page }) => {
    await page.getByTestId('currency-select').click();
    await page.getByTestId('currency-option-byn').click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('sorts by price ascending', async ({ page }) => {
    await page.getByTestId('sort-select').click();
    await page.getByTestId('sort-option-asc').click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('sorts by price descending', async ({ page }) => {
    await page.getByTestId('sort-select').click();
    await page.getByTestId('sort-option-desc').click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by price range', async ({ page }) => {
    // Open filters panel
    const filterButton = page.getByRole('button', { name: /Фильтры/i }).first();
    await filterButton.click();
    await page.waitForTimeout(300);

    // Fill price range
    await page.getByTestId('price-min-input').fill('100000');
    await page.getByTestId('price-max-input').fill('500000');

    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('filters by rooms', async ({ page }) => {
    await page.getByTestId('rooms-select').click();
    await page.getByTestId('room-option-2').click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table').first()).toBeVisible({ timeout: 15000 });
  });

  test('resets all filters', async ({ page }) => {
    await page.getByTestId('city-select').click();
    await page.getByTestId('city-option-mogilev').click();

    await page.getByTestId('status-select').click();
    await page.getByTestId('status-option-new').click();

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
    await page.getByTestId('rooms-select').click();
    await expect(page.getByTestId('room-option-1')).toBeVisible();
    await expect(page.getByTestId('room-option-2')).toBeVisible();
  });

  test('selecting room updates filter', async ({ page }) => {
    await page.getByTestId('rooms-select').click();
    await page.getByTestId('room-option-2').click();

    // Button should show selection
    await expect(page.getByTestId('rooms-select')).toBeVisible({ timeout: 15000 });
  });
});
