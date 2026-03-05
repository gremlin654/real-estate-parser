import type { ScanProgress, ScanSchedule } from '@/shared/types';

export interface ScanState {
  isScanning: boolean;
  progress: ScanProgress | null;
  schedule: ScanSchedule | null;
}

export const isScanComplete = (progress: ScanProgress): boolean => {
  return progress.stage === 'done' || progress.stage === 'error';
};

export const getScanStageLabel = (stage: string): string => {
  const labels: Record<string, string> = {
    starting: 'Запуск',
    marking_deleted: 'Подготовка',
    fetching: 'Загрузка данных',
    parsing: 'Обработка',
    upserting: 'Сохранение',
    marking_deleted_final: 'Финализация',
    done: 'Завершено',
    error: 'Ошибка',
  };
  return labels[stage] || stage;
};

export const getScanStageProgress = (stage: string, progress: ScanProgress): number => {
  const stageProgress: Record<string, [number, number]> = {
    starting: [0, 5],
    marking_deleted: [0, 5],
    fetching: [5, 50],
    parsing: [50, 80],
    upserting: [80, 100],
    marking_deleted_final: [95, 100],
    done: [100, 100],
    error: [0, 100],
  };

  const [min, max] = stageProgress[stage] || [0, 100];

  if (stage === 'fetching' && progress.pages_scraped > 0) {
    return min + ((progress.pages_scraped % 20) / 20) * (max - min);
  }

  if (stage === 'parsing' && progress.listings_fetched > 0) {
    return min + ((progress.listings_processed / progress.listings_fetched) || 0) * (max - min);
  }

  if (stage === 'upserting') {
    return min + ((progress.listings_processed / (progress.listings_fetched || 1)) || 0) * (max - min);
  }

  return stage === 'done' ? 100 : min;
};
