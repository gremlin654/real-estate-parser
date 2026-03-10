'use client';

import { useState } from 'react';
import { useFilterStore } from '@/store/filterStore';
import { usePricePerM2Stats, usePricePerM2Trends, usePricePerM2Distribution } from '@/api/listings';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Skeleton } from '@/shared/ui/skeleton';
import { Badge } from '@/shared/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs';
import { TrendingUp, BarChart3, DollarSign, ArrowDownUp, Building } from 'lucide-react';
import { PricePerM2TrendChartWithStyles as PricePerM2TrendChart } from '@/components/stats/PricePerM2TrendChart';
import { PricePerM2DistributionChartWithStyles as PricePerM2DistributionChart } from '@/components/stats/PricePerM2DistributionChart';
import { FilterByCity } from '@/features/listings/filter-by-city';
import { FilterByCurrency } from '@/features/listings/filter-by-currency';
import { FilterByRooms } from '@/features/listings/filter-by-rooms';
import { CITIES } from '@/shared/config';

type Period = 7 | 30 | 90;

export function PricePerM2AnalyticsPage() {
  const { city, currency, rooms, setCity, setCurrency, setRooms } = useFilterStore();
  const [period, setPeriod] = useState<Period>(30);
  const [interval, setInterval] = useState<'day' | 'week' | 'month'>('day');

  // Запросы данных
  const { data: stats, isLoading: statsLoading, error: statsError, isError: isStatsError } = usePricePerM2Stats({
    city: city === 'all' ? 'minsk' : city,
    rooms: rooms.length > 0 ? rooms[0] : undefined,
    currency: currency.toLowerCase() as 'byn' | 'usd',
  });

  const { data: trendsData, isLoading: trendsLoading, error: trendsError, isError: isTrendsError } = usePricePerM2Trends({
    city: city === 'all' ? 'minsk' : city,
    rooms: rooms.length > 0 ? rooms[0] : undefined,
    period_days: period,
    interval,
    currency: currency.toLowerCase() as 'byn' | 'usd',
  });

  const { data: distributionData, isLoading: distributionLoading, error: distributionError, isError: isDistributionError } = usePricePerM2Distribution({
    city: city === 'all' ? 'minsk' : city,
    rooms: rooms.length > 0 ? rooms[0] : undefined,
    bins: 10,
    currency: currency.toLowerCase() as 'byn' | 'usd',
  });

  const trends = trendsData || [];
  const distribution = distributionData || [];

  // Проверка на 404 ошибку
  const hasError = isStatsError || isTrendsError || isDistributionError;
  const isNotFound = [statsError, trendsError, distributionError].some(
    (error) => error?.message?.includes('404')
  );

  const handleCityChange = (value: string) => {
    setCity(value);
  };

  const handleCurrencyChange = (value: 'USD' | 'BYN') => {
    setCurrency(value);
  };

  const handleRoomsChange = (newRooms: number[], other?: boolean) => {
    setRooms(newRooms, other);
  };

  const StatCard = ({ 
    title, 
    value, 
    icon: Icon, 
    isLoading 
  }: { 
    title: string; 
    value: string; 
    icon: any; 
    isLoading: boolean;
  }) => (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between space-y-0">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            {isLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <p className="text-2xl font-bold">{value}</p>
            )}
          </div>
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div data-testid="price-per-m2-header">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          Аналитика цены за м²
        </h1>
        <p className="text-muted-foreground mt-1">
          Динамика и распределение цен за квадратный метр
        </p>
      </div>

      {/* Error State - 404 */}
      {hasError && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Building className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {isNotFound ? 'Нет данных для выбранных параметров' : 'Ошибка загрузки данных'}
              </h3>
              <p className="text-muted-foreground mb-4">
                {isNotFound 
                  ? 'Попробуйте изменить параметры фильтра или выберите другой город' 
                  : 'Произошла ошибка при загрузке данных. Попробуйте обновить страницу.'}
              </p>
              <Button onClick={() => window.location.reload()}>
                Обновить страницу
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      {!hasError && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-wrap items-center gap-2">
              <FilterByCity
                value={city}
                onChange={handleCityChange}
              />
              <FilterByCurrency
                value={currency}
                onChange={handleCurrencyChange}
              />
              <FilterByRooms
                value={rooms}
                other={false}
                onChange={handleRoomsChange}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      {!hasError && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4" data-testid="summary-stats-cards">
          <StatCard
            title="Средняя цена за м²"
            value={stats ? `${Math.floor(stats.average).toLocaleString()} ${currency}/м²` : '-'}
            icon={TrendingUp}
            isLoading={statsLoading}
          />
          <StatCard
            title="Медиана"
            value={stats ? `${Math.floor(stats.median).toLocaleString()} ${currency}/м²` : '-'}
            icon={DollarSign}
            isLoading={statsLoading}
          />
          <StatCard
            title="Минимум"
            value={stats ? `${Math.floor(stats.min).toLocaleString()} ${currency}/м²` : '-'}
            icon={ArrowDownUp}
            isLoading={statsLoading}
          />
          <StatCard
            title="Максимум"
            value={stats ? `${Math.floor(stats.max).toLocaleString()} ${currency}/м²` : '-'}
            icon={Building}
            isLoading={statsLoading}
          />
        </div>
      )}

      {/* Charts */}
      {!hasError && (
        <Tabs defaultValue="trend" className="space-y-4">
          <TabsList>
            <TabsTrigger value="trend" className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Динамика
            </TabsTrigger>
            <TabsTrigger value="distribution" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Распределение
            </TabsTrigger>
          </TabsList>

          <TabsContent value="trend" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Динамика цены за м²
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    {CITIES[city as keyof typeof CITIES] || city}
                  </Badge>
                  <div className="flex items-center gap-1" data-testid="period-buttons">
                    {[7, 30, 90].map((p) => (
                      <Button
                        key={p}
                        variant={period === p ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => {
                          setPeriod(p as Period);
                          setInterval(p === 7 ? 'day' : p === 30 ? 'day' : 'week');
                        }}
                        data-testid={`period-${p}`}
                      >
                        {p} дн.
                      </Button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {trendsLoading ? (
                  <Skeleton className="h-[350px] w-full" />
                ) : trends.length > 0 ? (
                  <PricePerM2TrendChart
                    data={trends}
                    currency={currency as 'BYN' | 'USD'}
                    period={period}
                  />
                ) : (
                  <div className="h-[350px] flex items-center justify-center text-muted-foreground">
                    Нет данных за выбранный период
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="distribution" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Распределение цены за м²
                </CardTitle>
              </CardHeader>
              <CardContent>
                {distributionLoading ? (
                  <Skeleton className="h-[350px] w-full" />
                ) : distribution.length > 0 ? (
                  <PricePerM2DistributionChart
                    data={distribution}
                    currency={currency as 'BYN' | 'USD'}
                  />
                ) : (
                  <div className="h-[350px] flex items-center justify-center text-muted-foreground">
                    Нет данных для отображения
                  </div>
                )}
                {distribution.length > 0 && (
                  <div className="mt-4 text-sm text-muted-foreground text-center">
                    Всего объявлений: {stats?.count.toLocaleString() || 0}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
