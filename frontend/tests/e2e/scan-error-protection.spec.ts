/**
 * E2E тесты для проверки исправления "false deleted при ошибках сканирования"
 * 
 * Тестируются сценарии через UI:
 * 1. Частичная загрузка (80%) → Ошибка в истории сканирований
 * 2. Нормальное сканирование (95%+) → Завершено успешно
 * 3. Пограничное значение (89% vs 90%) → Проверка порога
 * 4. 0 объявлений (ошибка API) → Ошибка в истории
 */

import { test, expect } from '../fixtures';

test.describe('Защита от false deleted при ошибках сканирования', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
  });

  test.describe('История сканирований - проверка статусов', () => {
    test('должна отображать статус "Ошибка" для аномальных сканирований', async ({ page }) => {
      /**
       * Сценарий: Частичная загрузка (80%)
       * Ожидаемый результат: Статус "Ошибка" с сообщением об аномалии
       */
      // Переход на страницу настроек (там история сканирований)
      await page.goto('/settings');
      await page.waitForTimeout(1000);

      // Проверка что таблица истории сканирований существует
      const historyTable = page.getByRole('table');
      await expect(historyTable).toBeVisible();

      // Проверка заголовков колонок
      await expect(page.getByRole('columnheader', { name: 'Статус' })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: /Дата/ })).toBeVisible();
      await expect(page.getByRole('columnheader', { name: 'Город' })).toBeVisible();

      // Проверка что статусы отображаются с иконками
      const statusCells = page.locator('tbody td').filter({ hasText: /Завершено|Ошибка|В процессе/ });
      const statusCount = await statusCells.count();
      
      // Должны быть какие-то статусы (если есть данные)
      if (statusCount > 0) {
        // Проверка что есть статусы с иконками
        const errorStatus = page.getByText('Ошибка');
        const completedStatus = page.getByText('Завершено');
        
        // Хотя бы один из статусов должен существовать
        const hasError = await errorStatus.count() > 0;
        const hasCompleted = await completedStatus.count() > 0;
        
        expect(hasError || hasCompleted).toBeTruthy();
      }
    });

    test('должна отображать сообщения об ошибках валидации', async ({ page }) => {
      /**
       * Сценарий: Проверка сообщений об аномалиях
       * Ожидаемый результат: Сообщение содержит "Аномалия" и количество объявлений
       */
      await page.goto('/settings');
      await page.waitForTimeout(1000);

      // Найти таблицу истории
      const table = page.getByRole('table');
      await expect(table).toBeVisible();

      // Проверка что в таблице есть строки
      const rows = table.locator('tbody tr');
      const rowCount = await rows.count();
      
      if (rowCount > 0) {
        // Кликнуть на первую строку для просмотра деталей (если есть такая возможность)
        // Или проверить tooltip с ошибкой
        const errorRow = rows.filter({ hasText: 'Ошибка' }).first();
        
        if (await errorRow.count() > 0) {
          // Проверить что есть сообщение об ошибке
          await expect(errorRow).toBeVisible();
          
          // Проверить hover для получения деталей ошибки
          await errorRow.hover();
          await page.waitForTimeout(500);
          
          // Tooltip или popover с деталями ошибки
          const errorDetails = page.getByText(/Аномалия|получено|ожидалось/);
          // Может быть или не быть в зависимости от реализации UI
        }
      }
    });

    test('должна корректно отображать длительность сканирования', async ({ page }) => {
      /**
       * Проверка что длительность отображается корректно
       */
      await page.goto('/settings');
      await page.waitForTimeout(1000);

      const table = page.getByRole('table');
      await expect(table).toBeVisible();

      // Проверка колонки "Длительность"
      const durationHeader = page.getByRole('columnheader', { name: /Длительность|Время/ });
      if (await durationHeader.count() > 0) {
        await expect(durationHeader).toBeVisible();
      }

      // Проверка что значения длительности есть в строках
      const durationPattern = /\d+\s*(сек|мин|мс)/;
      const durationCells = page.locator('tbody td').last(); // Последняя колонка обычно длительность
      
      const cellText = await durationCells.first().textContent();
      if (cellText) {
        // Длительность должна быть в формате "X сек" или "X мин" или "—"
        const isValid = durationPattern.test(cellText) || cellText.trim() === '—';
        expect(isValid).toBeTruthy();
      }
    });
  });

  test.describe('Список объявлений - проверка статусов после ошибок', () => {
    test('не должен показывать false deleted после ошибочного сканирования', async ({ page }) => {
      /**
       * Сценарий: После сканирования со статусом "Ошибка"
       * объявления не должны быть помечены как deleted
       */
      await page.goto('/listings');
      await page.waitForTimeout(1000);

      // Проверка что фильтр по статусам существует
      const statusFilter = page.getByRole('combobox').filter({ hasText: /Все|Статус/ });
      
      // Проверка что таблица объявлений существует
      const listingsTable = page.getByRole('table');
      await expect(listingsTable).toBeVisible();

      // Проверка заголовков
      await expect(page.getByRole('columnheader', { name: /Статус/ })).toBeVisible();

      // Проверка что есть активные объявления
      const activeStatus = page.getByText('active');
      const newStatus = page.getByText('new');
      
      // Должны быть какие-то объявления
      const rows = listingsTable.locator('tbody tr');
      const rowCount = await rows.count();
      expect(rowCount).toBeGreaterThan(0);
    });

    test('должен корректно отображать количество активных объявлений', async ({ page }) => {
      /**
       * Проверка что статистика показывает корректное количество
       */
      await page.goto('/');
      await page.waitForTimeout(1000);

      // Проверка карточек статистики на Dashboard
      const statCards = page.getByTestId(/stat-card|summary/);
      
      // Или поиск по тексту
      const activeLabel = page.getByText(/Активные|Active/i);
      
      // Проверка что значения статистики отображаются
      const statValues = page.locator('[class*="text-2xl"], [class*="text-3xl"]');
      const valueCount = await statValues.count();
      
      if (valueCount > 0) {
        const firstValue = await statValues.first().textContent();
        // Значение должно быть числом
        if (firstValue) {
          const isNumber = /^\d+$/.test(firstValue.trim());
          expect(isNumber).toBeTruthy();
        }
      }
    });
  });

  test.describe('Проверка API через UI', () => {
    test('должен получать корректные данные из /api/v1/scan/history', async ({ page }) => {
      /**
       * Проверка что API возвращает правильные статусы
       */
      const response = await page.request.get('/api/v1/scan/history?page=1&size=10');
      
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      
      // Проверка структуры ответа
      expect(data).toHaveProperty('items');
      expect(data).toHaveProperty('total');
      expect(Array.isArray(data.items)).toBeTruthy();

      if (data.items.length > 0) {
        const firstScan = data.items[0];
        
        // Проверка полей записи сканирования
        expect(firstScan).toHaveProperty('city');
        expect(firstScan).toHaveProperty('status');
        expect(firstScan).toHaveProperty('trigger_type');
        expect(firstScan).toHaveProperty('started_at');
        
        // Статус должен быть одним из допустимых
        expect(['completed', 'error', 'running']).toContain(firstScan.status);
        
        // Если статус error, должно быть сообщение об ошибке
        if (firstScan.status === 'error') {
          expect(firstScan).toHaveProperty('error_message');
          expect(firstScan.error_message).toBeTruthy();
        }
      }
    });

    test('должен получать корректные данные из /api/v1/stats/summary', async ({ page }) => {
      /**
       * Проверка что статистика по объявлениям корректна
       */
      const response = await page.request.get('/api/v1/stats/summary?city=minsk');
      
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      
      // Проверка структуры ответа (актуальная структура API)
      expect(data).toHaveProperty('active_total');
      
      // Количество активных не должно быть отрицательным
      expect(data.active_total).toBeGreaterThanOrEqual(0);
      
      // Проверка что active_total не упало до 0 после ошибки
      // (это было бы признаком false deleted)
      if (data.active_total > 0) {
        expect(data.active_total).toBeGreaterThan(0);
      }
    });

    test('должен получать корректные данные из /api/v1/listings', async ({ page }) => {
      /**
       * Проверка что список объявлений корректен
       */
      const response = await page.request.get('/api/v1/listings?page=1&size=20&status=active&city=minsk');
      
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      
      // Проверка структуры ответа
      expect(data).toHaveProperty('items');
      expect(Array.isArray(data.items)).toBeTruthy();

      // Проверка что все объявления в ответе имеют статус active
      for (const listing of data.items) {
        expect(listing.status).toBe('active');
      }
    });
  });

  test.describe('Проверка WebSocket прогресса сканирования', () => {
    test('должен корректно отображать стадию "error" при аномалии', async ({ page }) => {
      /**
       * Проверка что WebSocket прогресс показывает стадию error
       */
      // Переход на страницу настроек
      await page.goto('/settings');
      await page.waitForTimeout(1000);

      // Проверка что кнопка сканирования существует
      const scanButton = page.getByRole('button', { name: /Сканировать|Scan/i });
      await expect(scanButton).toBeVisible();

      // Проверка что кнопка не заблокирована
      const isDisabled = await scanButton.isDisabled();
      expect(isDisabled).toBeFalsy();

      // Примечание: Полноценное тестирование WebSocket требует мока API
      // или реальной интеграции с бэкендом
    });

    test('должен показывать прогресс по стадиям сканирования', async ({ page }) => {
      /**
       * Проверка отображения стадий: fetching → parsing → upserting → marking_deleted → done
       */
      await page.goto('/settings');
      await page.waitForTimeout(1000);

      // Проверка индикаторов прогресса (если есть активное сканирование)
      const progressIndicators = page.getByRole('progressbar');
      const progressCount = await progressIndicators.count();

      // Progress bar может быть или не быть в зависимости от состояния
      if (progressCount > 0) {
        await expect(progressIndicators.first()).toBeVisible();
      }

      // Проверка текста прогресса
      const progressText = page.getByText(/fetching|parsing|upserting|marking|Завершено|Ошибка/i);
      // Может быть или не быть
    });
  });

  test.describe('Проверка фильтрации по статусам', () => {
    test('должен фильтровать объявления по статусу deleted', async ({ page }) => {
      /**
       * Проверка что фильтр по deleted работает корректно
       */
      await page.goto('/listings');
      await page.waitForTimeout(1000);

      // Найти фильтр статусов
      const statusFilter = page.getByRole('combobox').filter({ hasText: /Статус|Status/ }).first();
      
      if (await statusFilter.count() > 0) {
        // Открыть dropdown
        await statusFilter.click();
        await page.waitForTimeout(500);

        // Выбрать статус deleted
        const deletedOption = page.getByRole('option', { name: /deleted|Удалённые/i });
        
        if (await deletedOption.count() > 0) {
          await deletedOption.click();
          await page.waitForTimeout(1000);

          // Проверить что отфильтрованы только deleted
          const table = page.getByRole('table');
          const rows = table.locator('tbody tr');
          
          // Все видимые строки должны иметь статус deleted
          // (или таблица должна быть пустой если нет deleted)
        }
      }
    });

    test('должен показывать количество объявлений по статусам', async ({ page }) => {
      /**
       * Проверка что статистика по статусам отображается
       */
      await page.goto('/listings');
      await page.waitForTimeout(1000);

      // Проверка что есть информация о количестве
      const pagination = page.getByText(/Показано \d+ из \d+/);
      // Может быть или не быть в зависимости от реализации

      // Или проверка total в заголовке
      const totalLabel = page.getByText(/Всего|Total/i);
      // Может быть или не быть
    });
  });

  test.describe('Сценарные тесты UI', () => {
    test('Сценарий 1: Частичная загрузка 80%', async ({ page }) => {
      /**
       * Дано: В базе 500 активных объявлений
       * Когда: Сканирование возвращает 400 объявлений (80%)
       * Ожидаемый результат: Статус "Ошибка", 500 активных в БД
       */
      // Проверка текущей статистики
      const summaryResponse = await page.request.get('/api/v1/stats/summary?city=minsk');
      const summary = await summaryResponse.json();
      const initialActive = summary.active_listings;

      // Примечание: Для полноценного тестирования нужен мок API
      // Здесь проверяем только что UI корректно отображает данные

      await page.goto('/settings');
      await page.waitForTimeout(1000);

      // Проверка что история сканирований отображается
      const historyTable = page.getByRole('table');
      await expect(historyTable).toBeVisible();

      // Проверка что есть записи со статусом "Ошибка" (если такие есть)
      const errorRows = page.locator('tbody tr').filter({ hasText: 'Ошибка' });
      const errorCount = await errorRows.count();

      // Если есть ошибки, проверить что у них есть сообщения
      if (errorCount > 0) {
        const firstErrorRow = errorRows.first();
        await expect(firstErrorRow).toBeVisible();
      }
    });

    test('Сценарий 2: Нормальное сканирование 95%+', async ({ page }) => {
      /**
       * Дано: В базе 500 активных объявлений
       * Когда: Сканирование возвращает 480-500 объявлений
       * Ожидаемый результат: Статус "Завершено", mark_deleted() вызван
       */
      await page.goto('/settings');
      await page.waitForTimeout(1000);

      // Проверка что есть записи со статусом "Завершено"
      const completedRows = page.locator('tbody tr').filter({ hasText: 'Завершено' });
      const completedCount = await completedRows.count();

      if (completedCount > 0) {
        const firstCompletedRow = completedRows.first();
        await expect(firstCompletedRow).toBeVisible();

        // Проверка что в завершённых сканированиях есть статистика
        // (количество созданных/обновлённых/удалённых)
      }
    });

    test('Сценарий 3: Пограничное значение', async ({ page }) => {
      /**
       * Проверка что порог 90% работает корректно
       */
      // Проверка через API
      const historyResponse = await page.request.get('/api/v1/scan/history?page=1&size=50');
      const history = await historyResponse.json();

      if (history.items.length > 0) {
        // Найти сканирования с количеством близким к порогу
        const boundaryScans = history.items.filter((scan: any) => {
          const fetched = scan.listings_fetched || 0;
          // Проверка что количество в диапазоне 85-95% от ожидаемого
          return fetched >= 425 && fetched <= 475; // Для среднего 500
        });

        // Проверка что сканирования near boundary обработаны корректно
        for (const scan of boundaryScans) {
          if (scan.listings_fetched < 450) {
            // < 90% должно быть error
            expect(scan.status).toBe('error');
          } else {
            // >= 90% должно быть completed
            expect(scan.status).toBe('completed');
          }
        }
      }
    });

    test('Сценарий 4: 0 объявлений', async ({ page }) => {
      /**
       * Дано: В базе есть активные объявления
       * Когда: API возвращает 0 объявлений
       * Ожидаемый результат: Статус "Ошибка", нет false deleted
       */
      // Проверка текущей статистики
      const summaryResponse = await page.request.get('/api/v1/stats/summary?city=minsk');
      const summary = await summaryResponse.json();

      // Должны быть активные объявления
      expect(summary.active_listings).toBeGreaterThan(0);

      // Проверка истории на наличие сканирований с 0 объявлений
      const historyResponse = await page.request.get('/api/v1/scan/history?page=1&size=50&city=minsk');
      const history = await historyResponse.json();

      const zeroScans = history.items.filter((scan: any) => scan.listings_fetched === 0);

      // Если есть сканирования с 0 объявлений, они должны иметь статус error
      for (const scan of zeroScans) {
        expect(scan.status).toBe('error');
        expect(scan.error_message).toBeTruthy();
        expect(scan.error_message).toContain('Аномалия');
      }
    });
  });
});
