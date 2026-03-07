'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import type { RoomDistributionResponse } from '@/shared/types';

interface RoomDistributionWidgetProps {
  data: RoomDistributionResponse['data'];
  city?: string;
  isLoading?: boolean;
}

const COLORS = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))', 'hsl(var(--chart-4))', 'hsl(var(--chart-5))'];

const formatPrice = (value: number | undefined): string => {
  if (value === undefined || value === null) return '—';
  return `$${value.toLocaleString()}`;
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="p-3 rounded-lg border bg-card/95 backdrop-blur-sm shadow-lg">
        <p className="font-semibold text-foreground mb-1">
          {data.rooms}-комнатные
        </p>
        <p className="text-sm text-muted-foreground">
          {data.count} объявлений
        </p>
        <p className="text-primary font-bold text-sm mt-1">
          {formatPrice(data.avg_price)}
        </p>
      </div>
    );
  }
  return null;
};

export function RoomDistributionWidget({
  data,
  city = 'Минск',
  isLoading,
}: RoomDistributionWidgetProps) {
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

  const chartData = data.map((item, index) => ({
    name: `${item.rooms}-комн.`,
    value: item.count,
    avgPrice: item.avg_price,
    rooms: item.rooms,
    count: item.count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Распределение по комнатам</CardTitle>
        <CardDescription>Количество объявлений по типу квартир в г. {city}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
      <style>{`
        .recharts-surface,
        .recharts-surface *,
        .recharts-pie,
        .recharts-pie path,
        .recharts-sector,
        .recharts-sector path,
        .recharts-active-sector {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
        .recharts-surface:focus,
        .recharts-surface:focus-visible,
        .recharts-pie:focus,
        .recharts-pie:focus-visible,
        .recharts-sector:focus,
        .recharts-sector:focus-visible,
        .recharts-active-sector:focus,
        .recharts-active-sector:focus-visible {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
      `}</style>
    </Card>
  );
}
