'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { ScanningCityCard } from './ScanningCityCard';
import { useFilterStore } from '@/store/filterStore';
import { cn } from '@/shared/lib/utils';
import { RefreshCw } from 'lucide-react';

const MAX_VISIBLE_CITIES = 3;

/**
 * Виджет активных сканирований.
 * Показывает карточки активных сканирований по городам.
 * Если сканирований > 3, показывает "+N ещё".
 * Если сканирований нет → возвращает null.
 */
export function ActiveScanningWidget() {
  const { getScanningCities } = useFilterStore();
  const scanningCities = getScanningCities();

  // Если нет активных сканирований → ничего не рендерим
  if (scanningCities.length === 0) {
    return null;
  }

  const visibleCities = scanningCities.slice(0, MAX_VISIBLE_CITIES);
  const hiddenCount = scanningCities.length - MAX_VISIBLE_CITIES;

  return (
    <Card className="border-primary/20 shadow-lg animate-in fade-in slide-in-from-top-4 duration-500">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <RefreshCw className="w-5 h-5 text-primary animate-spin-slow" />
            🔄 Активные сканирования
          </CardTitle>
          <span className="text-xs text-muted-foreground bg-primary/10 px-2 py-1 rounded-full">
            {scanningCities.length} {scanningCities.length === 1 ? 'город' : scanningCities.length < 5 ? 'города' : 'городов'}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Видимые карточки */}
          {visibleCities.map((city) => (
            <ScanningCityCard key={city.city} city={city} />
          ))}

          {/* Скрытые карточки */}
          {hiddenCount > 0 && (
            <Card className="flex items-center justify-center min-h-[160px] bg-muted/30 border-dashed">
              <CardContent className="text-center py-6">
                <div className="text-3xl font-bold text-primary">+{hiddenCount}</div>
                <p className="text-sm text-muted-foreground mt-1">
                  {hiddenCount === 1 ? 'ещё город' : hiddenCount < 5 ? 'ещё города' : 'ещё городов'}
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Footer с общей информацией */}
        <div className="mt-4 pt-3 border-t flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Всего активных: {scanningCities.length}
          </span>
          <span className="flex items-center gap-1">
            <RefreshCw className="w-3 h-3 animate-spin" />
            Real-time обновление
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
