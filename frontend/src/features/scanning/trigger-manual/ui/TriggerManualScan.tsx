'use client';

import { Button } from '@/shared/ui/button';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { useFilterStore } from '@/store/filterStore';
import { useScanProgressWebSocket } from '@/api/listings';

interface TriggerManualScanProps {
  city: string;
  onSuccess?: () => void;
}

export function TriggerManualScan({ city, onSuccess }: TriggerManualScanProps) {
  const queryClient = useQueryClient();
  const { isManualScanning, setManualScanning } = useFilterStore();
  const { progress } = useScanProgressWebSocket();

  const mutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/scan/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city }),
      });
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

  // Кнопка заблокирована если:
  // 1. Мутация в процессе (mutation.isPending)
  // 2. Глобальное флаг сканирования установлен (isManualScanning)
  // 3. WebSocket показывает что сканирование идёт (progress.is_scanning)
  const isDisabled = mutation.isPending || isManualScanning || progress.is_scanning;

  return (
    <Button onClick={() => mutation.mutate()} disabled={isDisabled}>
      <RefreshCw className={`w-4 h-4 mr-2 ${isDisabled ? 'animate-spin' : ''}`} />
      {isDisabled ? 'Сканирование...' : 'Сканировать'}
    </Button>
  );
}
