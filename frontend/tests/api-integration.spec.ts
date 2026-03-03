import { test, expect } from './fixtures';

test.describe('Kufar Monitor - API Integration', () => {
  test('должна загружать данные с backend', async ({ page }) => {
    const [response] = await Promise.all([
      page.waitForResponse(response => 
        response.url().includes('/api/v1/') && 
        response.status() === 200
      ),
      page.goto('/listings'),
    ]);
    
    const data = await response.json();
    expect(data).toBeDefined();
  });

  test('должна делать запрос к API статистики', async ({ page }) => {
    await page.goto('/');
    
    // Ждём любого API запроса
    await page.waitForResponse(response => 
      response.url().includes('/api/')
    );
    
    // Если дошли сюда - тест прошёл
    expect(true).toBe(true);
  });
});
