'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

interface FilterByStatusProps {
  value?: string;
  onChange: (status: string) => void;
}

export function FilterByStatus({ value, onChange }: FilterByStatusProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[180px]" data-testid="status-select">
        <SelectValue placeholder="Все статусы" />
      </SelectTrigger>
      <SelectContent data-testid="status-select-content">
        <SelectItem value="all" data-testid="status-option-all">Все статусы</SelectItem>
        <SelectItem value="active" data-testid="status-option-active">Активные</SelectItem>
        <SelectItem value="new" data-testid="status-option-new">Новые</SelectItem>
        <SelectItem value="updated" data-testid="status-option-updated">Обновленные</SelectItem>
        <SelectItem value="deleted" data-testid="status-option-deleted">Удаленные</SelectItem>
        <SelectItem value="archived" data-testid="status-option-archived">Архив</SelectItem>
      </SelectContent>
    </Select>
  );
}
