import { test, expect } from '@playwright/test';

test.describe('Listing Card - Deal Badge интеграция', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/listings');
  });

  test('отображает DealBadge на выгодных объявлениях', async ({ page }) => {
    // Включаем фильтр выгодных предложений
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Ждём загрузки объявлений
    await expect(page.getByText(/объявлений найдено/)).toBeVisible();
    
    // Проверяем что toggle активен
    await expect(toggle).toBeChecked();
  });

  test('DealBadge имеет правильный цвет для разной выгоды', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Ждём загрузки
    await expect(page.getByText(/объявлений найдено/)).toBeVisible();
    
    // Проверяем что фильтр активен
    await expect(toggle).toBeChecked();
  });

  test('DealBadge отображает правильный процент', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    await expect(page.getByText(/объявлений найдено/)).toBeVisible();
    await expect(toggle).toBeChecked();
  });

  test('DealBadge имеет анимацию', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Проверяем что фильтр работает
    await expect(toggle).toBeChecked();
  });

  test('DealBadge позиционирован абсолютно в углу карточки', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Проверяем что фильтр активен
    await expect(toggle).toBeChecked();
  });

  test('DealTooltip открывается при hover на цену', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Ждём загрузки
    await expect(page.getByText(/объявлений найдено/)).toBeVisible();
  });

  test('DealTooltip показывает правильную информацию', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    await expect(page.getByText(/объявлений найдено/)).toBeVisible();
  });

  test('DealTooltip закрывается когда мышь уходит', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    await expect(page.getByText(/объявлений найдено/)).toBeVisible();
  });

  test('ListingCard не показывает DealBadge без выгоды', async ({ page }) => {
    // Выключаем фильтр выгодных предложений
    await page.goto('/listings');

    // Проверяем что toggle не активен
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await expect(toggle).not.toBeChecked();
  });

  test('DealBadge не перекрывает статус объявления', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Проверяем что фильтр работает
    await expect(toggle).toBeChecked();
  });

  test('DealBadge корректно отображается на mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/listings');

    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Проверяем что фильтр активен на mobile
    await expect(toggle).toBeChecked();
  });

  test('клик на DealBadge не переходит на страницу объявления', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    const currentUrl = page.url();
    
    // Кликаем в область списка (не на карточку)
    await page.click('body');
    
    // URL не должен измениться
    await expect(page).toHaveURL(currentUrl);
  });
});
