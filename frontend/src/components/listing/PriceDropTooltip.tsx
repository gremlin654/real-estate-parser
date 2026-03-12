import React from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/shared/ui/tooltip';
import { cn } from '@/shared/lib/utils';

interface PriceDropTooltipProps {
  maxPrice: number;
  minPrice: number;
  currentPrice: number;
  dropPercent: number;
  currency: 'BYN' | 'USD';
  children: React.ReactNode;
  className?: string;
}

/**
 * PriceDropTooltip - tooltip для отображения истории падения цены
 *
 * Показывает:
 * - Максимальную цену
 * - Минимальную цену
 * - Текущую цену
 * - Падение в % и абсолютном значении
 */
export const PriceDropTooltip: React.FC<PriceDropTooltipProps> = ({
  maxPrice,
  minPrice,
  currentPrice,
  dropPercent,
  currency,
  children,
  className,
}) => {
  // Форматирование валюты
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency === 'USD' ? 'USD' : 'BYN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Вычисление абсолютного падения
  const absoluteDrop = maxPrice - currentPrice;

  const content = (
    <div className={cn('space-y-1.5 text-xs text-white', className)}>
      <div className="flex justify-between gap-4">
        <span className="text-white/70">Максимальная цена:</span>
        <span className="font-medium">{formatCurrency(maxPrice)}</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-white/70">Минимальная цена:</span>
        <span className="font-medium">{formatCurrency(minPrice)}</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-white/70">Текущая цена:</span>
        <span className="font-medium">{formatCurrency(currentPrice)}</span>
      </div>
      <div className="flex justify-between gap-4 pt-1 border-t border-white/20">
        <span className="text-white/70">Падение:</span>
        <span className="font-bold text-green-400">
          {dropPercent.toFixed(0)}% ({formatCurrency(absoluteDrop)})
        </span>
      </div>
    </div>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="cursor-help">{children}</span>
        </TooltipTrigger>
        <TooltipContent side="top" sideOffset={8} className="max-w-[280px]">
          {content}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};
