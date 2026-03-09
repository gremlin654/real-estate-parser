'use client';

import type { Listing } from '@/shared/types/listing';
import { Card } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table';
import { Link } from 'react-router-dom';
import { ExternalLink, Home, MapPin } from 'lucide-react';
import { useFilterStore } from '@/store/filterStore';

interface ListingTableProps {
  listings: Listing[];
  isLoading?: boolean;
}

export function ListingTable({ listings, isLoading }: ListingTableProps) {
  const { currency } = useFilterStore();
  if (isLoading) {
    return (
      <Card className="p-0 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[250px] text-center">Изображение</TableHead>
              <TableHead className="text-center">Название</TableHead>
              <TableHead className="text-center">Цена</TableHead>
              <TableHead className="text-center">Цена за м²</TableHead>
              <TableHead className="text-center">Комнаты</TableHead>
              <TableHead className="text-center">Площадь</TableHead>
              <TableHead className="text-center">Статус</TableHead>
              <TableHead className="w-[100px] text-center">Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 10 }).map((_, i) => (
              <TableRow key={i} className="animate-pulse">
                <TableCell>
                  <div className="h-20 w-28 bg-muted rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-48 bg-muted rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-20 bg-muted rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-20 bg-muted rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-8 bg-muted rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-4 w-16 bg-muted rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-6 w-20 bg-muted rounded" />
                </TableCell>
                <TableCell>
                  <div className="h-8 w-20 bg-muted rounded" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    );
  }

  if (!listings || listings.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-muted-foreground">Объявления не найдены</p>
      </Card>
    );
  }

  return (
    <Card className="p-0 overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[250px] text-center">Изображение</TableHead>
            <TableHead className="text-center">Название</TableHead>
            <TableHead className="text-center">Цена</TableHead>
            <TableHead className="text-center">Цена за м²</TableHead>
            <TableHead className="text-center">Комнаты</TableHead>
            <TableHead className="text-center">Площадь</TableHead>
            <TableHead className="text-center">Статус</TableHead>
            <TableHead className="w-[100px] text-center">Действия</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {listings.map((listing) => (
            <TableRow key={listing.id} className="hover:bg-muted/50">
              <TableCell className="text-center">
                <div className="relative h-20 w-28 overflow-hidden rounded-md mx-auto">
                  {listing.images && listing.images.length > 0 ? (
                    <img
                      src={listing.images[0]}
                      alt={listing.title}
                      className="h-full w-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="h-full w-full bg-muted flex items-center justify-center">
                      <Home className="h-8 w-8 text-muted-foreground" />
                    </div>
                  )}
                </div>
              </TableCell>
              <TableCell className="max-w-[300px] text-center">
                <div className="font-medium line-clamp-2">{listing.title}</div>
                {listing.address && (
                  <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1 justify-center">
                    <MapPin className="h-3 w-3" />
                    <span className="line-clamp-1">{listing.address}</span>
                  </div>
                )}
              </TableCell>
              <TableCell className="text-center">
                <div className="font-semibold">
                  {currency === 'USD'
                    ? (listing.price_usd ?? listing.price).toLocaleString()
                    : listing.price.toLocaleString()
                  }
                  <span className="text-sm text-muted-foreground ml-1">
                    {currency}
                  </span>
                </div>
              </TableCell>
              <TableCell className="text-center">
                {formatPricePerM2(listing, currency)}
              </TableCell>
              <TableCell className="text-center">
                <span className="text-sm font-medium">{listing.rooms ?? 0}</span>
              </TableCell>
              <TableCell className="text-center">
                {listing.area ? (
                  <span className="text-sm">{listing.area.toFixed(1)} м²</span>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </TableCell>
              <TableCell className="text-center">
                <StatusBadge status={listing.status} />
              </TableCell>
              <TableCell className="text-center">
                <Button
                  asChild
                  variant="outline"
                  size="sm"
                >
                  <Link to={`/listings/${listing.id}`}>
                    <ExternalLink className="h-4 w-4" />
                  </Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}

function formatPricePerM2(listing: Listing, currency: 'BYN' | 'USD'): string {
  const pricePerM2 = currency === 'USD' 
    ? listing.price_per_m2_usd 
    : listing.price_per_m2_byn;
  
  if (pricePerM2 === null || pricePerM2 === undefined) {
    return '—';
  }
  
  return `${pricePerM2.toLocaleString()} ${currency}/м²`;
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
    new: { label: 'Новое', variant: 'default' },
    active: { label: 'Активное', variant: 'default' },
    updated: { label: 'Обновлено', variant: 'secondary' },
    price_changed_byn: { label: 'Цена BYN', variant: 'secondary' },
    deleted: { label: 'Удалено', variant: 'destructive' },
    archived: { label: 'Архив', variant: 'outline' },
  };

  const config = statusConfig[status] || { label: status, variant: 'outline' as const };

  return <Badge variant={config.variant}>{config.label}</Badge>;
}
