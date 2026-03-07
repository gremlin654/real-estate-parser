'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/shared/ui/dialog';
import { Button } from '@/shared/ui/button';
import { ScanningCityCard } from './ScanningCityCard';
import { useFilterStore } from '@/store/filterStore';
import { RefreshCw, TrendingUp } from 'lucide-react';
import { cn } from '@/shared/lib/utils';

interface ScanProgressModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Модальное окно просмотра прогресса сканирований.
 * Показывает список всех активных сканирований в реальном времени.
 */
export function ScanProgressModal({ open, onOpenChange }: ScanProgressModalProps) {
  const scanningCities = useFilterStore((state) => state.getScanningCities());

  const hasActiveScanning = scanningCities.length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <RefreshCw className={cn('w-5 h-5 text-primary', hasActiveScanning && 'animate-spin-slow')} />
            <DialogTitle>
              Прогресс сканирования
            </DialogTitle>
          </div>
          <DialogDescription>
            {hasActiveScanning 
              ? `Активных сканирований: ${scanningCities.length}. Данные обновляются в реальном времени.`
              : 'В данный момент нет активных сканирований.'
            }
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {hasActiveScanning ? (
            <div className="space-y-4">
              {/* Список карточек */}
              <div className="grid gap-4 md:grid-cols-2">
                {scanningCities.map((city) => (
                  <ScanningCityCard key={city.city} city={city} />
                ))}
              </div>

              {/* Общая статистика */}
              <div className="mt-6 p-4 bg-muted/50 rounded-lg border">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-primary" />
                  <h4 className="text-sm font-semibold">Общая статистика</h4>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Городов</div>
                    <div className="text-lg font-semibold">{scanningCities.length}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Всего страниц</div>
                    <div className="text-lg font-semibold">
                      {scanningCities.reduce((sum, c) => sum + (c.pages_scraped || 0), 0)}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Всего объявлений</div>
                    <div className="text-lg font-semibold">
                      {scanningCities.reduce((sum, c) => sum + (c.listings_fetched || 0), 0)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Пустое состояние */
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                <RefreshCw className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Нет активных сканирований</h3>
              <p className="text-sm text-muted-foreground max-w-xs">
                Запустите ручное сканирование города на странице настроек или дождитесь автоматического сканирования
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button onClick={() => onOpenChange(false)} variant="outline">
            Закрыть
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
