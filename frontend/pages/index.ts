import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object для главной страницы (Dashboard)
 */
export class DashboardPage {
  readonly page: Page;
  readonly url: string;

  // Элементы навигации
  readonly sidebar: Locator;
  readonly dashboardLink: Locator;
  readonly listingsLink: Locator;
  readonly collapseButton: Locator;

  // Заголовок
  readonly heading: Locator;

  // Элементы статистики
  readonly newTodayCard: Locator;
  readonly deletedTodayCard: Locator;
  readonly priceChangedCard: Locator;
  readonly activeTotalCard: Locator;

  // Счётчики - используем более простые селекторы
  readonly newTodayCount: Locator;
  readonly deletedTodayCount: Locator;
  readonly priceChangedCount: Locator;
  readonly activeTotalCount: Locator;

  // Город
  readonly citySelector: Locator;
  readonly cityDropdown: Locator;

  constructor(page: Page) {
    this.page = page;
    this.url = '/';

    // Заголовок
    this.heading = page.getByRole('heading', { name: 'Панель управления' });

    // Навигация - используем first() для избежания дубликатов
    this.sidebar = page.locator('[data-slot="sidebar"]').first();
    this.dashboardLink = page.getByRole('link', { name: 'Панель управления' }).first();
    this.listingsLink = page.getByRole('link', { name: 'Объявления' }).first();
    this.collapseButton = page.getByRole('button', { name: /Свернуть|Развернуть/ }).first();

    // Карточки статистики - используем точный текст
    this.newTodayCard = page.getByText('Новых сегодня', { exact: true }).first();
    this.deletedTodayCard = page.getByText('Удалено сегодня', { exact: true }).first();
    this.priceChangedCard = page.getByText('Изменилась цена', { exact: true }).first();
    this.activeTotalCard = page.getByText('Активных всего', { exact: true }).first();

    // Счётчики - используем locator с XPath для поиска чисел
    this.newTodayCount = page.locator('xpath=//div[contains(text(), "Новых сегодня")]/following-sibling::div[contains(@class, "text-2xl")]').first();
    this.deletedTodayCount = page.locator('xpath=//div[contains(text(), "Удалено сегодня")]/following-sibling::div[contains(@class, "text-2xl")]').first();
    this.priceChangedCount = page.locator('xpath=//div[contains(text(), "Изменилась цена")]/following-sibling::div[contains(@class, "text-2xl")]').first();
    this.activeTotalCount = page.locator('xpath=//div[contains(text(), "Активных всего")]/following-sibling::div[contains(@class, "text-2xl")]').first();

    // Город - используем комбобокс с точным значением
    this.citySelector = page.locator('[role="combobox"][value="Могилёв"]').or(page.locator('[role="combobox"]').first());
    this.cityDropdown = page.getByRole('listbox').first();
  }

  async goto() {
    await this.page.goto(this.url);
  }

  async waitForLoad() {
    await expect(this.page.getByRole('heading', { name: 'Панель управления' })).toBeVisible();
  }

  async getStats() {
    return {
      newToday: await this.newTodayCount.textContent(),
      deletedToday: await this.deletedTodayCount.textContent(),
      priceChanged: await this.priceChangedCount.textContent(),
      activeTotal: await this.activeTotalCount.textContent(),
    };
  }

  async selectCity(city: string) {
    await this.citySelector.click();
    await this.page.getByRole('option', { name: city }).click();
  }
}

/**
 * Page Object для страницы объявлений (Listings)
 */
export class ListingsPage {
  readonly page: Page;
  readonly url: string;

  // Заголовок
  readonly heading: Locator;
  readonly listingsCount: Locator;

  // Кнопки действий
  readonly scanButton: Locator;
  readonly resetButton: Locator;

  // Фильтры
  readonly cityFilter: Locator;
  readonly statusFilter: Locator;
  readonly currencyFilter: Locator;
  readonly sortFilter: Locator;
  readonly minPriceInput: Locator;
  readonly maxPriceInput: Locator;

  // Таблица
  readonly table: Locator;
  readonly tableRows: Locator;
  readonly firstListing: Locator;

  // Пагинация
  readonly pagination: Locator;
  readonly currentPage: Locator;
  readonly totalPages: Locator;
  readonly prevButton: Locator;
  readonly nextButton: Locator;

  // Сообщения
  readonly noListingsMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.url = '/listings';

    this.heading = page.getByRole('heading', { name: 'Объявления' });
    this.listingsCount = page.getByText(/объявлений/).first();

    this.scanButton = page.getByRole('button', { name: 'Сканировать' });
    this.resetButton = page.getByRole('button', { name: 'Сброс' });

    this.cityFilter = page.getByRole('combobox', { name: /Город/i });
    this.statusFilter = page.getByRole('combobox', { name: /Статус/i });
    this.currencyFilter = page.getByRole('combobox', { name: /BYN|USD/ });
    this.sortFilter = page.getByRole('combobox', { name: /По умолчанию|сортировка/i });
    this.minPriceInput = page.getByRole('spinbutton', { name: 'Мин. цена' });
    this.maxPriceInput = page.getByRole('spinbutton', { name: 'Макс. цена' });

