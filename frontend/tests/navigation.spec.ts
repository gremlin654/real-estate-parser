import { test, expect } from './fixtures';
import { DashboardPage, ListingsPage, SettingsPage, StatisticsPage } from './pages/index';

test.describe('Kufar Monitor - Navigation', () => {
  test('должна навигировать с Dashboard на Listings', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForLoad();

    // Кликаем на ссылку "Объявления" в боковой панели
    const listingsLink = page.getByRole('link', { name: /Объявления/i }).first();
    await listingsLink.click();

    // Проверяем, что перешли на Listings
    await expect(page).toHaveURL('/listings');
    await expect(page.getByRole('heading', { name: 'Объявления' })).toBeVisible();
  });

  test('должна навигировать с Dashboard на Settings', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForLoad();

    // Кликаем на ссылку "Настройки" в боковой панели
    const settingsLink = page.getByRole('link', { name: /Настройки/i }).first();
    await settingsLink.click();

    // Проверяем, что перешли на Settings
    await expect(page).toHaveURL('/settings');
    await expect(page.getByRole('heading', { name: /Настройки/i })).toBeVisible({ timeout: 15000 });
  });

  test('должна навигировать с Dashboard на Statistics', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForLoad();

    // Кликаем на ссылку "Статистика" в боковой панели
    const statsLink = page.getByRole('link', { name: /Статистика/i }).first();
    await statsLink.click();

    // Проверяем, что перешли на Statistics
    await expect(page).toHaveURL('/statistics');
    await expect(page.getByRole('heading', { name: /Статистика/i })).toBeVisible({ timeout: 15000 });
  });

  test('должна навигировать с Listings на Dashboard', async ({ page }) => {
    const listings = new ListingsPage(page);
    await listings.goto();
    await listings.waitForLoad();

    // Кликаем на ссылку "Панель управления" в боковой панели
    const dashboardLink = page.getByRole('link', { name: /Панель управления/i }).first();
    await dashboardLink.click();

    // Проверяем, что перешли на Dashboard
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Панель управления' })).toBeVisible();
  });

  test('должна навигировать с Settings на Dashboard', async ({ page }) => {
    const settings = new SettingsPage(page);
    await settings.goto();
    await settings.waitForLoad();

    // Кликаем на ссылку "Панель управления" в боковой панели
    const dashboardLink = page.getByRole('link', { name: /Панель управления/i }).first();
    await dashboardLink.click();

    // Проверяем, что перешли на Dashboard
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Панель управления' })).toBeVisible();
  });

  test('должна навигировать с Statistics на Dashboard', async ({ page }) => {
    const statistics = new StatisticsPage(page);
    await statistics.goto();
    await statistics.waitForLoad();

    // Кликаем на ссылку "Панель управления" в боковой панели
    const dashboardLink = page.getByRole('link', { name: /Панель управления/i }).first();
    await dashboardLink.click();

    // Проверяем, что перешли на Dashboard
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Панель управления' })).toBeVisible();
  });

  test('должна навигировать через боковую панель на все страницы', async ({ page }) => {
    // Переходим на Dashboard
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForLoad();

    // Кликаем на "Объявления" в боковой панели (первая найденная ссылка)
    await page.getByRole('link', { name: 'Объявления' }).first().click();
    await expect(page).toHaveURL('/listings');
    await page.waitForLoadState('networkidle');

    // Кликаем на "Статистика" в боковой панели
    await page.getByRole('link', { name: 'Статистика' }).first().click();
    await expect(page).toHaveURL('/statistics');
    await page.waitForLoadState('networkidle');

    // Кликаем на "Настройки" в боковой панели
    await page.getByRole('link', { name: 'Настройки' }).first().click();
    await expect(page).toHaveURL('/settings');
    await page.waitForLoadState('networkidle');

    // Кликаем на "Панель управления" в боковой панели
    await page.getByRole('link', { name: 'Панель управления' }).first().click();
    await expect(page).toHaveURL('/');
  });

  test('должна открывать ListingDetail из Listings', async ({ page }) => {
    const listings = new ListingsPage(page);
    await listings.goto();
    await listings.waitForLoad();
    await page.waitForLoadState('networkidle');

    // Ждём загрузки объявлений
    await page.waitForSelector('a[href^="/listings/"]', { timeout: 30000, state: 'visible' });

    // Кликаем на первое объявление
    const firstListing = page.locator('a[href^="/listings/"]').first();
    await firstListing.click();
    await page.waitForLoadState('networkidle');

    // Проверяем, что перешли на детальную страницу
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/listings\/[\w-]+/);

    // Проверяем, что есть кнопка "Назад"
    const backButton = page.getByRole('button', { name: 'Назад' });
    await expect(backButton).toBeVisible();
  });

  test('должна возвращаться на Listings с ListingDetail', async ({ page }) => {
    const listings = new ListingsPage(page);
    await listings.goto();
    await listings.waitForLoad();
    await page.waitForLoadState('networkidle');

    // Ждём загрузки объявлений
    await page.waitForSelector('a[href^="/listings/"]', { timeout: 30000, state: 'visible' });

    // Кликаем на первое объявление
    const firstListing = page.locator('a[href^="/listings/"]').first();
    await firstListing.click();
    await page.waitForLoadState('networkidle');

    // Кликаем на кнопку "Назад"
    const backButton = page.getByRole('button', { name: 'Назад' });
    await backButton.click();
    await page.waitForLoadState('networkidle');

    // Проверяем, что вернулись на Listings
    await expect(page).toHaveURL('/listings');
  });

  test('должна сохранять состояние навигации при обновлении страницы', async ({ page }) => {
    const listings = new ListingsPage(page);
    await listings.goto();
    await listings.waitForLoad();

    // Обновляем страницу
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Проверяем, что остались на Listings
    await expect(page).toHaveURL('/listings');
    await expect(page.getByRole('heading', { name: 'Объявления' })).toBeVisible();
  });

  test('должна корректно обрабатывать прямой переход на URL', async ({ page }) => {
    // Прямой переход на Listings
    await page.goto('/listings');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL('/listings');

    // Прямой переход на Settings
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL('/settings');

    // Прямой переход на Statistics
    await page.goto('/statistics');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL('/statistics');
  });
});
