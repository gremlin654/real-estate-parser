'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { PricePerM2Trend } from '@/shared/types';
import { CardContent } from '@/shared/ui/card';

interface PricePerM2TrendChartProps {
  data: PricePerM2Trend[];
  currency: 'BYN' | 'USD';
  period?: number;
}

export function PricePerM2TrendChart({ data, currency, period = 30 }: PricePerM2TrendChartProps) {
  const formatCurrency = (value: number) => {
    return `${value.toLocaleString()} ${currency}/м²`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-medium mb-2">{formatDate(label)}</p>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span>Средняя: </span>
              <span className="font-semibold">{formatCurrency(data.average)}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span>Медиана: </span>
              <span className="font-semibold">{formatCurrency(data.median)}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="w-3 h-3 rounded-full bg-gray-400" />
              <span>Объявлений: </span>
              <span>{data.count}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  if (!data || data.length === 0) {
    return (
      <CardContent className="flex items-center justify-center h-[350px]">
        <p className="text-muted-foreground">Нет данных для отображения</p>
      </CardContent>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          className="text-xs"
          tick={{ fontSize: 12 }}
        />
        <YAxis
          tickFormatter={(value) => `${value.toLocaleString()}`}
          className="text-xs"
          tick={{ fontSize: 12 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="average"
          name="Средняя"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="median"
          name="Медиана"
          stroke="#22c55e"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
