'use client';

import { Button } from '@/shared/ui/button';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface TriggerManualScanProps {
  city: string;
  onSuccess?: () => void;
}

export function TriggerManualScan({ city, onSuccess }: TriggerManualScanProps) {
  const queryClient = useQueryClient();

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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
      queryClient.invalidateQueries({ queryKey: ['scanProgress'] });
      toast.success('Сканирование запущено');
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(`Ошибка: ${error.message}`);
    },
  });

  return (
    <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
      <RefreshCw className={`w-4 h-4 mr-2 ${mutation.isPending ? 'animate-spin' : ''}`} />
      {mutation.isPending ? 'Сканирование...' : 'Сканировать'}
    </Button>
  );
}
