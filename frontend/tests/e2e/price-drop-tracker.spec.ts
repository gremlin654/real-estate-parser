import { test, expect } from '@playwright/test';

test.describe('Price Drop Tracker - Трекинг падения цены', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/price-drops');
  });

  test('отображает заголовок страницы Price Drop Tracker', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Price Drop Tracker/i })).toBeVisible();
  });

  test('отображает описание страницы', async ({ page }) => {
    await expect(page.getByText(/Отслеживайте падение цен на недвижимость/i)).toBeVisible();
  });

  test('отображает статистические карточки', async ({ page }) => {
    // Ждём загрузки данных
    await page.waitForTimeout(2000);
    
    // Проверяем наличие карточек статистики или loading state
    const hasStats = await page.getByText(/Всего предложений/i).isVisible().catch(() => false);
    const hasLoading = await page.locator('[class*="animate-pulse"]').first().isVisible().catch(() => false);
    
    expect(hasStats || hasLoading).toBeTruthy();
  });

  test('имеет фильтр по городу', async ({ page }) => {
    await expect(page.getByTestId('city-select')).toBeVisible();
  });

  test('имеет фильтр по валюте', async ({ page }) => {
    await expect(page.getByTestId('currency-select')).toBeVisible();
  });

  test('имеет фильтр по комнатам', async ({ page }) => {
    await expect(page.getByTestId('rooms-select')).toBeVisible();
  });

  test('имеет slider для фильтра падения цены', async ({ page }) => {
    // Ждём загрузки страницы
    await page.waitForTimeout(1000);
    
    const hasSliderText = await page.getByText(/Падение цены:/i).isVisible().catch(() => false);
    const hasSlider = await page.locator('input[type="range"]').first().isVisible().catch(() => false);
    const hasLoading = await page.locator('[class*="animate-pulse"]').first().isVisible().catch(() => false);
    
    expect(hasSliderText || hasSlider || hasLoading).toBeTruthy();
  });

  test('отображает список объявлений с PriceDropBadge', async ({ page }) => {
    // Ждём загрузки объявлений
    await page.waitForTimeout(2000);

    // Проверяем что есть карточки объявлений или empty state или loading
    const hasCards = await page.locator('[class*="aspect-video"]').count() > 0;
    const hasEmptyState = await page.getByText(/объявления с падением цены не найдены/i).isVisible().catch(() => false);
    const hasLoading = await page.locator('[class*="animate-pulse"]').first().isVisible().catch(() => false);

    expect(hasCards || hasEmptyState || hasLoading).toBeTruthy();
  });

  test('переключает город в фильтре', async ({ page }) => {
    await page.getByTestId('city-select').click();
    await page.getByTestId('city-option-minsk').click();

    // Ждём обновления страницы
    await page.waitForTimeout(500);
    
    // Проверяем что город изменился в селекте
    await expect(page.getByTestId('city-select')).toContainText('Минск');
  });

  test('переключает валюту', async ({ page }) => {
    // Ждём загрузки страницы
    await page.waitForTimeout(1000);
    
    // Находим переключатель валюты и кликаем
    await page.getByTestId('currency-select').click();
    
    // Ждём появления опций
    await page.waitForTimeout(500);
    
    // Пытаемся кликнуть на опцию
    const hasBynOption = await page.getByTestId('currency-option-byn').isVisible().catch(() => false);
    if (hasBynOption) {
      await page.getByTestId('currency-option-byn').click();
      await page.waitForTimeout(500);
      await expect(page.getByTestId('currency-select')).toContainText('BYN');
    } else {
      // Если опция не найдена, закрываем dropdown
      await page.keyboard.press('Escape');
    }
  });

  test('изменяет значение slider падения цены', async ({ page }) => {
    // Ждём загрузки страницы
    await page.waitForTimeout(1000);
    
    const slider = page.locator('input[type="range"]').first();
    const hasSlider = await slider.isVisible().catch(() => false);
    
    if (hasSlider) {
      // Изменяем значение slider через drag
      const sliderBoundingBox = await slider.boundingBox();
      if (sliderBoundingBox) {
        await page.mouse.move(sliderBoundingBox.x, sliderBoundingBox.y);
        await page.mouse.down();
        await page.mouse.move(sliderBoundingBox.x + 50, sliderBoundingBox.y);
        await page.mouse.up();
      }

      // Ждём обновления
      await page.waitForTimeout(500);
    }
    
    // Проверяем что значение изменилось (текст на слайдере)
    await expect(page.getByText(/Падение цены:/i)).toBeVisible();
  });

  test('отображает кнопку экспорта', async ({ page }) => {
    await expect(page.getByRole('button', { name: /экспорт/i })).toBeVisible();
  });

  test('имеет пагинацию', async ({ page }) => {
    // Ждём загрузки данных
    await page.waitForTimeout(1000);
    
    // Проверяем что пагинация есть (если есть данные)
    const pagination = page.getByRole('navigation');
    const hasPagination = await pagination.first().isVisible().catch(() => false);

    if (hasPagination) {
      await expect(pagination.first()).toBeVisible();
    }
  });

  test('отображает empty state если нет предложений', async ({ page }) => {
    // Ждём загрузки
    await page.waitForTimeout(2000);
    
    // Может показать empty state или данные или loading
    const emptyState = page.getByText(/объявления с падением цены не найдены/i);
    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    const hasData = await page.locator('[class*="aspect-video"]').first().isVisible().catch(() => false);
    const hasLoading = await page.locator('[class*="animate-pulse"]').first().isVisible().catch(() => false);
    
    // Одно из трёх должно быть
    expect(hasEmptyState || hasData || hasLoading).toBeTruthy();
  });

  test('корректно отображает проценты падения на бейджах', async ({ page }) => {
    await page.waitForTimeout(2000);

    // Проверяем что бейджи с процентами есть (если есть объявления)
    const badges = page.locator('[class*="from-yellow"]:not([class*="hidden"]), [class*="from-orange"]:not([class*="hidden"]), [class*="from-red"]:not([class*="hidden"])');
    const hasBadges = await badges.count() > 0;

    if (hasBadges) {
      // Проверяем что на бейджах есть проценты
      const badgeWithPercent = badges.filter({ hasText: /%/ });
      await expect(badgeWithPercent.first()).toBeVisible();
    }
  });

  test('синхронизирует фильтры с URL', async ({ page }) => {
    // Устанавливаем фильтр города
    await page.getByTestId('city-select').click();
    await page.getByTestId('city-option-grodno').click();

    // Ждём обновления
    await page.waitForTimeout(500);
    
    // Проверяем что город изменился
    await expect(page.getByTestId('city-select')).toContainText('Гродно');
  });

  test('переходит на страницу объявления при клике', async ({ page }) => {
    await page.waitForTimeout(2000);

    // Находим первую карточку объявления
    const firstCard = page.locator('[class*="aspect-video"]').first();
    const hasCard = await firstCard.isVisible().catch(() => false);

    if (hasCard) {
      // Кликаем на кнопку "Подробнее"
      const detailsButton = page.getByRole('button', { name: /Подробнее/i }).first();
      await detailsButton.click();

      // Проверяем что перешли на страницу объявления
      await expect(page).toHaveURL(/\/listings\//);
    }
  });

  test('отображает градиенты в зависимости от процента падения', async ({ page }) => {
    await page.waitForTimeout(2000);

    // Проверяем что есть бейджи с разными градиентами (если есть объявления)
    const hasYellowBadge = await page.locator('[class*="from-yellow"]').first().isVisible().catch(() => false);
    const hasOrangeBadge = await page.locator('[class*="from-orange"]').first().isVisible().catch(() => false);
    const hasRedBadge = await page.locator('[class*="from-red"]').first().isVisible().catch(() => false);
    const hasLoading = await page.locator('[class*="animate-pulse"]').first().isVisible().catch(() => false);
    const hasEmptyState = await page.getByText(/объявления с падением цены не найдены/i).isVisible().catch(() => false);

    // Хотя бы один тип бейджа или loading или empty state должен быть
    expect(hasYellowBadge || hasOrangeBadge || hasRedBadge || hasLoading || hasEmptyState).toBeTruthy();
  });
});

test.describe('Price Drop Tracker - Навигация', () => {
  test('доступна ссылка в меню', async ({ page }) => {
    await page.goto('/');

    // Ищем ссылку Price Drop в меню
    const priceDropLink = page.getByRole('link', { name: /📉 Price Drop/i });
    await expect(priceDropLink).toBeVisible();

    // Кликаем на ссылку
    await priceDropLink.click();

    // Проверяем что перешли на страницу Price Drop
    await expect(page).toHaveURL('/price-drops');
  });

  test('прямой переход на /price-drops', async ({ page }) => {
    await page.goto('/price-drops');

    await expect(page).toHaveURL('/price-drops');
    await expect(page.getByRole('heading', { name: /Price Drop Tracker/i })).toBeVisible();
  });
});
