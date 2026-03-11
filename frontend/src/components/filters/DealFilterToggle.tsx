import React from 'react';
import { Switch } from '@/shared/ui/switch';
import { cn } from '@/shared/lib/utils';

interface DealFilterToggleProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  discountThreshold?: number;
  className?: string;
}

/**
 * DealFilterToggle - переключатель фильтра "Только выгодные объявления"
 *
 * Показывает иконку 🔥 и текст "Только выгодные"
 */
export const DealFilterToggle: React.FC<DealFilterToggleProps> = ({
  enabled,
  onToggle,
  discountThreshold = -10,
  className,
}) => {
  const handleToggle = (checked: boolean) => {
    onToggle(checked);
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Switch
        id="deals-only-toggle"
        data-testid="deal-filter-toggle"
        checked={enabled}
        onCheckedChange={handleToggle}
        aria-label="Только выгодные объявления"
      />
      <label
        htmlFor="deals-only-toggle"
        className="flex items-center gap-1.5 text-sm font-medium cursor-pointer select-none"
      >
        <span className="text-lg" role="img" aria-label="fire">
          🔥
        </span>
        <span>
          Только выгодные
        </span>
      </label>
    </div>
  );
};
