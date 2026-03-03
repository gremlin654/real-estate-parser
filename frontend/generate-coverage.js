#!/usr/bin/env node
import { CoverageReport } from 'monocart-coverage-reports';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function generateCoverageReport() {
  console.log('Generating Playwright coverage report...');
  
  const mcr = new CoverageReport({
    name: 'Kufar Monitor - Playwright Coverage',
    outputDir: path.join(__dirname, 'playwright-report/coverage'),
    reports: [
      ['v8'],
      ['html'],
      ['text-summary'],
    ],
    // Не фильтруем - показываем все данные
    entryFilter: () => true,
  });

  // Читаем кэш coverage данных из monocart-report
  const cacheDir = path.join(__dirname, 'monocart-report/coverage/.cache');
  const outputDir = path.join(__dirname, 'playwright-report/coverage');
  
  // Создаём директорию для отчёта если не существует
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  if (!fs.existsSync(cacheDir)) {
    console.log('No coverage cache found at', cacheDir);
    return;
  }
  
  const files = fs.readdirSync(cacheDir);
  const coverageFiles = files.filter(f => f.startsWith('coverage-') && f.endsWith('.json'));
  
  console.log(`Found ${coverageFiles.length} coverage files`);
  
  for (const file of coverageFiles) {
    const content = fs.readFileSync(path.join(cacheDir, file), 'utf-8');
    const data = JSON.parse(content);
    
    // Добавляем только data массив (V8 формат)
    if (data.data && Array.isArray(data.data)) {
      await mcr.add(data.data);
    }
  }
  
  await mcr.generate();
  console.log('✅ Coverage report generated at playwright-report/coverage/index.html');
}

generateCoverageReport().catch(console.error);
