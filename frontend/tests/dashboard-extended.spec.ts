import { test, expect } from './fixtures';
import { DashboardPage } from './pages/DashboardPage';

test.describe('Dashboard', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
  });

  test('displays dashboard header', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Панель управления' })).toBeVisible();
  });

  test('displays stats cards', async ({ page }) => {
    await expect(page.getByText('Новых сегодня').first()).toBeVisible();
    await expect(page.getByText('Удалено сегодня').first()).toBeVisible();
    await expect(page.getByText('Изменилась цена').first()).toBeVisible();
    await expect(page.getByText('Активных всего').first()).toBeVisible();
  });

  test('allows changing city', async ({ page }) => {
    const citySelect = page.getByRole('combobox').first();
    await citySelect.click();
    // Ищем "Могилёв" внутри dropdown селектора города
    const mogilevOption = page.locator('[role="option"]').filter({ hasText: 'Могилёв' }).first();
    await mogilevOption.click();
    await page.waitForTimeout(1000);
    await expect(page.getByText('Город: Могилёв')).toBeVisible();
  });

  test('displays scan history section', async ({ page }) => {
    await expect(page.getByText('История сканирований')).toBeVisible();
  });

  test('displays quick action cards', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Объявления' })).toBeVisible();
    await expect(page.getByText('Сводка')).toBeVisible();
  });

  test('navigates to listings page', async ({ page }) => {
    await dashboardPage.navigateTo('/listings');
    await expect(page).toHaveURL(/.*listings/);
  });
});
