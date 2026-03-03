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

  constructor(page: Page) {
    this.page = page;
    this.header = page.getByRole('heading', { name: 'Объявления' });
    this.citySelect = page.getByLabel('Город');
    this.statusSelect = page.getByLabel('Статус');
    this.currencySelect = page.getByLabel('Валюта');
    this.sortOrderSelect = page.getByLabel('Сортировка');
    this.minPriceInput = page.getByPlaceholder('Мин. цена');
    this.maxPriceInput = page.getByPlaceholder('Макс. цена');
    this.roomsFilter = page.getByRole('button', { name: /Комнаты/i });
    this.resetButton = page.getByText('Сброс');
    this.scanButton = page.getByRole('button', { name: /Сканировать/i });
    this.table = page.locator('table');
  }

  async goto() {
    await this.page.goto('/listings');
  }

  async waitForLoad() {
    await this.header.waitFor({ state: 'visible', timeout: 10000 });
  }

  async selectCity(cityName: string) {
    await this.citySelect.click();
    await this.page.getByText(cityName).click();
  }

  async selectStatus(status: string) {
    await this.statusSelect.click();
    await this.page.getByText(status).click();
  }

  async selectCurrency(currency: string) {
    await this.currencySelect.click();
    await this.page.getByText(currency).click();
  }

  async selectSortOrder(order: string) {
    await this.sortOrderSelect.click();
    await this.page.getByText(order).click();
  }

  async setPriceRange(min: string, max: string) {
    await this.minPriceInput.fill(min);
    await this.maxPriceInput.fill(max);
  }

  async selectRooms(rooms: string[]) {
    await this.roomsFilter.click();
    for (const room of rooms) {
      await this.page.getByText(`${room} комната${room === '1' ? '' : 'ы'}`).click();
    }
  }

  async resetFilters() {
    await this.resetButton.click();
  }

  async startScan() {
    await this.scanButton.click();
  }
}
