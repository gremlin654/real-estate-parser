import { test, expect } from './fixtures';

test.describe('Settings', () => {
  test('should load settings page', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByText('Настройки')).toBeVisible();
  });
});
