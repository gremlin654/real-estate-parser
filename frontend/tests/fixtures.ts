import { test as base } from '@playwright/test';

export const test = base.extend({
  page: async ({ page }, use) => {
    // Не переходим автоматически на '/', это делается в каждом тесте явно
    await use(page);
  },
});

export { expect } from '@playwright/test';
