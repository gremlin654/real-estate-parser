import { test, expect } from './fixtures';

test.describe('Listings', () => {
  test('should load listings page', async ({ page }) => {
    await page.goto('/listings');
    await expect(page.getByText('Объявления')).toBeVisible();
  });

  test('should filter by city', async ({ page }) => {
    await page.goto('/listings');
    const citySelect = page.locator('select').first();
    await citySelect.selectOption('minsk');
  });
});
