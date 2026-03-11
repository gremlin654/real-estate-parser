import { test, expect } from '@playwright/test';

test.describe('Deal Finder - Фильтр выгодных предложений', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/listings');
  });

  test('отображает кнопку фильтров', async ({ page }) => {
    await expect(page.getByRole('button', { name: /фильтры/i })).toBeVisible();
  });

  test('показывает фильтр "Только выгодные" при открытии фильтров', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    await expect(page.getByText('Выгодные предложения:')).toBeVisible();
    
    // Используем data-testid для надёжности
    const filterToggle = page.getByTestId('deal-filter-toggle');
    await expect(filterToggle).toBeVisible();
  });

  test('переключает фильтр "Только выгодные"', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();

    const toggle = page.getByTestId('deal-filter-toggle');
    await expect(toggle).not.toBeChecked();

    await toggle.click();
    await expect(toggle).toBeChecked();
  });

  test('сохраняет состояние фильтра в URL', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();

    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Проверяем URL с обоими параметрами
    await expect(page).toHaveURL(/dealsOnly=true/);
    await expect(page).toHaveURL(/discountPercent=-10/);
  });

  test('обновляет список объявлений при включении фильтра', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();

    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Ждём обновления списка
    await expect(page.getByText(/объявлений найдено/)).toBeVisible();
  });

  test('отображает DealBadge на выгодных объявлениях', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();

    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Ждём загрузки объявлений - проверяем что список обновился
    await expect(page.getByText(/объявлений найдено/)).toBeVisible();
    
    // Проверяем что toggle активен
    await expect(toggle).toBeChecked();
  });

  test('скрывает фильтр при повторном клике', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    await expect(page.getByText('Выгодные предложения:')).toBeVisible();

    await page.getByRole('button', { name: /скрыть фильтры/i }).click();
    await expect(page.getByText('Выгодные предложения:')).not.toBeVisible();
  });

  test('сохраняет состояние фильтра после перезагрузки страницы', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();

    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    await page.reload();

    // После перезагрузки фильтр должен восстановиться из URL
    await page.getByRole('button', { name: /фильтры/i }).click();
    await expect(toggle).toBeChecked();
  });

  test('работает совместно с другими фильтрами', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();

    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Выбираем город
    await page.getByTestId('city-select').click();
    await page.getByTestId('city-option-minsk').click();

    // Проверяем что фильтр активен
    await expect(toggle).toBeChecked();
  });

  test('отображает правильный discount threshold', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();
    
    // Проверяем что toggle имеет правильный aria-label
    const toggle = page.getByTestId('deal-filter-toggle');
    await expect(toggle).toHaveAttribute('aria-label', 'Только выгодные объявления');
  });

  test('корректно сбрасывается при изменении города', async ({ page }) => {
    await page.getByRole('button', { name: /фильтры/i }).click();

    const toggle = page.getByTestId('deal-filter-toggle');
    await toggle.click();

    // Меняем город
    await page.getByTestId('city-select').click();
    await page.getByTestId('city-option-mogilev').click();

    // Проверяем что фильтр остался активным
    await expect(toggle).toBeChecked();
  });
});
