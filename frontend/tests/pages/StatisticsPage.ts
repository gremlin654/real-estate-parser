import { Page, Locator } from '@playwright/test';

export class StatisticsPage {
  readonly page: Page;
  readonly header: Locator;
  readonly subheader: Locator;
  readonly citySelect: Locator;
  readonly periodSelect: Locator;
  readonly tabsList: Locator;
  readonly oneRoomTab: Locator;
  readonly twoRoomTab: Locator;
  readonly threeRoomTab: Locator;
  readonly fourRoomTab: Locator;
  readonly chartCard: Locator;
  readonly chartTitle: Locator;
  readonly chartDescription: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.getByText('Статистика цен');
    this.subheader = page.getByText('Средние цены на квартиры по месяцам в USD');
    this.citySelect = page.getByLabel('Выберите город');
    this.periodSelect = page.getByLabel('Период');
    this.tabsList = page.getByRole('tablist');
    this.oneRoomTab = page.getByRole('tab', { name: '1-комнатные' });
    this.twoRoomTab = page.getByRole('tab', { name: '2-комнатные' });
    this.threeRoomTab = page.getByRole('tab', { name: '3-комнатные' });
    this.fourRoomTab = page.getByRole('tab', { name: '4-комнатные' });
    this.chartCard = page.locator('canvas').first();
    this.chartTitle = page.getByText(/-комнатные квартиры/);
    this.chartDescription = page.getByText('Средняя цена в USD по месяцам');
  }

  async goto() {
    await this.page.goto('/statistics');
  }

  async waitForLoad() {
    await this.header.waitFor({ state: 'visible', timeout: 10000 });
  }

  async selectCity(cityName: string) {
    await this.citySelect.click();
    await this.page.getByText(cityName).click();
  }

  async selectPeriod(period: string) {
    await this.periodSelect.click();
    await this.page.getByText(period).click();
  }

  async selectRoomTab(rooms: string) {
    const tab = this.page.getByRole('tab', { name: new RegExp(`${rooms}-комнатные`) });
    await tab.click();
  }

  async getActiveTab(): Promise<string | null> {
    const activeTab = this.page.locator('[role="tab"][data-state="active"]');
    return await activeTab.textContent();
  }

  async isChartVisible(): Promise<boolean> {
    return await this.chartCard.isVisible();
  }
}
