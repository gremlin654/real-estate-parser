import { test, expect } from './fixtures';

test.describe('Settings', () => {
  test('should load settings page', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: 'Настройки' })).toBeVisible();
    await expect(page.getByText('Управление параметрами сканирования')).toBeVisible();
  });
  
  test('should update scan interval', async ({ page }) => {
    await page.goto('/settings');
    
    // Change interval using slider
    const slider = page.getByRole('slider');
    await slider.click();
    
    // Save changes
    await page.getByRole('button', { name: 'Сохранить изменения' }).click();
    
    // Wait for success (query invalidated)
    await page.waitForTimeout(1000);
  });
  
  test('should change city', async ({ page }) => {
    await page.goto('/settings');
    
    // Select different city from dropdown
    await page.getByRole('combobox').click();
    await page.getByRole('option', { name: 'Гродно' }).click();
    
    // Wait for city to update
    await expect(page.getByText('Текущий город: Гродно')).toBeVisible();
  });
});
