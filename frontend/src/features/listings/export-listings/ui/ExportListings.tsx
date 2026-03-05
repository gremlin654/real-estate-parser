'use client';

import { Button } from '@/shared/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu';
import { Download } from 'lucide-react';

interface ExportListingsProps {
  city?: string;
  status?: string;
  priceFrom?: number | null;
  priceTo?: number | null;
  rooms?: number[];
}

export function ExportListings({ city, status, priceFrom, priceTo, rooms }: ExportListingsProps) {
  const buildUrl = (format: string) => {
    const params = new URLSearchParams();
    params.set('format', format);
    if (city) params.set('city', city);
    if (status) params.set('status', status);
    if (priceFrom) params.set('price_from', String(priceFrom));
    if (priceTo) params.set('price_to', String(priceTo));
    if (rooms?.length) {
      rooms.forEach((r) => params.append('rooms', String(r)));
    }
    return `/api/v1/export/listings?${params}`;
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" />
          Экспорт
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem asChild>
          <a href={buildUrl('csv')} download>
            CSV
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a href={buildUrl('xlsx')} download>
            XLSX
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a href={buildUrl('json')} download>
            JSON
          </a>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
