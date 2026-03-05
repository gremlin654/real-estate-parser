'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { Skeleton } from '@/shared/ui/skeleton';
import { usePriceTrends, useRoomDistribution, useDailyActivity } from '@/api/listings';
import {
  BarChart3,
  PieChart,
  Activity,
  ArrowLeftRight,
} from 'lucide-react';
import { PriceTrendChartWidget } from '@/widgets/PriceChart';
import { RoomDistributionWidget } from '@/widgets/RoomDistribution';
import { DailyActivityWidget } from '@/widgets/DailyActivity';
import { CityComparisonWidget } from '@/widgets/CityComparison';
import { useCityComparison } from '@/api/listings';
import { CITIES } from '@/shared/config';

export function Statistics() {
  const [selectedCity, setSelectedCity] = useState('minsk');
  const [selectedRooms, setSelectedRooms] = useState(2);
  const [period, setPeriod] = useState(12);

  const { data: priceTrends } = usePriceTrends(selectedCity, selectedRooms, period);
  const { data: roomDistribution } = useRoomDistribution(selectedCity);
  const { data: dailyActivity } = useDailyActivity(selectedCity, 30);
  const { data: cityComparison } = useCityComparison();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
            Статистика
          </h1>
          <p className="text-muted-foreground mt-1">
            Аналитика рынка недвижимости
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedCity} onValueChange={setSelectedCity}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Город" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(CITIES).map(([code, name]) => (
                <SelectItem key={code} value={code}>
                  {name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={period.toString()} onValueChange={(v) => setPeriod(parseInt(v))}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Период" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="6">6 месяцев</SelectItem>
              <SelectItem value="12">1 год</SelectItem>
              <SelectItem value="24">2 года</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="trends" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Динамика цен
          </TabsTrigger>
          <TabsTrigger value="rooms" className="flex items-center gap-2">
            <PieChart className="w-4 h-4" />
            По комнатам
          </TabsTrigger>
          <TabsTrigger value="activity" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Активность
          </TabsTrigger>
          <TabsTrigger value="cities" className="flex items-center gap-2">
            <ArrowLeftRight className="w-4 h-4" />
            Сравнение
          </TabsTrigger>
        </TabsList>

        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <CardTitle>Динамика цен</CardTitle>
              <CardDescription>
                Средняя цена для {selectedRooms}-комнатных квартир в г.{' '}
                {CITIES[selectedCity as keyof typeof CITIES]}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Комнат:</span>
                <Select
                  value={selectedRooms.toString()}
                  onValueChange={(v) => setSelectedRooms(parseInt(v))}
                >
                  <SelectTrigger className="w-[120px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1-комн</SelectItem>
                    <SelectItem value="2">2-комн</SelectItem>
                    <SelectItem value="3">3-комн</SelectItem>
                    <SelectItem value="4">4+ комн</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <PriceTrendChartWidget
                data={priceTrends?.data || []}
                rooms={selectedRooms}
                city={selectedCity}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rooms">
          <RoomDistributionWidget
            data={roomDistribution?.data || []}
            city={selectedCity}
          />
        </TabsContent>

        <TabsContent value="activity">
          <DailyActivityWidget
            data={dailyActivity?.data || []}
            city={selectedCity}
            periodDays={30}
          />
        </TabsContent>

        <TabsContent value="cities">
          <CityComparisonWidget data={cityComparison?.data || []} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
