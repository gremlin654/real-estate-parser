import { test, expect } from './fixtures';
import { StatisticsPage } from './pages/index';

test.describe('Kufar Monitor - Statistics', () => {
  let statisticsPage: StatisticsPage;

  test.beforeEach(async ({ page }) => {
    statisticsPage = new StatisticsPage(page);
    await statisticsPage.goto();
    await statisticsPage.waitForLoad();
  });

  test('должна загружать страницу статистики', async ({ page }) => {
    await expect(page).toHaveURL('/statistics');
    await expect(statisticsPage.header).toBeVisible();
  });

  test('должна отображать заголовок и описание', async ({ page }) => {
    await expect(statisticsPage.header).toBeVisible();
    await expect(statisticsPage.subheader).toBeVisible();
  });

  test('должна отображать селектор города', async ({ page }) => {
    await expect(statisticsPage.citySelect).toBeVisible();
  });

  test('должна отображать селектор периода', async ({ page }) => {
    await expect(statisticsPage.periodSelect).toBeVisible();
  });

  test('должна отображать все табы комнат', async ({ page }) => {
    await expect(statisticsPage.oneRoomTab).toBeVisible();
    await expect(statisticsPage.twoRoomTab).toBeVisible();
    await expect(statisticsPage.threeRoomTab).toBeVisible();
    await expect(statisticsPage.fourRoomTab).toBeVisible();
  });

  test('должна переключать табы комнат', async ({ page }) => {
    // Кликаем на 2-комнатные
    await statisticsPage.twoRoomTab.click();
    await expect(statisticsPage.twoRoomTab).toHaveAttribute('data-state', 'active');

    // Кликаем на 3-комнатные
    await statisticsPage.threeRoomTab.click();
    await expect(statisticsPage.threeRoomTab).toHaveAttribute('data-state', 'active');
  });

  test('должна отображать график для выбранного таба', async ({ page }) => {
    // Проверяем, что график виден
    const chartVisible = await statisticsPage.isChartVisible();
    expect(chartVisible).toBe(true);
  });

  test('должна отображать карточку с графиком', async ({ page }) => {
    await expect(statisticsPage.chartCard).toBeVisible();
  });

  test('должна отображать заголовок графика', async ({ page }) => {
    await expect(statisticsPage.chartTitle).toBeVisible();
  });

  test('должна отображать описание графика', async ({ page }) => {
    await expect(statisticsPage.chartDescription).toBeVisible();
  });

  test('должна позволять выбрать период', async ({ page }) => {
    // Выбираем 6 месяцев
    await statisticsPage.selectPeriod('6 месяцев');
    await expect(page.getByText('6 месяцев')).toBeVisible();

    // Выбираем 24 месяца
    await statisticsPage.selectPeriod('24 месяца');
    await expect(page.getByText('24 месяца')).toBeVisible();
  });

  test('должна позволять выбрать город', async ({ page }) => {
    // Выбираем Гомель
    await statisticsPage.selectCity('Гомель');
    await expect(page.getByText('Гомель')).toBeVisible();

    // Выбираем Брест
    await statisticsPage.selectCity('Брест');
    await expect(page.getByText('Брест')).toBeVisible();
  });

  test('должна отображать все доступные периоды', async ({ page }) => {
    await statisticsPage.periodSelect.click();
    await expect(page.getByText('6 месяцев')).toBeVisible();
    await expect(page.getByText('12 месяцев')).toBeVisible();
    await expect(page.getByText('24 месяца')).toBeVisible();
  });

  test('должна отображать все доступные города', async ({ page }) => {
    await statisticsPage.citySelect.click();
    await expect(page.getByText('Минск')).toBeVisible();
    await expect(page.getByText('Могилёв')).toBeVisible();
    await expect(page.getByText('Гродно')).toBeVisible();
    await expect(page.getByText('Брест')).toBeVisible();
    await expect(page.getByText('Гомель')).toBeVisible();
    await expect(page.getByText('Витебск')).toBeVisible();
  });

  test('должна показывать количество месяцев данных', async ({ page }) => {
    // Проверяем, что есть информация о количестве месяцев
    await expect(page.getByText(/месяцев данных/)).toBeVisible();
  });

  test('должна корректно переключаться между табами и отображать график', async ({ page }) => {
    // Проходим по всем табам
    const tabs = [
      statisticsPage.oneRoomTab,
      statisticsPage.twoRoomTab,
      statisticsPage.threeRoomTab,
      statisticsPage.fourRoomTab,
    ];

    for (const tab of tabs) {
      await tab.click();
      await expect(tab).toHaveAttribute('data-state', 'active');
      
      // Проверяем, что график остаётся видимым
      const chartVisible = await statisticsPage.isChartVisible();
      expect(chartVisible).toBe(true);
    }
  });

  test('должна иметь активный таб по умолчанию', async ({ page }) => {
    const activeTab = await statisticsPage.getActiveTab();
    expect(activeTab).toBeTruthy();
  });
});
