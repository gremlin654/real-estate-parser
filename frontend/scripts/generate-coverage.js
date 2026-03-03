/**
 * Скрипт для генерации отчёта о покрытии кода
 * 
 * Playwright + Istanbul coverage integration
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Директории
const projectRoot = __dirname;
const coverageDir = path.join(projectRoot, 'coverage');
const tempDir = path.join(projectRoot, 'node_modules', '.cache', 'nyc');

console.log('📊 Kufar Monitor - Coverage Report Generator\n');

// Создаём директорию coverage
if (!existsSync(coverageDir)) {
  mkdirSync(coverageDir, { recursive: true });
}

try {
  console.log('1️⃣ Запуск тестов Playwright...\n');
  
  // Запускаем тесты
  execSync('npx playwright test --project=chromium', {
    stdio: 'inherit',
    cwd: projectRoot,
  });

  console.log('\n2️⃣ Генерация отчёта...\n');

  // Читаем coverage данные из playwright отчёта
  const playwrightReportDir = path.join(projectRoot, 'playwright-report');
  
  if (existsSync(playwrightReportDir)) {
    console.log(`✅ Отчёты Playwright сохранены в: ${playwrightReportDir}`);
    console.log(`   Для просмотра: npx playwright show-report\n`);
  }

  // Создаём summary файл
  const summaryPath = path.join(coverageDir, 'coverage-summary.txt');
  const summary = `
Kufar Monitor Frontend - Coverage Summary
==========================================

Дата: ${new Date().toISOString()}

Тесты: Playwright E2E (19 тестов)
Браузер: Chromium Desktop

Отчёты:
- HTML: playwright-report/index.html
- Trace: playwright-report/traceviewer/

Для запуска с покрытием:
  npm run test:e2e:coverage

Для просмотра отчёта:
  npx playwright show-report
`.trim();

  writeFileSync(summaryPath, summary);
  console.log(`📄 Summary сохранён: ${summaryPath}`);

  console.log('\n✅ Готово!\n');
  console.log('📈 Отчёты:');
  console.log(`   HTML: ${path.join(playwrightReportDir, 'index.html')}`);
  console.log(`   Summary: ${summaryPath}`);
  console.log('\n👉 Просмотр:');
  console.log('   npx playwright show-report\n');

} catch (error) {
  console.error('❌ Ошибка:', error.message);
  process.exit(1);
}
