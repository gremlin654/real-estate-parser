import type { ScanProgress } from '@/shared/types';

/**
 * Рассчитывает общий прогресс сканирования в процентах (0-100)
 * на основе текущей стадии и метрик.
 */
export function calculateProgress(scan: Partial<ScanProgress>): number {
  const { stage, pages_scraped, listings_fetched, listings_processed } = scan;

  if (!stage) return 0;

  switch (stage) {
    case 'starting':
      return 0;
    case 'marking_deleted':
      return 2;
    case 'fetching':
      // 0-50%: прогресс на основе количества страниц (ожидаем максимум ~500)
      return Math.min(50, ((pages_scraped || 0) / 500) * 50);
    case 'parsing':
      // 50-80%: прогресс на основе обработанных объявлений
      return 50 + Math.min(30, ((listings_fetched || 0) / 1500) * 30);
    case 'upserting':
      // 80-100%: прогресс на основе сохранённых объявлений
      return 80 + Math.min(20, ((listings_processed || 0) / 1500) * 20);
    case 'marking_deleted_final':
      return 95;
    case 'done':
      return 100;
    case 'error':
      return -1;
    default:
      return 0;
  }
}

/**
 * Возвращает человекочитаемое название стадии сканирования.
 */
export function formatStage(stage: string): string {
  const stages: Record<string, string> = {
    starting: 'Запуск...',
    marking_deleted: '🗑️ Подготовка',
    fetching: '📥 Сканирование страниц',
    parsing: '🔍 Обработка данных',
    upserting: '💾 Сохранение',
    marking_deleted_final: '🗑️ Удаление старых',
    done: '✅ Завершено',
    error: '❌ Ошибка',
  };
  return stages[stage] || stage;
}

/**
 * Форматирует длительность в секундах в человекочитаемый формат.
 */
export function formatDuration(seconds: number): string {
  if (seconds < 0) return '—';
  if (seconds < 60) return `${seconds} сек`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins} мин ${secs} сек`;
}

/**
 * Возвращает цвет прогресс-бара в зависимости от стадии.
 */
export function getStageColor(stage: string): string {
  const colors: Record<string, string> = {
    starting: 'bg-gray-500',
    marking_deleted: 'bg-gray-500',
    fetching: 'bg-blue-500',
    parsing: 'bg-violet-500',
    upserting: 'bg-emerald-500',
    marking_deleted_final: 'bg-gray-500',
    done: 'bg-green-500',
    error: 'bg-red-500',
  };
  return colors[stage] || 'bg-gray-500';
}

/**
 * Возвращает градиент для прогресс-бара в зависимости от стадии.
 */
export function getStageGradient(stage: string): string {
  const gradients: Record<string, string> = {
    starting: 'from-gray-400 to-gray-600',
    marking_deleted: 'from-gray-400 to-gray-600',
    fetching: 'from-blue-500 to-blue-600',
    parsing: 'from-violet-500 to-violet-600',
    upserting: 'from-emerald-500 to-emerald-600',
    marking_deleted_final: 'from-gray-400 to-gray-600',
    done: 'from-green-500 to-green-600',
    error: 'from-red-500 to-red-600',
  };
  return gradients[stage] || 'from-gray-400 to-gray-600';
}

/**
 * Определяет, является ли стадия финальной (сканирование завершено).
 */
export function isStageFinal(stage: string): boolean {
  return stage === 'done' || stage === 'error';
}

/**
 * Определяет, является ли стадия активной (сканирование в процессе).
 */
export function isStageActive(stage: string): boolean {
  return !isStageFinal(stage);
}
