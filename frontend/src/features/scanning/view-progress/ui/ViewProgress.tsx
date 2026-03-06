'use client';

import { ScanProgressDisplay } from '@/entities/scan';
import { useScanProgressWebSocket } from '@/api/listings';

export function ViewProgress() {
  const { progress } = useScanProgressWebSocket();

  // Показываем прогресс только если сканирование активно
  if (!progress || !progress.is_scanning) {
    return null;
  }

  return <ScanProgressDisplay progress={progress} />;
}
