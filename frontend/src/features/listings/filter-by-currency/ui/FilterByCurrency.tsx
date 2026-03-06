'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

interface FilterByCurrencyProps {
  value: 'USD' | 'BYN';
  onChange: (value: 'USD' | 'BYN') => void;
}

export function FilterByCurrency({ value, onChange }: FilterByCurrencyProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[100px] h-9">
        <SelectValue placeholder="Валюта" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="USD">USD</SelectItem>
        <SelectItem value="BYN">BYN</SelectItem>
      </SelectContent>
    </Select>
  );
}
