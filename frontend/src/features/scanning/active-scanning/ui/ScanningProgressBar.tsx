import { cn } from '@/shared/lib/utils';
import { getStageGradient } from '@/shared/lib/scan-progress';
import { memo } from 'react';

interface ScanningProgressBarProps {
  progress: number; // 0-100
  stage: string;
  className?: string;
}

/**
 * Компонент прогресс-бара для отображения прогресса сканирования.
 * Цвет зависит от стадии сканирования.
 * Анимация pulsing для активного состояния.
 */
export const ScanningProgressBar = memo(function ScanningProgressBar({ progress, stage, className }: ScanningProgressBarProps) {
  const gradient = getStageGradient(stage);
  const isError = stage === 'error';
  const isComplete = stage === 'done';
  const isActive = progress >= 0 && progress < 100;

  return (
    <div className={cn('w-full', className)}>
      {/* Progress bar container */}
      <div className="relative h-3 w-full overflow-hidden rounded-full bg-secondary">
        {/* Progress fill */}
        <div
          className={cn(
            'h-full rounded-full bg-gradient-to-r transition-all duration-300 ease-out',
            gradient,
            isActive && 'animate-pulse'
          )}
          style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
        />
      </div>

      {/* Progress text */}
      <div className="mt-1 flex justify-between text-xs text-muted-foreground">
        <span>{isError ? 'Ошибка' : isComplete ? 'Завершено' : `${Math.round(progress)}%`}</span>
      </div>
    </div>
  );
});
