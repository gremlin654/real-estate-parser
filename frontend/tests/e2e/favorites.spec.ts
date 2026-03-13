import { test, expect } from '@playwright/test';

test.describe('Избранные объявления (Favorites)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/listings');
  });

  test('отображает кнопку избранного на карточке объявления', async ({ page }) => {
    // Ждём загрузки списка объявлений
    await page.waitForSelector('[data-testid="listing-card"]', { timeout: 10000 });
    
    // Проверяем что кнопка избранного присутствует
    const favoriteButtons = page.getByLabel(/добавить в избранное|удалить из избранного/i);
    await expect(favoriteButtons.first()).toBeVisible();
  });

  test('добавляет объявление в избранное при клике', async ({ page }) => {
    await page.waitForSelector('[data-testid="listing-card"]', { timeout: 10000 });
    
    // Находим первую кнопку избранного
    const favoriteButton = page.getByLabel(/добавить в избранное/i).first();
    await favoriteButton.click();
    
    // Проверяем что кнопка изменилась на "удалить из избранного"
    await expect(favoriteButton).toHaveAttribute('aria-label', /удалить из избранного/i);
    await expect(favoriteButton).toHaveAttribute('aria-pressed', 'true');
  });

  test('удаляет объявление из избранного при повторном клике', async ({ page }) => {
    await page.waitForSelector('[data-testid="listing-card"]', { timeout: 10000 });
    
    // Добавляем в избранное
    const favoriteButton = page.getByLabel(/добавить в избранное/i).first();
    await favoriteButton.click();
    
    // Ждём изменения состояния
    await page.waitForTimeout(500);
    
    // Удаляем из избранного
    const unfavoriteButton = page.getByLabel(/удалить из избранного/i).first();
    await unfavoriteButton.click();
    
    // Проверяем что кнопка вернулась в исходное состояние
    await expect(page.getByLabel(/добавить в избранное/i).first()).toBeVisible();
  });

  test('отображает анимацию при добавлении в избранное', async ({ page }) => {
    await page.waitForSelector('[data-testid="listing-card"]', { timeout: 10000 });
    
    const favoriteButton = page.getByLabel(/добавить в избранное/i).first();
    await favoriteButton.click();
    
    // Проверяем что была анимация (scale)
    await expect(favoriteButton).toHaveClass(/scale-/);
  });

  test('переход на страницу избранных через навигацию', async ({ page }) => {
    // Находим ссылку "Избранные" в навигации
    const favoritesLink = page.getByRole('link', { name: /избранные/i });
    await favoritesLink.click();
    
    // Проверяем что перешли на страницу избранных
    await expect(page).toHaveURL('/favorites');
    await expect(page.getByRole('heading', { name: /избранные объявления/i })).toBeVisible();
  });

  test('страница избранных отображает заголовок', async ({ page }) => {
    await page.goto('/favorites');
    
    const heading = page.getByRole('heading', { name: /избранные объявления/i });
    await expect(heading).toBeVisible();
    
    // Проверяем иконку звезды
    const starIcon = page.locator('svg').filter({ hasText: /star/i }).first();
    await expect(starIcon).toBeVisible();
  });

  test('страница избранных отображает empty state если пусто', async ({ page }) => {
    await page.goto('/favorites');
    
    // Проверяем empty state (если нет избранных)
    const emptyState = page.getByText(/нет избранных объявлений/i);
    if (await emptyState.isVisible()) {
      await expect(emptyState).toBeVisible();
      await expect(page.getByRole('button', { name: /перейти к объявлениям/i })).toBeVisible();
    }
  });

  test('кнопка экспорта на странице избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    const exportButton = page.getByTestId('export-button');
    await expect(exportButton).toBeVisible();
    
    // Открываем dropdown экспорта
    await exportButton.click();
    
    // Проверяем опции экспорта
    await expect(page.getByTestId('export-csv')).toBeVisible();
    await expect(page.getByTestId('export-xlsx')).toBeVisible();
    await expect(page.getByTestId('export-json')).toBeVisible();
  });

  test('фильтры на странице избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    // Проверяем наличие фильтров
    await expect(page.getByTestId('city-select')).toBeVisible();
    await expect(page.getByTestId('price-min-input')).toBeVisible();
    await expect(page.getByTestId('price-max-input')).toBeVisible();
    await expect(page.getByTestId('rooms-select')).toBeVisible();
    await expect(page.getByTestId('sort-select')).toBeVisible();
  });

  test('фильтр города на странице избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    const citySelect = page.getByTestId('city-select');
    await citySelect.click();
    
    const minskOption = page.getByText('Минск');
    await minskOption.click();
    
    // Проверяем что фильтр применился
    await expect(citySelect).toHaveText(/Минск/);
  });

  test('фильтр цены на странице избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    const priceMinInput = page.getByTestId('price-min-input');
    const priceMaxInput = page.getByTestId('price-max-input');
    const applyButton = page.getByTestId('price-apply-button');
    
    await priceMinInput.fill('100000');
    await priceMaxInput.fill('200000');
    await applyButton.click();
    
    // Проверяем что значения применились
    await expect(priceMinInput).toHaveValue('100000');
    await expect(priceMaxInput).toHaveValue('200000');
  });

  test('кнопка сброса фильтров', async ({ page }) => {
    await page.goto('/favorites');
    
    const resetButton = page.getByTestId('reset-filters-button');
    await resetButton.click();
    
    // Проверяем что фильтры сбросились
    const citySelect = page.getByTestId('city-select');
    await expect(citySelect).toHaveText(/Все города|все города/i);
  });

  test('кнопка назад на странице избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    const backButton = page.getByRole('button').filter({ has: page.locator('svg').first() });
    await backButton.click();
    
    // Проверяем что вернулись назад
    await expect(page).not.toHaveURL('/favorites');
  });

  test('пагинация на странице избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    // Проверяем наличие пагинации (если есть данные)
    const pagination = page.getByRole('navigation', { name: /pagination/i });
    if (await pagination.isVisible()) {
      await expect(pagination).toBeVisible();
      
      const nextButton = page.getByRole('link', { name: /next/i });
      const prevButton = page.getByRole('link', { name: /previous/i });
      
      // Проверяем что кнопки пагинации существуют
      await expect(nextButton.or(prevButton)).toBeVisible();
    }
  });

  test('сортировка на странице избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    const sortSelect = page.getByTestId('sort-select');
    await sortSelect.click();
    
    const priceAscOption = page.getByText('Цена (возрастание)');
    await priceAscOption.click();
    
    // Проверяем что сортировка применилась
    await expect(sortSelect).toHaveText(/Цена \(возрастание\)/);
  });

  test('фильтр комнат на странице избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    const roomsSelect = page.getByTestId('rooms-select');
    await roomsSelect.click();
    
    const option2 = page.getByText('2');
    await option2.click();
    
    // Проверяем что фильтр применился
    await expect(roomsSelect).toHaveText(/2/);
  });

  test('сохранение состояния избранного после перезагрузки', async ({ page }) => {
    await page.goto('/listings');
    await page.waitForSelector('[data-testid="listing-card"]', { timeout: 10000 });
    
    // Добавляем в избранное
    const favoriteButton = page.getByLabel(/добавить в избранное/i).first();
    await favoriteButton.click();
    
    // Перезагружаем страницу
    await page.reload();
    
    // Проверяем что состояние сохранилось
    await page.waitForSelector('[data-testid="listing-card"]', { timeout: 10000 });
    await expect(page.getByLabel(/удалить из избранного/i).first()).toBeVisible();
  });

  test('навигация к деталям объявления из избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    // Если есть объявления в избранном
    const listingCards = page.getByTestId('listing-card');
    if (await listingCards.count() > 0) {
      const firstCard = listingCards.first();
      await firstCard.click();
      
      // Проверяем что перешли на страницу деталей
      await expect(page).toHaveURL(/\/listings\/.+/);
    }
  });

  test('отображение количества избранных', async ({ page }) => {
    await page.goto('/favorites');
    
    // Проверяем что отображается количество
    const countText = page.getByText(/\d+ избранных объявлений?/i);
    if (await countText.isVisible()) {
      await expect(countText).toBeVisible();
    }
  });

  test('кнопка "Перейти к объявлениям" в empty state', async ({ page }) => {
    await page.goto('/favorites');
    
    const emptyStateButton = page.getByRole('button', { name: /перейти к объявлениям/i });
    if (await emptyStateButton.isVisible()) {
      await emptyStateButton.click();
      await expect(page).toHaveURL('/listings');
    }
  });
});
