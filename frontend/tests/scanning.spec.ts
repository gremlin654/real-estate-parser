import { test, expect } from './fixtures';

test.describe('Kufar Monitor - Scanning', () => {
  test('должна иметь кнопку сканирования', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    // Ищем кнопку "Сканирование" или "Сканировать"
    const scanButton = page.getByRole('button', { name: /Сканир/ }).first();
    await expect(scanButton).toBeVisible({ timeout: 20000 });
  });

  test('должна запускать сканирование по клику', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');

    const scanButton = page.getByRole('button', { name: /Сканир/ }).first();
    await scanButton.click();

    // Проверяем, что появился индикатор "Обновляется"
    const indicator = page.getByText('Обновляется').first();
    await expect(indicator).toBeVisible({ timeout: 20000 });
  });
});
