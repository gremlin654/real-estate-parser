import { test, expect } from './fixtures';
import { DashboardPage, ListingsPage } from '../pages/index';

test.describe('Kufar Monitor - Mobile Responsive', () => {
  test('должна корректно отображаться на мобильных устройствах', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForLoad();
    
    await expect(dashboard.heading).toBeVisible();
  });

  test('должна отображать Listings на мобильном', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    const listings = new ListingsPage(page);
    await listings.goto();
    await listings.waitForLoad();
    
    await expect(listings.heading).toBeVisible();
  });

  test('должна работать на планшете', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForLoad();
    
    await expect(dashboard.heading).toBeVisible();
  });
});
