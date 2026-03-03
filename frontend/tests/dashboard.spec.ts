import { test, expect } from './fixtures';

test.describe('Dashboard', () => {
  test('should load dashboard page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Kufar Monitor/);
  });

  test('should display statistics cards', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Панель управления')).toBeVisible();
  });
});
