import { cn } from '@/shared/lib/utils';
import { getStageGradient } from '@/shared/lib/scan-progress';

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
export function ScanningProgressBar({ progress, stage, className }: ScanningProgressBarProps) {
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
            'h-full rounded-full bg-gradient-to-r transition-all duration-500 ease-out',
            gradient,
            isActive && 'animate-pulse'
          )}
          style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
        />
        
        {/* Striped pattern for active state */}
        {isActive && (
          <div className="absolute inset-0 overflow-hidden rounded-full">
            <div
              className={cn(
                'absolute inset-0 opacity-20',
                'bg-[repeating-linear-gradient(45deg,transparent,transparent_10px,rgba(255,255,255,0.3)_10px,rgba(255,255,255,0.3)_20px)]',
                'animate-[shimmer_2s_linear_infinite]'
              )}
            />
          </div>
        )}
      </div>
      
      {/* Progress text */}
      <div className="mt-1 flex justify-between text-xs text-muted-foreground">
        <span>{isError ? 'Ошибка' : isComplete ? 'Завершено' : `${Math.round(progress)}%`}</span>
      </div>
      
      {/* Inline styles for custom animation */}
      <style>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  );
}
