import React from 'react';
import { cn } from '@/shared/lib/utils';

interface DealBadgeProps {
  dealPercent: number;
  className?: string;
}

/**
 * DealBadge - бейдж для отображения выгоды объявления
 * 
 * Цвет зависит от выгоды:
 * - -10% to -15%: оранжевый
 * - -15% to -20%: красно-оранжевый
 * - -20%+: красный
 */
export const DealBadge: React.FC<DealBadgeProps> = ({ dealPercent, className }) => {
  // Не показываем бейдж если выгода меньше 10% (строго меньше -10)
  if (dealPercent >= -10) {
    return null;
  }

  // Определяем градиент в зависимости от выгоды
  const getGradient = () => {
    if (dealPercent > -15) {
      return 'bg-gradient-to-br from-orange-400 to-orange-500'; // -10% to -15%
    }
    if (dealPercent > -20) {
      return 'bg-gradient-to-br from-orange-500 to-red-500'; // -15% to -20%
    }
    return 'bg-gradient-to-br from-red-500 to-red-600'; // -20%+
  };

  const gradient = getGradient();

  return (
    <div
      className={cn(
        'absolute top-2 left-2 z-10',
        'animate-fade-in',
        className
      )}
    >
      <div
        className={cn(
          'inline-flex items-center justify-center',
          'rounded-full px-2 py-1',
          'text-xs font-bold text-white',
          'shadow-lg',
          'min-w-[60px]',
          'text-center',
          gradient,
          // Mobile адаптивность
          'sm:px-2.5 sm:py-1.5 sm:text-sm',
          'md:px-3 md:py-1.5 md:text-base'
        )}
      >
        🔥 {dealPercent.toFixed(0)}%
      </div>
    </div>
  );
};
