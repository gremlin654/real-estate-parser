'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

interface FilterByCurrencyProps {
  value: 'USD' | 'BYN';
  onChange: (value: 'USD' | 'BYN') => void;
}

export function FilterByCurrency({ value, onChange }: FilterByCurrencyProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[100px] h-9" data-testid="currency-select">
        <SelectValue placeholder="Валюта" />
      </SelectTrigger>
      <SelectContent data-testid="currency-select-content">
        <SelectItem value="USD" data-testid="currency-option-usd">USD $</SelectItem>
        <SelectItem value="BYN" data-testid="currency-option-byn">Цена BYN</SelectItem>
      </SelectContent>
    </Select>
  );
}
