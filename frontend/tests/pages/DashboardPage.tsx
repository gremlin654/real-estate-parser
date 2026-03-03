import { Page, Locator } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly header: Locator;
  readonly citySelect: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.getByRole('heading', { name: 'Панель управления' });
    this.citySelect = page.getByLabel('Город');
  }

  async goto() {
    await this.page.goto('/');
  }

  async waitForLoad() {
    await this.header.waitFor({ state: 'visible', timeout: 10000 });
  }

  async navigateTo(path: string) {
    await this.page.goto(path);
  }

  async selectCity(cityName: string) {
    await this.citySelect.click();
    await this.page.getByText(cityName).click();
  }
}
