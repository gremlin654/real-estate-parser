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
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Все города" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Все города</SelectItem>
        {Object.entries(CITIES).map(([code, name]) => (
          <SelectItem key={code} value={code}>
            {name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
