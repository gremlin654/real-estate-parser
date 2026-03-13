'use client';

import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { usePriceDropQuery } from '@/api/listings';
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
import { Slider } from '@/shared/ui/slider';
import { Download, TrendingDown, Home, DollarSign, Percent } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ListingCardWidget } from '@/widgets/ListingCard/ui/ListingCardWidget';
import { FilterByCity } from '@/features/listings/filter-by-city';
import { FilterByRooms } from '@/features/listings/filter-by-rooms';
import { FilterByCurrency } from '@/features/listings/filter-by-currency';
import { CITIES } from '@/shared/config';

export function PriceDropsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { currency, setFilters } = useFilterStore();
  
  // Получаем параметры из URL
  const cityParam = searchParams.get('city') || 'minsk';
  const dropPercentParam = parseInt(searchParams.get('drop_percent') || '10', 10);
  const pageParam = parseInt(searchParams.get('page') || '1', 10);
  
  const [dropPercent, setDropPercent] = useState(dropPercentParam);
  const [page, setPage] = useState(pageParam);
  const size = 20;

  const { data: priceDropData, isLoading, isError, error } = usePriceDropQuery({
    city: cityParam,
    dropPercent: dropPercent,
    currency: currency === 'USD' ? 'usd' : 'byn',
    page,
    size,
  });

  const totalPages = Math.ceil((priceDropData?.total || 0) / size);

  const handleCityChange = (value: string) => {
    searchParams.set('city', value);
    searchParams.set('page', '1');
    setSearchParams(searchParams);
    setPage(1);
  };

  const handleDropPercentChange = (value: number[]) => {
    const newValue = value[0];
    setDropPercent(newValue);
    searchParams.set('drop_percent', String(newValue));
    searchParams.set('page', '1');
    setSearchParams(searchParams);
    setPage(1);
  };

  const handleCurrencyChange = (value: 'USD' | 'BYN') => {
    setFilters({ currency: value });
    searchParams.set('page', '1');
    setSearchParams(searchParams);
    setPage(1);
  };

  const handleRoomsChange = (rooms: number[], other?: boolean) => {
    rooms.forEach((room) => searchParams.append('rooms', String(room)));
    if (other) searchParams.set('rooms_other', 'true');
    searchParams.set('page', '1');
    setSearchParams(searchParams);
    setPage(1);
  };

  const handlePageChange = (newPage: number) => {
    searchParams.set('page', String(newPage));
    setSearchParams(searchParams);
    setPage(newPage);
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
            Не удалось загрузить объявления с падением цены: {error?.message}
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
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-3">
            📉 Price Drop Tracker
          </h1>
          <p className="text-muted-foreground mt-1">
            Отслеживайте падение цен на недвижимость
          </p>
        </div>

        <Button variant="outline" className="flex items-center gap-2">
          <Download className="w-4 h-4" />
          <span>Экспорт</span>
        </Button>
      </div>

      {/* Stats Cards */}
      {priceDropData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-100 rounded-full">
                  <TrendingDown className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Всего предложений</p>
                  <p className="text-2xl font-bold">{priceDropData.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-100 rounded-full">
                  <Percent className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Среднее падение</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {priceDropData.avg_drop_percent.toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <TrendingDown className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Максимальное падение</p>
                  <p className="text-2xl font-bold text-red-600">
                    {priceDropData.max_drop_percent.toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-full">
                  <DollarSign className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Минимальное падение</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {priceDropData.min_drop_percent.toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <FilterByCity
            value={cityParam}
            onChange={handleCityChange}
          />
          
          <FilterByCurrency
            value={currency}
            onChange={handleCurrencyChange}
          />
          
          <FilterByRooms
            value={[]}
            other={false}
            onChange={handleRoomsChange}
          />

          {/* Drop Percent Slider */}
          <div className="flex items-center gap-4 min-w-[250px]">
            <span className="text-sm text-muted-foreground whitespace-nowrap">
              Падение цены: {dropPercent}%+
            </span>
            <Slider
              value={[dropPercent]}
              min={5}
              max={50}
              step={1}
              onValueChange={handleDropPercentChange}
              className="flex-1"
            />
          </div>
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
      {!isLoading && (!priceDropData || priceDropData.items.length === 0) && (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold mb-2">
              Объявления с падением цены не найдены
            </h3>
            <p className="text-muted-foreground mb-4">
              Попробуйте уменьшить минимальный процент падения или выбрать другой город
            </p>
            <Button asChild>
              <Link to="/listings">Перейти к объявлениям</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Price Drops Grid */}
      {!isLoading && priceDropData && priceDropData.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {priceDropData.items.map((item) => (
              <ListingCardWidget key={item.id} listing={item} />
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
        </>
      )}
    </div>
  );
}
