'use client';

import { useState } from 'react';
import { useListings, useManualScan } from '@/api/listings';
import { useFilterStore } from '@/store/filterStore';
import { Card } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Progress } from '@/shared/ui/progress';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/shared/ui/pagination';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import {
  RefreshCw,
  Download,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { ListingTable } from '@/widgets/ListingTable';
import { FilterByCity } from '@/features/listings/filter-by-city';
import { FilterByStatus } from '@/features/listings/filter-by-status';
import { FilterByPrice } from '@/features/listings/filter-by-price';
import { FilterByRooms } from '@/features/listings/filter-by-rooms';
import { FilterByCurrency } from '@/features/listings/filter-by-currency';
import { SortListings } from '@/features/listings/sort-listings';
import { ExportListings } from '@/features/listings/export-listings';
import { TriggerManualScan, TriggerManualScanAlert } from '@/features/scanning/trigger-manual';
import { ViewProgress } from '@/features/scanning/view-progress';
import { ScanProgressModal } from '@/features/scanning/active-scanning';
import { Eye } from 'lucide-react';
import { CITIES } from '@/shared/config';

export function Listings() {
  const {
    city,
    page,
    size,
    status,
    priceFrom,
    priceTo,
    rooms,
    roomsOther,
    sort,
    currency,
    setPage,
    setFilters,
    getScanningCities,
  } = useFilterStore();

  const [showFilters, setShowFilters] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const scanningCities = getScanningCities();
  const hasAnyScanning = scanningCities.length > 0;

  const { data: listingsData, isLoading } = useListings({
    city: city === 'all' ? undefined : city,
    page,
    size,
    status: status === 'all' ? undefined : status,
    priceFrom,
    priceTo,
    rooms,
    roomsOther,
    currency,
    sort,
  });

  const totalPages = Math.ceil((listingsData?.total || 0) / size);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters({ [key]: value });
    setPage(1);
  };

  const handleCurrencyChange = (value: 'USD' | 'BYN') => {
    setFilters({ currency: value });
  };

  const handleRoomsChange = (newRooms: number[], other?: boolean) => {
    setFilters({ rooms: newRooms, roomsOther: other ?? false });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Объявления
          </h1>
          <p className="text-muted-foreground mt-1">
            {listingsData?.total || 0} объявлений найдено
          </p>
        </div>

        <div className="flex flex-col gap-2 w-full">
          <div className="flex items-center gap-2">
            <TriggerManualScan city={city === 'all' ? 'minsk' : city} />
            <Button
              variant="outline"
              onClick={() => setShowProgressModal(true)}
              disabled={!hasAnyScanning}
              className="flex items-center gap-2"
            >
              <Eye className="w-4 h-4" />
              <span className="hidden sm:inline">Прогресс</span>
            </Button>
            <ExportListings city={city !== 'all' ? city : undefined} status={status !== 'all' ? status : undefined} />
          </div>

          {/* Алерт о сканировании других городов */}
          <TriggerManualScanAlert city={city === 'all' ? 'minsk' : city} />
        </div>

        {/* Модальное окно просмотра прогресса */}
        <ScanProgressModal open={showProgressModal} onOpenChange={setShowProgressModal} />
      </div>

      {/* Progress */}
      <ViewProgress />

      {/* Filters */}
      <Card className="p-4">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <FilterByCity
              value={city}
              onChange={(value) => handleFilterChange('city', value)}
            />
            <FilterByCurrency
              value={currency}
              onChange={handleCurrencyChange}
            />
            <FilterByStatus
              value={status}
              onChange={(value) => handleFilterChange('status', value)}
            />
            <FilterByRooms 
              value={rooms} 
              other={roomsOther}
              onChange={handleRoomsChange} 
            />
            <SortListings value={sort} onChange={(value) => handleFilterChange('sort', value)} />

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? 'Скрыть фильтры' : 'Фильтры'}
            </Button>
          </div>

          {showFilters && (
            <FilterByPrice
              priceFrom={priceFrom}
              priceTo={priceTo}
              onChange={(from, to) => {
                setFilters({ priceFrom: from, priceTo: to });
                setPage(1);
              }}
            />
          )}
        </div>
      </Card>

      {/* Listings Table */}
      <ListingTable 
        listings={listingsData?.items || []} 
        isLoading={isLoading}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  if (page > 1) handlePageChange(page - 1);
                }}
                className={page === 1 ? 'pointer-events-none opacity-50' : ''}
                size="default"
              />
            </PaginationItem>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (page <= 3) {
                pageNum = i + 1;
              } else if (page >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = page - 2 + i;
              }
              return (
                <PaginationItem key={pageNum}>
                  <PaginationLink
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      handlePageChange(pageNum);
                    }}
                    isActive={pageNum === page}
                    size="default"
                  >
                    {pageNum}
                  </PaginationLink>
                </PaginationItem>
              );
            })}
            <PaginationItem>
              <PaginationNext
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  if (page < totalPages) handlePageChange(page + 1);
                }}
                className={page === totalPages ? 'pointer-events-none opacity-50' : ''}
                size="default"
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
}
