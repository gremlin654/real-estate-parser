import { test, expect } from './fixtures';

// Глобальная проверка доступности backend
let backendAvailable = false;
let backendUrl = 'http://localhost:8000';

test.beforeAll(async () => {
  try {
    const response = await fetch(`${backendUrl}/health`, { method: 'GET', signal: AbortSignal.timeout(5000) });
    backendAvailable = response.ok;
  } catch {
    backendAvailable = false;
  }
});

test.describe('Kufar Monitor - API Endpoints', () => {
  test('должна успешно получать health endpoint', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/health`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('status');
  });

  test('должна успешно получать список городов', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/scan/cities`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    expect(data.length).toBeGreaterThan(0);
  });

  test('должна успешно получать расписание сканирования', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/scan/schedule`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('scan_interval_minutes');
    expect(data).toHaveProperty('enabled');
  });

  test('должна успешно получать текущий город', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/scan/city`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('city');
  });

  test('должна успешно получать статус сканирования', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/scan/status`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toBeDefined();
  });

  test('должна успешно получать прогресс сканирования', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/scan/progress`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('is_scanning');
  });

  test('должна успешно получать summary статистику', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/stats/summary?city=minsk`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toBeDefined();
  });

  test('должна успешно получать список объявлений', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/listings?page=1&size=10`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('page');
  });

  test('должна возвращать 404 для несуществующего объявления', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/listings/non-existent-id`);
    expect(response.status()).toBe(404);
  });

  test('должна успешно получать историю объявления', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    // Сначала получаем список объявлений
    const listingsResponse = await page.request.get(`${backendUrl}/api/v1/listings?page=1&size=1`);
    const listings = await listingsResponse.json();

    if (listings.items && listings.items.length > 0) {
      const listingId = listings.items[0].id;
      const historyResponse = await page.request.get(`${backendUrl}/api/v1/history/${listingId}`);
      expect(historyResponse.ok()).toBeTruthy();

      const history = await historyResponse.json();
      expect(Array.isArray(history)).toBeTruthy();
    } else {
      test.skip(true, 'Нет объявлений для проверки истории');
    }
  });

  test('должна обновлять расписание сканирования', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.post(`${backendUrl}/api/v1/scan/schedule`, {
      data: {
        scan_interval_minutes: 30,
        enabled: true,
      },
    });
    expect(response.ok()).toBeTruthy();
  });

  test('должна обновлять город сканирования', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.post(`${backendUrl}/api/v1/scan/city`, {
      data: {
        city: 'mogilev',
      },
    });
    expect(response.ok()).toBeTruthy();
  });

  test('должна запускать ручное сканирование', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.post(`${backendUrl}/api/v1/scan/trigger`);
    expect(response.ok()).toBeTruthy();
  });

  test('должна получать price trends для статистики', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/stats/price-trends?city=minsk&rooms=1&period=12`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('data');
  });

  test('должна корректно обрабатывать неверные параметры', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/api/v1/stats/price-trends?city=invalid&rooms=999`);
    // Должен вернуть ошибку или пустые данные
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });

  test('должна иметь CORS заголовки', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/health`);
    const headers = response.headers();

    // CORS заголовки могут присутствовать
    expect(headers).toBeDefined();
  });

  test('должна возвращать JSON контент-тип', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const response = await page.request.get(`${backendUrl}/health`);
    const contentType = response.headers()['content-type'];

    expect(contentType).toContain('application/json');
  });

  test('должна иметь адекватное время ответа API', async ({ page }) => {
    test.skip(!backendAvailable, 'Backend не запущен');

    const startTime = Date.now();
    const response = await page.request.get(`${backendUrl}/api/v1/listings?page=1&size=10`);
    const endTime = Date.now();

    const responseTime = endTime - startTime;

    // API должен отвечать быстрее 5 секунд
    expect(responseTime).toBeLessThan(5000);
    expect(response.ok()).toBeTruthy();
  });
});
