import React from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/shared/ui/tooltip';
import { cn } from '@/shared/lib/utils';

interface BreakdownItem {
  score: number;
  weight: number;
  weighted: number;
}

interface DealScoreTooltipProps {
  dealScore: number;
  dealLabel: string;
  breakdown?: {
    price_score?: BreakdownItem;
    trend_score?: BreakdownItem;
    liquidity_score?: BreakdownItem;
    freshness_score?: BreakdownItem;
    floor_score?: BreakdownItem;
    bonus_score?: BreakdownItem;
  };
  children: React.ReactNode;
  className?: string;
}

const factorLabels: Record<string, string> = {
  price_score: 'Цена ниже рынка',
  trend_score: 'Падение цены',
  liquidity_score: 'Дней на рынке',
  freshness_score: 'Свежее',
  floor_score: 'Этаж',
  bonus_score: 'Бонусы',
};

/**
 * DealScoreTooltip - tooltip с детализацией Deal Score по факторам
 *
 * Показывает breakdown каждого фактора с прогресс-барами:
 * - Цена ниже рынка
 * - Падение цены
 * - Дней на рынке
 * - Свежее объявление
 * - Этаж
 * - Бонусы (фото, площадь)
 */
export const DealScoreTooltip: React.FC<DealScoreTooltipProps> = ({
  dealScore,
  dealLabel,
  breakdown,
  children,
  className,
}) => {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>{children}</TooltipTrigger>
        <TooltipContent
          side="top"
          sideOffset={8}
          className={cn('max-w-xs p-3 bg-gray-900 border-gray-700', className)}
        >
          <div className="space-y-2">
            {/* Header */}
            <div className="text-center">
              <div className="text-base font-bold text-white">
                Deal Score: {dealScore}/100 {dealLabel}
              </div>
            </div>

            <div className="border-t border-gray-600" />

            {/* Breakdown */}
            {breakdown && (
              <div className="space-y-1.5">
                {Object.entries(breakdown).map(([key, value]) => {
                  if (!value) return null;
                  const label = factorLabels[key] || key;
                  const color = getFactorColor(value.score);

                  return (
                    <div key={key} className="flex items-center justify-between text-xs">
                      <span className="text-gray-300">{label}:</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={cn('h-full rounded-full transition-all', color)}
                            style={{ width: `${Math.min(100, Math.max(0, value.score))}%` }}
                          />
                        </div>
                        <span className="text-white font-mono w-10 text-right text-xs">
                          +{value.weighted.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {!breakdown && (
              <div className="text-xs text-gray-400 text-center">
                Детализация недоступна
              </div>
            )}

            <div className="border-t border-gray-600" />

            {/* Total */}
            <div className="text-center text-sm font-semibold text-white">
              Итого: {dealScore}/100
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

function getFactorColor(score: number): string {
  if (score >= 70) return 'bg-green-500';
  if (score >= 40) return 'bg-yellow-500';
  return 'bg-red-500';
}
