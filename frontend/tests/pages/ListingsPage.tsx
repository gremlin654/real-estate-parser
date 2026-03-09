import { Page, Locator } from '@playwright/test';

export class ListingsPage {
  readonly page: Page;
  readonly header: Locator;
  readonly citySelect: Locator;
  readonly statusSelect: Locator;
  readonly currencySelect: Locator;
  readonly sortOrderSelect: Locator;
  readonly minPriceInput: Locator;
  readonly maxPriceInput: Locator;
  readonly roomsFilter: Locator;
  readonly resetButton: Locator;
  readonly scanButton: Locator;
  readonly table: Locator;
  readonly filtersButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.getByRole('heading', { name: 'Объявления' }).first();
    this.citySelect = page.getByLabel('Город').first();
    this.statusSelect = page.getByLabel('Статус').first();
    this.currencySelect = page.getByLabel('Валюта').first();
    this.sortOrderSelect = page.getByLabel('Сортировка').first();
    this.minPriceInput = page.getByPlaceholder('Мин. цена').first();
    this.maxPriceInput = page.getByPlaceholder('Макс. цена').first();
    this.roomsFilter = page.getByRole('button', { name: /Комнаты/i }).first();
    this.resetButton = page.getByRole('button', { name: /Сброс/i }).first();
    this.scanButton = page.getByRole('button', { name: /Сканировать/i }).first();
    this.table = page.locator('table').first();
    this.filtersButton = page.getByRole('button', { name: /Фильтры/i }).first();
  }

  async goto() {
    await this.page.goto('/listings');
  }

  async waitForLoad() {
    await this.header.waitFor({ state: 'visible', timeout: 20000 });
    await this.page.waitForLoadState('networkidle');
  }

  async selectCity(cityName: string) {
    await this.citySelect.click();
    await this.page.getByText(cityName, { exact: true }).first().click();
  }

  async selectStatus(status: string) {
    await this.statusSelect.click();
    await this.page.getByText(status, { exact: true }).first().click();
  }

  async selectCurrency(currency: string) {
    await this.currencySelect.click();
    await this.page.getByText(currency, { exact: true }).first().click();
  }

  async selectSortOrder(order: string) {
    await this.sortOrderSelect.click();
    await this.page.getByText(order, { exact: true }).first().click();
  }

  async setPriceRange(min: string, max: string) {
    await this.minPriceInput.fill(min);
    await this.maxPriceInput.fill(max);
  }

  async selectRooms(rooms: string[]) {
    await this.roomsFilter.click();
    for (const room of rooms) {
      await this.page.getByText(`${room} комната${room === '1' ? '' : 'ы'}`).first().click();
    }
  }

  async resetFilters() {
    await this.resetButton.click();
  }

  async startScan() {
    await this.scanButton.click();
  }
}
