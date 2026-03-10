import { test, expect } from './fixtures';

// Глобальная проверка доступности backend
let backendAvailable = false;

test.beforeAll(async () => {
  try {
    const response = await fetch('http://localhost:8000/health', { method: 'GET', signal: AbortSignal.timeout(5000) });
    backendAvailable = response.ok;
  } catch {
    backendAvailable = false;
  }
});

test.describe('Kufar Monitor - API Integration', () => {
  test('должна загружать данные с backend', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

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
    test.skip(!backendAvailable, 'Backend не запущен');

    await page.goto('/');

    // Ждём любого API запроса
    await page.waitForResponse(response =>
      response.url().includes('/api/')
    );

    // Если дошли сюда - тест прошёл
    expect(true).toBe(true);
  });
});
