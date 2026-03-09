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
    this.header = page.getByRole('heading', { name: /Статистика/i }).first();
    this.subheader = page.getByText('Средние цены на квартиры по месяцам').first();
    this.citySelect = page.getByLabel('Город').first();
    this.periodSelect = page.getByLabel('Период').first();
    this.tabsList = page.getByRole('tablist').first();
    this.oneRoomTab = page.getByRole('tab', { name: /1-комн/ }).first();
    this.twoRoomTab = page.getByRole('tab', { name: /2-комн/ }).first();
    this.threeRoomTab = page.getByRole('tab', { name: /3-комн/ }).first();
    this.fourRoomTab = page.getByRole('tab', { name: /4-комн/ }).first();
    this.chartCard = page.locator('canvas').first();
    this.chartTitle = page.getByText(/-комнатные квартиры/).first();
    this.chartDescription = page.getByText('Средняя цена в USD по месяцам').first();
  }

  async goto() {
    await this.page.goto('/statistics');
  }

  async waitForLoad() {
    await this.header.waitFor({ state: 'visible', timeout: 20000 });
    await this.page.waitForLoadState('networkidle');
  }

  async selectCity(cityName: string) {
    await this.citySelect.click();
    await this.page.getByText(cityName, { exact: true }).first().click();
  }

  async selectPeriod(period: string) {
    await this.periodSelect.click();
    await this.page.getByText(period, { exact: true }).first().click();
  }

  async selectRoomTab(rooms: string) {
    const tab = this.page.getByRole('tab', { name: new RegExp(`${rooms}-комнатные`) }).first();
    await tab.click();
  }

  async getActiveTab(): Promise<string | null> {
    const activeTab = this.page.locator('[role="tab"][data-state="active"]').first();
    return await activeTab.textContent();
  }

  async isChartVisible(): Promise<boolean> {
    return await this.chartCard.isVisible();
  }
}
