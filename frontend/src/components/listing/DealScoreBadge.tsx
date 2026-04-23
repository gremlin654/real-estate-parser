import React from 'react';
import { cn } from '@/shared/lib/utils';

interface DealScoreBadgeProps {
  score: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/**
 * DealScoreBadge - бейдж для отображения Deal Score (оценка выгодности)
 *
 * Цветовая схема (оптимизирована для реальных данных):
 * - 50+: зелёный градиент (🔥 HOT)
 * - 35-50: жёлтый/оранжевый градиент (👍 GOOD)
 * - <35: не показываем (😐 NORMAL)
 *
 * Позиционирование в карточке:
 * - absolute top-2 left-2 (не перекрывать FavoriteButton top-2 right-2)
 * - Если есть DealBadge — сдвинуть: top-2 left-20
 */
export const DealScoreBadge: React.FC<DealScoreBadgeProps> = ({
  score,
  label,
  size = 'md',
  className,
}) => {
  // Не показываем бейдж если score ниже 35
  if (score < 35) {
    return null;
  }

  // Определяем градиент в зависимости от score
  const getGradient = () => {
    if (score >= 50) {
      return 'bg-gradient-to-br from-green-500 to-emerald-600';
    }
    return 'bg-gradient-to-br from-yellow-400 to-orange-500'; // score >= 35
  };

  // Определяем размер
  const sizeClasses = {
    sm: 'text-[11px] px-1.5 py-0.5',
    md: 'text-xs px-2 py-0.5',
    lg: 'text-sm px-2.5 py-1',
  };

  const gradient = getGradient();
  const displayLabel = label || getDefaultLabel(score);

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-semibold shadow-sm',
        'animate-fade-in',
        gradient,
        sizeClasses[size],
        className,
      )}
      role="status"
      aria-label={`Deal Score: ${score} из 100 — ${displayLabel}`}
      title={`Deal Score: ${score}/100`}
    >
      <span>{displayLabel}</span>
      <span className="opacity-90">{score.toFixed(1)}</span>
    </div>
  );
};

function getDefaultLabel(score: number): string {
  if (score >= 50) return '🔥';
  if (score >= 35) return '👍';
  return '😐';
}
