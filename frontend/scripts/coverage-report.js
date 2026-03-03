#!/usr/bin/env node

/**
 * Скрипт для генерации отчёта о покрытии кода (coverage)
 * 
 * Использование:
 *   npm run test:e2e:coverage
 */

import { execSync } from 'child_process';
import { existsSync, mkdirSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const coverageDir = path.join(__dirname, 'playwright-report', 'coverage');

// Создаём директорию для отчётов если не существует
if (!existsSync(coverageDir)) {
  mkdirSync(coverageDir, { recursive: true });
  console.log(`✅ Создана директория для coverage отчётов: ${coverageDir}`);
}

console.log('📊 Запуск тестов с покрытием...\n');

try {
  // Запускаем тесты
  execSync('npx playwright test', {
    stdio: 'inherit',
    env: {
      ...process.env,
      NODE_ENV: 'test',
    },
  });

  console.log('\n✅ Тесты завершены!');
  console.log('\n📈 Отчёты о покрытии:');
  console.log(`   HTML: ${path.join(coverageDir, 'index.html')}`);
  console.log(`   LCOV: ${path.join(coverageDir, 'lcov.info')}`);
  console.log('\n👉 Для просмотра отчёта выполните:');
  console.log('   npx playwright show-report\n');
} catch (error) {
  console.error('❌ Ошибка при запуске тестов:', error.message);
  process.exit(1);
}
