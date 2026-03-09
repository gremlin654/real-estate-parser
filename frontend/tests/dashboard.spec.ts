import { test, expect } from './fixtures';

test.describe('Dashboard', () => {
  test('should load dashboard page', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveTitle(/Kufar Monitor/);
  });

  test('should display statistics cards', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Панель управления' })).toBeVisible({ timeout: 15000 });
  });
});
