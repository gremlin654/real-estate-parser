'use client';

import { useState } from 'react';
import { useDealsQuery } from '@/api/listings';
import { useFilterStore } from '@/store/filterStore';
import { Card, CardContent } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/shared/ui/alert';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/shared/ui/pagination';
import { Download, TrendingDown, Home, DollarSign, Percent } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ListingCardWidget } from '@/widgets/ListingCard/ui/ListingCardWidget';
import { FilterByCity } from '@/features/listings/filter-by-city';
import { FilterByRooms } from '@/features/listings/filter-by-rooms';
import { FilterByCurrency } from '@/features/listings/filter-by-currency';
import { CITIES } from '@/shared/config';

export function DealsPage() {
  const { city, rooms, roomsOther, currency, setFilters } = useFilterStore();
  const [page, setPage] = useState(1);
  const size = 20;

  const { data: dealsData, isLoading, isError, error } = useDealsQuery({
    city: city === 'all' ? undefined : city,
    rooms,
    roomsOther,
    currency: currency === 'USD' ? 'usd' : 'byn',
    page,
    size,
  });

  const totalPages = Math.ceil((dealsData?.total || 0) / size);

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

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency === 'USD' ? 'USD' : 'BYN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Обработка ошибки
  if (isError) {
    return (
      <div className="container mx-auto p-4">
        <Alert variant="destructive">
          <AlertTitle>Ошибка загрузки</AlertTitle>
          <AlertDescription>
            Не удалось загрузить выгодные предложения: {error?.message}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent flex items-center gap-3">
            🔥 Выгодные предложения
          </h1>
          <p className="text-muted-foreground mt-1">
            Квартиры по цене ниже средней цены за м²
          </p>
        </div>

        <Button variant="outline" className="flex items-center gap-2">
          <Download className="w-4 h-4" />
          <span>Экспорт</span>
        </Button>
      </div>

      {/* Stats Cards */}
      {dealsData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <TrendingDown className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Всего предложений</p>
                  <p className="text-2xl font-bold">{dealsData.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-orange-100 rounded-full">
                  <Percent className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Средняя цена за м²</p>
                  <p className="text-2xl font-bold">{formatCurrency(dealsData.avg_price_per_m2)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-full">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Лучшая выгода</p>
                  <p className="text-2xl font-bold text-green-600">
                    {dealsData.items.length > 0 
                      ? `${Math.min(...dealsData.items.map(d => d.deal_percent)).toFixed(0)}%`
                      : '0%'
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-full">
                  <Home className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Город</p>
                  <p className="text-lg font-semibold">
                    {city === 'all' ? 'Все' : CITIES[city as keyof typeof CITIES] || city}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-2">
          <FilterByCity
            value={city}
            onChange={(value) => handleFilterChange('city', value)}
          />
          <FilterByCurrency
            value={currency}
            onChange={handleCurrencyChange}
          />
          <FilterByRooms
            value={rooms}
            other={roomsOther}
            onChange={handleRoomsChange}
          />
        </div>
      </Card>

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <div className="animate-pulse">
                <div className="aspect-video bg-muted" />
                <CardContent className="p-4 space-y-3">
                  <div className="h-4 bg-muted rounded w-3/4" />
                  <div className="h-6 bg-muted rounded w-1/2" />
                  <div className="flex gap-2">
                    <div className="h-4 bg-muted rounded w-16" />
                    <div className="h-4 bg-muted rounded w-16" />
                  </div>
                </CardContent>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && (!dealsData || dealsData.items.length === 0) && (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold mb-2">Выгодные предложения не найдены</h3>
            <p className="text-muted-foreground mb-4">
              Попробуйте изменить параметры поиска или выбрать другой город
            </p>
            <Button asChild>
              <Link to="/listings">Перейти к объявлениям</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Deals Grid */}
      {!isLoading && dealsData && dealsData.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {dealsData.items.map((deal) => (
              <ListingCardWidget key={deal.id} listing={deal} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      if (page > 1) setPage(page - 1);
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
                          setPage(pageNum);
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
                      if (page < totalPages) setPage(page + 1);
                    }}
                    className={page === totalPages ? 'pointer-events-none opacity-50' : ''}
                    size="default"
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </>
      )}
    </div>
  );
}
