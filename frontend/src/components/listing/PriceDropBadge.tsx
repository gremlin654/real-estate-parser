import React from 'react';
import { cn } from '@/shared/lib/utils';

interface PriceDropBadgeProps {
  dropPercent: number;
  className?: string;
}

/**
 * PriceDropBadge - бейдж для отображения падения цены объявления
 *
 * Цвет зависит от процента падения:
 * - 5% to 10%: жёлтый (from-yellow-400 to-yellow-500)
 * - 10% to 20%: оранжевый (from-orange-400 to-orange-500)
 * - 20%+: красный (from-red-500 to-red-600)
 *
 * Отображается только при падении >= 5%
 */
export const PriceDropBadge: React.FC<PriceDropBadgeProps> = ({ dropPercent, className }) => {
  // Не показываем бейдж если падение меньше 5%
  if (dropPercent < 5) {
    return null;
  }

  // Определяем градиент в зависимости от падения
  const getGradient = () => {
    if (dropPercent < 10) {
      return 'bg-gradient-to-br from-yellow-400 to-yellow-500'; // 5% to 10%
    }
    if (dropPercent < 20) {
      return 'bg-gradient-to-br from-orange-400 to-orange-500'; // 10% to 20%
    }
    return 'bg-gradient-to-br from-red-500 to-red-600'; // 20%+
  };

  const gradient = getGradient();

  return (
    <div
      className={cn(
        'absolute top-2 right-2 z-10',
        'animate-fade-in',
        className
      )}
    >
      <div
        className={cn(
          'inline-flex items-center justify-center gap-1',
          'rounded-full px-2 py-1',
          'text-xs font-bold text-white',
          'shadow-lg',
          'min-w-[60px]',
          'text-center',
          gradient,
          // Mobile адаптивность
          'text-xs sm:px-2.5 sm:py-1.5 sm:text-sm',
          'md:px-3 md:py-1.5 md:text-base'
        )}
      >
        <span>📉</span>
        <span>{dropPercent.toFixed(0)}%</span>
      </div>
    </div>
  );
};
