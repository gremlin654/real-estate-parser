import { describe, it, expect } from 'vitest';
import {
  calculateProgress,
  formatStage,
  formatDuration,
  getStageColor,
  getStageGradient,
  isStageFinal,
  isStageActive,
} from './scan-progress';

describe('scan-progress utils', () => {
  describe('calculateProgress', () => {
    it('должен возвращать 0 для стадии starting', () => {
      expect(calculateProgress({ stage: 'starting', pages_scraped: 0, listings_fetched: 0, listings_processed: 0 })).toBe(0);
    });

    it('должен возвращать 2 для стадии marking_deleted', () => {
      expect(calculateProgress({ stage: 'marking_deleted' })).toBe(2);
    });

    it('должен возвращать 0-50% для стадии fetching', () => {
      expect(calculateProgress({ stage: 'fetching', pages_scraped: 0, listings_fetched: 0, listings_processed: 0 })).toBe(0);
      expect(calculateProgress({ stage: 'fetching', pages_scraped: 250, listings_fetched: 0, listings_processed: 0 })).toBe(25);
      expect(calculateProgress({ stage: 'fetching', pages_scraped: 500, listings_fetched: 0, listings_processed: 0 })).toBe(50);
      expect(calculateProgress({ stage: 'fetching', pages_scraped: 1000, listings_fetched: 0, listings_processed: 0 })).toBe(50);
    });

    it('должен возвращать 50-80% для стадии parsing', () => {
      expect(calculateProgress({ stage: 'parsing', pages_scraped: 0, listings_fetched: 0, listings_processed: 0 })).toBe(50);
      expect(calculateProgress({ stage: 'parsing', pages_scraped: 0, listings_fetched: 750, listings_processed: 0 })).toBe(65);
      expect(calculateProgress({ stage: 'parsing', pages_scraped: 0, listings_fetched: 1500, listings_processed: 0 })).toBe(80);
    });

    it('должен возвращать 80-100% для стадии upserting', () => {
      expect(calculateProgress({ stage: 'upserting', pages_scraped: 0, listings_fetched: 0, listings_processed: 0 })).toBe(80);
      expect(calculateProgress({ stage: 'upserting', pages_scraped: 0, listings_fetched: 0, listings_processed: 750 })).toBe(90);
      expect(calculateProgress({ stage: 'upserting', pages_scraped: 0, listings_fetched: 0, listings_processed: 1500 })).toBe(100);
    });

    it('должен возвращать 95 для стадии marking_deleted_final', () => {
      expect(calculateProgress({ stage: 'marking_deleted_final' })).toBe(95);
    });

    it('должен возвращать 100 для стадии done', () => {
      expect(calculateProgress({ stage: 'done' })).toBe(100);
    });

    it('должен возвращать -1 для стадии error', () => {
      expect(calculateProgress({ stage: 'error' })).toBe(-1);
    });

    it('должен возвращать 0 для неизвестной стадии', () => {
      expect(calculateProgress({ stage: 'unknown' })).toBe(0);
    });
  });

  describe('formatStage', () => {
    it('должен форматировать все стадии', () => {
      expect(formatStage('starting')).toBe('Запуск...');
      expect(formatStage('marking_deleted')).toBe('🗑️ Подготовка');
      expect(formatStage('fetching')).toBe('📥 Сканирование страниц');
      expect(formatStage('parsing')).toBe('🔍 Обработка данных');
      expect(formatStage('upserting')).toBe('💾 Сохранение');
      expect(formatStage('marking_deleted_final')).toBe('🗑️ Удаление старых');
      expect(formatStage('done')).toBe('✅ Завершено');
      expect(formatStage('error')).toBe('❌ Ошибка');
    });

    it('должен возвращать стадию как есть для неизвестной стадии', () => {
      expect(formatStage('unknown')).toBe('unknown');
    });
  });

  describe('formatDuration', () => {
    it('должен возвращать "—" для отрицательных секунд', () => {
      expect(formatDuration(-1)).toBe('—');
      expect(formatDuration(-100)).toBe('—');
    });

    it('должен форматировать секунды < 60', () => {
      expect(formatDuration(0)).toBe('0 сек');
      expect(formatDuration(1)).toBe('1 сек');
      expect(formatDuration(45)).toBe('45 сек');
      expect(formatDuration(59)).toBe('59 сек');
    });

    it('должен форматировать минуты и секунды', () => {
      expect(formatDuration(60)).toBe('1 мин 0 сек');
      expect(formatDuration(61)).toBe('1 мин 1 сек');
      expect(formatDuration(90)).toBe('1 мин 30 сек');
      expect(formatDuration(125)).toBe('2 мин 5 сек');
      expect(formatDuration(300)).toBe('5 мин 0 сек');
    });
  });

  describe('getStageColor', () => {
    it('должен возвращать правильные цвета для стадий', () => {
      expect(getStageColor('starting')).toBe('bg-gray-500');
      expect(getStageColor('fetching')).toBe('bg-blue-500');
      expect(getStageColor('parsing')).toBe('bg-violet-500');
      expect(getStageColor('upserting')).toBe('bg-emerald-500');
      expect(getStageColor('done')).toBe('bg-green-500');
      expect(getStageColor('error')).toBe('bg-red-500');
    });
  });

  describe('getStageGradient', () => {
    it('должен возвращать правильные градиенты для стадий', () => {
      expect(getStageGradient('fetching')).toBe('from-blue-500 to-blue-600');
      expect(getStageGradient('parsing')).toBe('from-violet-500 to-violet-600');
      expect(getStageGradient('upserting')).toBe('from-emerald-500 to-emerald-600');
    });
  });

  describe('isStageFinal', () => {
    it('должен возвращать true для финальных стадий', () => {
      expect(isStageFinal('done')).toBe(true);
      expect(isStageFinal('error')).toBe(true);
    });

    it('должен возвращать false для активных стадий', () => {
      expect(isStageFinal('starting')).toBe(false);
      expect(isStageFinal('fetching')).toBe(false);
      expect(isStageFinal('parsing')).toBe(false);
      expect(isStageFinal('upserting')).toBe(false);
    });
  });

  describe('isStageActive', () => {
    it('должен возвращать true для активных стадий', () => {
      expect(isStageActive('starting')).toBe(true);
      expect(isStageActive('fetching')).toBe(true);
      expect(isStageActive('parsing')).toBe(true);
      expect(isStageActive('upserting')).toBe(true);
    });

    it('должен возвращать false для финальных стадий', () => {
      expect(isStageActive('done')).toBe(false);
      expect(isStageActive('error')).toBe(false);
    });
  });
});
