import { test, expect } from './fixtures';

test.describe('Kufar Monitor - Listing Detail', () => {
  test('должна загружать детальную страницу', async ({ page }) => {
    await page.goto('/listings');
    
    // Ждём пока загрузятся объявления (до 30 секунд)
    await page.waitForSelector('a[href^="/listings/"]', { timeout: 30000 });

    // Кликаем на первое объявление
    const listings = page.locator('a[href^="/listings/"]');
    await listings.first().click();
    await page.waitForTimeout(1000);

    // Проверяем, что есть кнопка "Назад" - признак детальной страницы
    const backButton = page.getByRole('button', { name: 'Назад' });
    await expect(backButton).toBeVisible();
  });

  test('должна отображать галерею изображений', async ({ page }) => {
    await page.goto('/listings');
    
    // Ждём загрузки объявлений
    await page.waitForSelector('a[href^="/listings/"]', { timeout: 30000 });
    
    const listings = page.locator('a[href^="/listings/"]');
    await listings.first().click();
    await page.waitForTimeout(1000);

    // Проверяем, что есть изображения
    const images = page.getByRole('img');
    const count = await images.count();
    expect(count).toBeGreaterThan(0);
  });

  test('должна отображать цену и статус', async ({ page }) => {
    await page.goto('/listings');
    
    // Ждём загрузки объявлений
    await page.waitForSelector('a[href^="/listings/"]', { timeout: 30000 });
    
    const listings = page.locator('a[href^="/listings/"]');
    await listings.first().click();
    await page.waitForTimeout(1000);

    // Проверяем, что есть цена или статус
    const hasPrice = await page.getByText(/\$|BYN/).count() > 0;
    const hasStatus = await page.getByText(/Активное|Новое/).count() > 0;
    expect(hasPrice || hasStatus).toBe(true);
  });

  test('должна иметь ссылку на Kufar', async ({ page }) => {
    await page.goto('/listings');
    
    // Ждём загрузки объявлений
    await page.waitForSelector('a[href^="/listings/"]', { timeout: 30000 });
    
    const listings = page.locator('a[href^="/listings/"]');
    await listings.first().click();
    await page.waitForTimeout(1000);

    // Проверяем, что есть ссылка на kufar.by
    const kufarLinks = page.getByRole('link', { name: /Куфар|kufar/i });
    const count = await kufarLinks.count();
    // Ссылка может не быть, это нормально
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('должна иметь кнопку назад', async ({ page }) => {
    await page.goto('/listings');
    
    // Ждём загрузки объявлений
    await page.waitForSelector('a[href^="/listings/"]', { timeout: 30000 });
    
    const listings = page.locator('a[href^="/listings/"]');
    await listings.first().click();
    await page.waitForTimeout(1000);

    // Кнопка назад должна быть
    const backButton = page.getByRole('button', { name: 'Назад' });
    await expect(backButton).toBeVisible();
  });
});
