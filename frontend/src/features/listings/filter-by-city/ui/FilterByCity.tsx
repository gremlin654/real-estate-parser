'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { CITIES } from '@/shared/config';

interface FilterByCityProps {
  value?: string;
  onChange: (city: string) => void;
}

export function FilterByCity({ value, onChange }: FilterByCityProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[180px]" data-testid="city-select">
        <SelectValue placeholder="Все города" />
      </SelectTrigger>
      <SelectContent data-testid="city-select-content">
        <SelectItem value="all" data-testid="city-option-all">Все города</SelectItem>
        {Object.entries(CITIES).map(([code, name]) => (
          <SelectItem key={code} value={code} data-testid={`city-option-${code}`}>
            {name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
