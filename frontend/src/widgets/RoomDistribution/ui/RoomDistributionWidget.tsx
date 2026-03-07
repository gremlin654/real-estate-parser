'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import type { RoomDistributionResponse } from '@/shared/types';

interface RoomDistributionWidgetProps {
  data: RoomDistributionResponse['data'];
  city?: string;
  isLoading?: boolean;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088FE', '#00C49F'];

const formatPrice = (value: number | undefined): string => {
  if (value === undefined || value === null) return '—';
  return `$${value.toLocaleString()}`;
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="p-3 rounded-lg border bg-card/95 backdrop-blur-sm shadow-lg">
        <p className="font-semibold text-white mb-1">
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

  // Группируем 4+ комнатные в одну категорию
  const groupedData = data.reduce((acc, item) => {
    const rooms = item.rooms >= 4 ? '4+' : `${item.rooms}`;
    const existing = acc.find((a) => a.rooms === rooms);
    if (existing) {
      existing.count += item.count;
      existing.avg_price = ((existing.avg_price * (existing.count - item.count)) + (item.avg_price * item.count)) / existing.count;
    } else {
      acc.push({
        rooms,
        count: item.count,
        avg_price: item.avg_price,
      });
    }
    return acc;
  }, [] as Array<{rooms: string; count: number; avg_price: number}>);

  const chartData = groupedData.map((item, index) => ({
    name: item.rooms === '4+' ? '4+ комн.' : `${item.rooms}-комн.`,
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
              style={{ outline: 'none' }}
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[index % COLORS.length]}
                  stroke="#1a1a1a"
                  strokeWidth={2}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ 
                color: 'white',
                fontSize: '14px'
              }} 
            />
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
        .recharts-active-sector,
        .recharts-text {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
        .recharts-text {
          fill: white !important;
          font-weight: 600 !important;
          text-shadow: 1px 1px 2px rgba(0,0,0,0.8) !important;
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
