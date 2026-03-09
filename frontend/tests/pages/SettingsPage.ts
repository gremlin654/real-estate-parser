import { Page, Locator } from '@playwright/test';

export class SettingsPage {
  readonly page: Page;
  readonly header: Locator;
  readonly citySelect: Locator;
  readonly autoScanSwitch: Locator;
  readonly intervalInput: Locator;
  readonly saveButton: Locator;
  readonly currentInterval: Locator;
  readonly currentStatus: Locator;
  readonly currentCity: Locator;
  readonly successAlert: Locator;
  readonly errorAlert: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.getByRole('heading', { name: /Настройки/i });
    this.citySelect = page.getByLabel('Город сканирования');
    this.autoScanSwitch = page.getByRole('switch', { name: /Автоматическое сканирование/i });
    this.intervalInput = page.getByLabel('Интервал сканирования');
    this.saveButton = page.getByRole('button', { name: 'Сохранить' });
    this.currentInterval = page.getByText(/Текущий интервал:/);
    this.currentStatus = page.getByText(/Статус:/);
    this.currentCity = page.getByText(/Город:/);
    this.successAlert = page.getByText('Настройки успешно сохранены');
    this.errorAlert = page.locator('[role="alert"]').filter({ hasText: /Ошибка/i });
  }

  async goto() {
    await this.page.goto('/settings');
  }

  async waitForLoad() {
    await this.header.waitFor({ state: 'visible', timeout: 15000 });
    await this.page.waitForLoadState('networkidle');
  }

  async selectCity(cityName: string) {
    await this.citySelect.click();
    await this.page.getByText(cityName, { exact: true }).first().click();
  }

  async toggleAutoScan() {
    await this.autoScanSwitch.click();
  }

  async setInterval(minutes: string) {
    await this.intervalInput.fill(minutes);
  }

  async save() {
    await this.saveButton.click();
  }

  async getCurrentCity(): Promise<string> {
    const text = await this.currentCity.textContent() || '';
    return text.replace('Город:', '').trim();
  }
}
