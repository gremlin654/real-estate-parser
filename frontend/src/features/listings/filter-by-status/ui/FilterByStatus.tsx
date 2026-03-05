'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

interface FilterByStatusProps {
  value?: string;
  onChange: (status: string) => void;
}

export function FilterByStatus({ value, onChange }: FilterByStatusProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Все статусы" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Все статусы</SelectItem>
        <SelectItem value="active">Активные</SelectItem>
        <SelectItem value="new">Новые</SelectItem>
        <SelectItem value="updated">Обновленные</SelectItem>
        <SelectItem value="deleted">Удаленные</SelectItem>
        <SelectItem value="archived">Архив</SelectItem>
      </SelectContent>
    </Select>
  );
}
