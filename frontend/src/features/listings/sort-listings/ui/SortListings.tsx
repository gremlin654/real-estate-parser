'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

interface SortListingsProps {
  value: string;
  onChange: (sort: string) => void;
}

export function SortListings({ value, onChange }: SortListingsProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Сортировка" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="newest">Сначала новые</SelectItem>
        <SelectItem value="oldest">Сначала старые</SelectItem>
        <SelectItem value="price_asc">Цена: по возрастанию</SelectItem>
        <SelectItem value="price_desc">Цена: по убыванию</SelectItem>
      </SelectContent>
    </Select>
  );
}
