'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import type { PriceTrendData } from '@/shared/types';

interface PriceTrendChartWidgetProps {
  data: PriceTrendData[];
  rooms?: number;
  city?: string;
  isLoading?: boolean;
}

const formatMonthYear = (year: number, month: number): string => {
  const monthNames = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
  return `${monthNames[month - 1]} ${year}`;
};

const formatPrice = (value: number): string => {
  return `$${value.toLocaleString()}`;
};

const CustomTooltip = ({ active, payload, label, rooms }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="p-4 rounded-lg border bg-card/95 backdrop-blur-sm shadow-lg">
        <p className="font-semibold text-foreground mb-2">{label}</p>
        <p className="text-sm text-muted-foreground mb-1">{rooms}-комнатные квартиры</p>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-primary to-accent" />
          <span className="text-primary font-bold text-lg">{formatPrice(data.avg_price_usd)}</span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">{data.listings_count} объявлений</p>
      </div>
    );
  }
  return null;
};

export function PriceTrendChartWidget({
  data,
  rooms = 2,
  city = 'Минск',
  isLoading,
}: PriceTrendChartWidgetProps) {
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

  const chartData = data.map((point) => ({
    ...point,
    label: formatMonthYear(point.year, point.month),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Динамика цен</CardTitle>
        <CardDescription>
          Средняя цена для {rooms}-комнатных квартир в г. {city}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => value.split(' ')[0]}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip rooms={rooms} />} />
            <Area
              type="monotone"
              dataKey="avg_price_usd"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              fill="url(#colorPrice)"
            />
            <Line
              type="monotone"
              dataKey="avg_price_usd"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: 'hsl(var(--accent))' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
      <style>{`
        .recharts-surface,
        .recharts-surface *,
        .recharts-curve,
        .recharts-curve path,
        .recharts-area,
        .recharts-area path,
        .recharts-line,
        .recharts-line path,
        .recharts-dot,
        .recharts-active-dot {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
        .recharts-surface:focus,
        .recharts-surface:focus-visible,
        .recharts-curve:focus,
        .recharts-curve:focus-visible,
        .recharts-area:focus,
        .recharts-area:focus-visible,
        .recharts-line:focus,
        .recharts-line:focus-visible,
        .recharts-dot:focus,
        .recharts-dot:focus-visible,
        .recharts-active-dot:focus,
        .recharts-active-dot:focus-visible {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
      `}</style>
    </Card>
  );
}
