'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { CITIES } from '@/shared/config';

interface ChangeCityProps {
  value: string;
  onChange: (city: string) => void;
}

export function ChangeCity({ value, onChange }: ChangeCityProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger>
        <SelectValue placeholder="Выберите город" />
      </SelectTrigger>
      <SelectContent>
        {Object.entries(CITIES).map(([code, name]) => (
          <SelectItem key={code} value={code}>
            {name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
