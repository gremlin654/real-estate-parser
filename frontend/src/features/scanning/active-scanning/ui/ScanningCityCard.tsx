import { Card, CardContent } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { ScanningProgressBar } from './ScanningProgressBar';
import { formatStage, formatDuration } from '@/shared/lib/scan-progress';
import type { ScanningCity } from '@/store/filterStore';
import { cn } from '@/shared/lib/utils';
import { Clock, FileText, Database, RefreshCw } from 'lucide-react';
import { memo } from 'react';

interface ScanningCityCardProps {
  city: ScanningCity;
  className?: string;
}

/**
 * Карточка активного сканирования города.
 * Отображает:
 * - Название города и тип сканирования
 * - Прогресс бар (0-100%)
 * - Стадию сканирования
 * - Время elapsed
 * - Метрики (страницы, объявления)
 */
export const ScanningCityCard = memo(function ScanningCityCard({ city, className }: ScanningCityCardProps) {
  const isManual = city.trigger_type === 'manual';
  const isError = city.stage === 'error';
  const isComplete = city.stage === 'done';

  return (
    <Card
      className={cn(
        'relative overflow-hidden transition-all duration-300 hover:shadow-lg',
        isError ? 'border-red-500/50' : 'border-primary/20',
        className
      )}
    >
      {/* Status indicator */}
      <div
        className={cn(
          'absolute top-0 right-0 w-20 h-20 -mr-10 -mt-10 rounded-full opacity-10',
          isError ? 'bg-red-500' : isComplete ? 'bg-green-500' : 'bg-primary'
        )}
      />

      <CardContent className="p-4 space-y-3">
        {/* Header: City name + Type badge */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl" role="img" aria-label="city">
              🏙️
            </span>
            <div>
              <h3 className="font-semibold text-lg leading-none">{city.city_name}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                {isManual ? 'Ручное' : 'Автоматическое'}
              </p>
            </div>
          </div>

          <Badge
            variant={isManual ? 'default' : 'secondary'}
            className={cn(
              'text-xs',
              isError && 'bg-red-500 hover:bg-red-600',
              isComplete && 'bg-green-500 hover:bg-green-600'
            )}
          >
            {isError ? 'Ошибка' : isComplete ? 'Готово' : isManual ? '🔄' : '⏰'}
          </Badge>
        </div>

        {/* Progress bar */}
        <ScanningProgressBar progress={city.progress} stage={city.stage} />

        {/* Stage label */}
        <div className="text-sm text-muted-foreground">
          {formatStage(city.stage)}
        </div>

        {/* Metrics grid */}
        <div className="grid grid-cols-2 gap-2 pt-2 border-t">
          {/* Time elapsed */}
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            <span>{formatDuration(city.elapsed_seconds || 0)}</span>
          </div>

          {/* Pages scraped */}
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <FileText className="w-3.5 h-3.5" />
            <span>📄 {city.pages_scraped || 0}</span>
          </div>

          {/* Listings fetched */}
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Database className="w-3.5 h-3.5" />
            <span>📊 {city.listings_fetched || 0}</span>
          </div>

          {/* Listings processed */}
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <RefreshCw className="w-3.5 h-3.5" />
            <span>💾 {city.listings_processed || 0}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
});
