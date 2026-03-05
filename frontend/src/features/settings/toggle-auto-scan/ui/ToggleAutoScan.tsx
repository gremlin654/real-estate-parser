'use client';

import { Switch } from '@/shared/ui/switch';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ScanSchedule } from '@/shared/types';
import { toast } from 'sonner';

interface ToggleAutoScanProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

export function ToggleAutoScan({ enabled, onToggle }: ToggleAutoScanProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="space-y-0.5">
        <div className="text-sm font-medium">Автоматическое сканирование</div>
        <div className="text-xs text-muted-foreground">
          {enabled ? 'Включено' : 'Выключено'}
        </div>
      </div>
      <Switch checked={enabled} onCheckedChange={onToggle} />
    </div>
  );
}
