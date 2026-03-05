'use client';

import { Slider } from '@/shared/ui/slider';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ScanSchedule } from '@/shared/types';
import { toast } from 'sonner';

interface ChangeIntervalProps {
  value: number;
  onChange: (value: number) => void;
}

export function ChangeInterval({ value, onChange }: ChangeIntervalProps) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between">
        <span className="text-sm font-medium">Интервал сканирования</span>
        <span className="text-sm text-muted-foreground">{value} мин</span>
      </div>
      <Slider
        value={[value]}
        min={5}
        max={1440}
        step={5}
        onValueChange={(vals) => onChange(vals[0])}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>5 мин</span>
        <span>24 часа</span>
      </div>
    </div>
  );
}
