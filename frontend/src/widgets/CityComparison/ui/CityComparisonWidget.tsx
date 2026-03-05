'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import type { CityComparisonData } from '@/shared/types';
import { CITIES } from '@/shared/config';

interface CityComparisonWidgetProps {
  data: CityComparisonData['data'];
  isLoading?: boolean;
}

const formatPrice = (value: number): string => {
  return `$${value.toLocaleString()}`;
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="p-3 rounded-lg border bg-card/95 backdrop-blur-sm shadow-lg">
        <p className="font-semibold text-foreground mb-1">{data.cityName}</p>
        <p className="text-primary font-bold text-lg">{formatPrice(data.avg_price_usd)}</p>
        <p className="text-sm text-muted-foreground mt-1">{data.count} объявлений</p>
      </div>
    );
  }
  return null;
};

export function CityComparisonWidget({ data, isLoading }: CityComparisonWidgetProps) {
  if (isLoading) {
    return (
      <div className="flex h-[300px] items-center justify-center">
        <p className="text-muted-foreground">Загрузка...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center">
        <p className="text-muted-foreground">Нет данных для отображения</p>
      </div>
    );
  }

  const chartData = data.map((item) => ({
    cityName: CITIES[item.city as keyof typeof CITIES] || item.city,
    avg_price_usd: item.avg_price_usd,
    count: item.count,
    city: item.city,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Сравнение городов</CardTitle>
        <CardDescription>Средняя цена квартир по городам</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="cityName" tick={{ fontSize: 12 }} angle={-10} textAnchor="end" height={60} />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="avg_price_usd" name="Средняя цена" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={`hsl(var(--chart-${index + 1}))`} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
      <style>{`
        .recharts-surface,
        .recharts-surface *,
        .recharts-bar,
        .recharts-bar *,
        .recharts-bar-rectangle,
        .recharts-bar-rectangle path {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
        .recharts-surface:focus,
        .recharts-surface:focus-visible,
        .recharts-bar:focus,
        .recharts-bar:focus-visible,
        .recharts-bar-rectangle:focus,
        .recharts-bar-rectangle:focus-visible,
        .recharts-bar-rectangle path:focus,
        .recharts-bar-rectangle path:focus-visible {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
      `}</style>
    </Card>
  );
}
