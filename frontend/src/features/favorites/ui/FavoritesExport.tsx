'use client';

import { Button } from '@/shared/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu';
import { Download } from 'lucide-react';
import type { FavoritesFilters } from '@/shared/types';

interface FavoritesExportProps {
  filters?: FavoritesFilters;
  disabled?: boolean;
}

export function FavoritesExport({ filters, disabled }: FavoritesExportProps) {
  const buildUrl = (format: string) => {
    const params = new URLSearchParams();
    params.set('format', format);

    if (filters?.city) params.set('city', filters.city);
    if (filters?.priceFrom) params.set('price_from', String(filters.priceFrom));
    if (filters?.priceTo) params.set('price_to', String(filters.priceTo));
    if (filters?.rooms?.length) {
      filters.rooms.forEach((r) => params.append('rooms', String(r)));
    }

    return `/api/v1/export/favorites?${params}`;
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" disabled={disabled} data-testid="export-button">
          <Download className="w-4 h-4 mr-2" />
          Экспорт
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem asChild>
          <a href={buildUrl('csv')} download data-testid="export-csv">
            CSV
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a href={buildUrl('xlsx')} download data-testid="export-xlsx">
            XLSX
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a href={buildUrl('json')} download data-testid="export-json">
            JSON
          </a>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
