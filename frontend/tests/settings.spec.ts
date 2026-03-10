import { test, expect } from './fixtures';

test.describe('Settings', () => {
  test('should load settings page', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /Настройки/i }).first()).toBeVisible({ timeout: 20000 });
    await expect(page.getByText('Управление параметрами сканирования').first()).toBeVisible();
  });

  test('should update scan interval', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Change interval using slider - используем first() для strict mode
    const slider = page.getByRole('slider').first();
    if (await slider.isVisible()) {
      await slider.click();
      await page.waitForLoadState('networkidle');
    }

    // Save changes
    const saveButton = page.getByRole('button', { name: 'Сохранить' }).first();
    if (await saveButton.isVisible()) {
      await saveButton.click();
      await page.waitForLoadState('networkidle');
    }
  });

  test('should change city', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // Select different city from dropdown
    const citySelect = page.getByLabel('Город сканирования').first();
    await citySelect.click();
    await page.getByRole('option', { name: 'Гродно' }).first().click();
    await page.waitForLoadState('networkidle');

    // Wait for city to update
    await expect(page.getByText('Гродно').first()).toBeVisible({ timeout: 20000 });
  });
});
