import React from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/shared/ui/tooltip';
import { cn } from '@/shared/lib/utils';

interface DealTooltipProps {
  currentPricePerM2: number;
  avgPricePerM2: number;
  dealPercent: number;
  currency: 'BYN' | 'USD';
  area?: number | null;
  children: React.ReactNode;
  className?: string;
}

/**
 * DealTooltip - tooltip для отображения информации о выгоде объявления
 * 
 * Показывает:
 * - Среднюю цену за м²
 * - Цену этой квартиры за м²
 * - Выгоду в % и абсолютном значении
 */
export const DealTooltip: React.FC<DealTooltipProps> = ({
  currentPricePerM2,
  avgPricePerM2,
  dealPercent,
  currency,
  area,
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

  // Вычисление абсолютной выгоды
  const calculateAbsoluteSavings = () => {
    if (!area) return null;
    const priceDiff = avgPricePerM2 - currentPricePerM2;
    return priceDiff * area;
  };

  const absoluteSavings = calculateAbsoluteSavings();

  const content = (
    <div className={cn('space-y-1.5 text-xs text-white', className)}>
      <div className="flex justify-between gap-4">
        <span className="text-white/70">Средняя цена за м²:</span>
        <span className="font-medium">{formatCurrency(avgPricePerM2)}</span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-white/70">Цена этой квартиры:</span>
        <span className="font-medium">{formatCurrency(currentPricePerM2)}</span>
      </div>
      {absoluteSavings !== null && (
        <div className="flex justify-between gap-4 pt-1 border-t border-white/20">
          <span className="text-white/70">Выгода:</span>
          <span className="font-bold text-green-400">
            {dealPercent.toFixed(0)}% ({formatCurrency(absoluteSavings)} на квартиру {area} м²)
          </span>
        </div>
      )}
      {!absoluteSavings && (
        <div className="flex justify-between gap-4 pt-1 border-t border-white/20">
          <span className="text-white/70">Выгода:</span>
          <span className="font-bold text-green-400">
            {dealPercent.toFixed(0)}%
          </span>
        </div>
      )}
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