    this.table = page.getByRole('table').or(page.locator('main').locator('div').first());
    this.tableRows = page.getByRole('row').or(page.locator('[role="article"]'));
    this.firstListing = this.tableRows.first();

    this.pagination = page.getByText(/Страница/);
    this.currentPage = page.getByText(/Страница\s+\d+/);
    this.totalPages = page.getByText(/из\s+\d+/);
    this.prevButton = page.getByRole('button', { name: /Назад/ });
    this.nextButton = page.getByRole('button', { name: /Вперёд/ });

    this.noListingsMessage = page.getByText(/Объявлений не найдено/);
  }

  async goto() {
    await this.page.goto(this.url);
  }

  async waitForLoad() {
    await expect(this.heading).toBeVisible();
  }

  async getListingsCount(): Promise<number> {
    const text = await this.listingsCount.textContent();
    const match = text?.match(/(\d+)/);
    return match ? parseInt(match[1]) : 0;
  }

  async selectCity(city: string) {
    await this.cityFilter.click();
    await this.page.getByRole('option', { name: city }).click();
  }

  async selectCurrency(currency: 'BYN' | 'USD') {
    await this.currencyFilter.click();
    await this.page.getByRole('option', { name: currency }).click();
  }

  async selectStatus(status: string) {
    await this.statusFilter.click();
    await this.page.getByRole('option', { name: status }).click();
  }

  async openListing(title: string) {
    await this.page.getByRole('link', { name: title }).click();
  }

  async openFirstListing() {
    await this.firstListing.click();
  }

  async isCurrencyDisplayed(currency: 'BYN' | 'USD'): Promise<boolean> {
    const prices = await this.tableRows.all();
    if (prices.length === 0) return false;
    
    const priceText = await prices[0].textContent();
    return currency === 'USD' ? priceText?.includes('$') ?? false : priceText?.includes('BYN') ?? false;
  }
}

/**
 * Page Object для детальной страницы объявления
 */
export class ListingDetailPage {
  readonly page: Page;

  // Навигация
  readonly backButton: Locator;

  // Галерея
  readonly gallery: Locator;
  readonly galleryImages: Locator;
  readonly prevSlideButton: Locator;
  readonly nextSlideButton: Locator;

  // Информация
  readonly title: Locator;
  readonly status: Locator;
  readonly price: Locator;

  // Параметры
  readonly rooms: Locator;
  readonly area: Locator;
  readonly floor: Locator;
  readonly yearBuilt: Locator;
  readonly address: Locator;

  // Ссылки
  readonly kufarLink: Locator;

  // История
  readonly historySection: Locator;
  readonly historyTimeline: Locator;

  // Даты
  readonly firstSeen: Locator;
  readonly lastSeen: Locator;

  // Техническая информация
  readonly listingId: Locator;
  readonly kufarId: Locator;

  constructor(page: Page) {
    this.page = page;

    this.backButton = page.getByRole('button', { name: 'Назад' });

    this.gallery = page.getByRole('region', { roledescription: 'carousel' });
    this.galleryImages = this.gallery.getByRole('img');
    this.prevSlideButton = this.gallery.getByRole('button', { name: 'Previous' });
    this.nextSlideButton = this.gallery.getByRole('button', { name: 'Next' });

    this.title = page.getByRole('heading').first();
    this.status = page.getByText(/Активное|Новое|Удалено|Обновлено/).first();
    this.price = page.getByText(/\$|BYN/).first();

    this.rooms = page.getByText(/Комнаты/).locator('..');
    this.area = page.getByText(/Площадь/).locator('..');
    this.floor = page.getByText(/Этаж/).locator('..');
    this.yearBuilt = page.getByText(/Год постройки/).locator('..');
    this.address = page.getByText(/Адрес:/).locator('..');

    this.kufarLink = page.getByRole('link', { name: /Открыть на Куфар/ });

    this.historySection = page.getByText(/История/);
    this.historyTimeline = page.getByRole('list').or(page.locator('[role="timeline"]'));

    this.firstSeen = page.getByText(/Первое появление:/).locator('..');
    this.lastSeen = page.getByText(/Последнее появление:/).locator('..');

    this.listingId = page.getByText(/ID:/).locator('..');
    this.kufarId = page.getByText(/Kufar ID:/).locator('..');
  }

  async waitForLoad() {
    await expect(this.title).toBeVisible();
  }

  async getImageCount(): Promise<number> {
    return await this.galleryImages.count();
  }

  async nextImage() {
    await this.nextSlideButton.click();
  }

  async prevImage() {
    await this.prevSlideButton.click();
  }

  async getPrice(): Promise<string> {
    return (await this.price.textContent()) || '';
  }

  async goToKufar() {
    const [newPage] = await Promise.all([
      this.page.waitForEvent('popup'),
      this.kufarLink.click(),
    ]);
    return newPage;
  }
}
