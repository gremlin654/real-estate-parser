import { test, expect } from './fixtures';

test.describe('Kufar Monitor - Scanning', () => {
  test('должна иметь кнопку сканирования', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForTimeout(500);
    
    // Ищем кнопку "Сканирование" или "Сканировать"
    const scanButton = page.getByRole('button', { name: /Сканир/ });
    await expect(scanButton).toBeVisible();
  });

  test('должна запускать сканирование по клику', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForTimeout(500);
    
    const scanButton = page.getByRole('button', { name: /Сканир/ });
    await scanButton.click();
    await page.waitForTimeout(2000);
    
    // Проверяем, что появился индикатор "Обновляется"
    const indicator = page.getByText('Обновляется').first();
    await expect(indicator).toBeVisible({ timeout: 5000 });
  });
});
