'use client';

import { Button } from '@/shared/ui/button';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, AlertCircle, Eye } from 'lucide-react';
import { toast } from 'sonner';
import { useFilterStore } from '@/store/filterStore';
import { useScanProgressWebSocket } from '@/api/listings';
import { Alert, AlertDescription } from '@/shared/ui/alert';
import { CITIES } from '@/shared/config';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip';
import { useState } from 'react';
import { ScanProgressModal } from '@/features/scanning/active-scanning/ui/ScanProgressModal';

interface TriggerManualScanProps {
  city: string;
  onSuccess?: () => void;
}

export function TriggerManualScan({ city, onSuccess }: TriggerManualScanProps) {
  const [showProgressModal, setShowProgressModal] = useState(false);
  const queryClient = useQueryClient();
  const { setManualScanning, isCityScanning, getScanningCities } = useFilterStore();
  const scanningCities = getScanningCities();
  const { progress } = useScanProgressWebSocket();

  const mutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/scan/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city }),
      });
      
      // Обработка ошибки 409 Conflict (город уже сканируется)
      if (response.status === 409) {
        const error = await response.json();
        throw new Error(error.detail || 'Город уже сканируется');
      }
      if (!response.ok) throw new Error('Failed to trigger scan');
      return response.json();
    },
    onMutate: () => {
      setManualScanning(true);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      toast.success('Сканирование запущено');
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(`Ошибка: ${error.message}`);
      setManualScanning(false);
    },
  });

  const cityName = CITIES[city as keyof typeof CITIES] || city;
  const isCityCurrentlyScanning = isCityScanning(city);
  const hasAnyScanning = scanningCities.length > 0;

  // Кнопка "Сканировать" заблокирована если:
  // 1. Мутация в процессе (mutation.isPending)
  // 2. Этот конкретный город уже сканируется
  const isScanDisabled = mutation.isPending || isCityCurrentlyScanning;

  // Получаем список других сканирующихся городов для информирования
  const otherScanningCities = scanningCities.filter((s) => s.city !== city);

  return (
    <div className="space-y-2">
      {/* Кнопки управления */}
      <div className="flex gap-2">
        {/* Кнопка "Сканировать" */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={() => mutation.mutate()}
                disabled={isScanDisabled}
                className="flex-1"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isScanDisabled ? 'animate-spin' : ''}`} />
                {isCityCurrentlyScanning ? 'Сканируется...' : 'Сканировать'}
              </Button>
            </TooltipTrigger>
            {isCityCurrentlyScanning && (
              <TooltipContent>
                <p>Сканирование этого города уже выполняется</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>

        {/* Кнопка "Посмотреть прогресс" */}
        <Button
          variant="outline"
          onClick={() => setShowProgressModal(true)}
          disabled={!hasAnyScanning}
          className="flex items-center gap-2"
        >
          <Eye className="w-4 h-4" />
          <span className="hidden sm:inline">Прогресс</span>
        </Button>
      </div>

      {/* Информация о других активных сканированиях */}
      {otherScanningCities.length > 0 && !isCityCurrentlyScanning && (
        <Alert className="mt-2">
          <div className="flex gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <AlertDescription className="text-sm">
              Сканируются: {otherScanningCities.map((s) => s.city_name).join(', ')}
            </AlertDescription>
          </div>
        </Alert>
      )}

      {/* Модальное окно просмотра прогресса */}
      <ScanProgressModal open={showProgressModal} onOpenChange={setShowProgressModal} />
    </div>
  );
}
