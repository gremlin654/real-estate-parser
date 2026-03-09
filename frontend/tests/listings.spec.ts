import { test, expect } from './fixtures';
import { ListingsPage } from './pages/ListingsPage';

test.describe('Listings', () => {
  test('should load listings page', async ({ page }) => {
    const listingsPage = new ListingsPage(page);
    await listingsPage.goto();
    await listingsPage.waitForLoad();
    await expect(page.getByRole('heading', { name: 'Объявления' }).first()).toBeVisible();
  });

  test('should filter by city', async ({ page }) => {
    const listingsPage = new ListingsPage(page);
    await listingsPage.goto();
    await listingsPage.waitForLoad();

    const citySelect = page.getByLabel('Город').first();
    await citySelect.click();
    await page.getByText('Минск', { exact: true }).first().click();
    await page.waitForLoadState('networkidle');
  });
});
