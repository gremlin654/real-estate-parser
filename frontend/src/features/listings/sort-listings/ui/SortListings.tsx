'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

interface SortListingsProps {
  value: string;
  onChange: (sort: string) => void;
}

export function SortListings({ value, onChange }: SortListingsProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[200px]" data-testid="sort-select">
        <SelectValue placeholder="Сортировка" />
      </SelectTrigger>
      <SelectContent data-testid="sort-select-content">
        <SelectItem value="newest" data-testid="sort-option-newest">Сначала новые</SelectItem>
        <SelectItem value="oldest" data-testid="sort-option-oldest">Сначала старые</SelectItem>
        <SelectItem value="price_asc" data-testid="sort-option-asc">Цена ↑</SelectItem>
        <SelectItem value="price_desc" data-testid="sort-option-desc">Цена ↓</SelectItem>
      </SelectContent>
    </Select>
  );
}
