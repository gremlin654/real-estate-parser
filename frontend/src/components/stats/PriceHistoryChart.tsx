'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Dot,
} from 'recharts';
import type { PriceDropHistoryItem } from '@/shared/types';
import { CardContent } from '@/shared/ui/card';

interface PriceHistoryChartProps {
  history: PriceDropHistoryItem[];
  currency: 'BYN' | 'USD';
}

interface ChartDataPoint {
  date: string;
  price: number;
  eventType: string;
  isPriceChange: boolean;
}

/**
 * PriceHistoryChart - график истории изменения цены объявления
 *
 * Использует recharts LineChart для отображения:
 * - Точек на каждом событии изменения цены
 * - Tooltip с датой и ценой
 * - Адаптивности для mobile
 */
export function PriceHistoryChart({ history, currency }: PriceHistoryChartProps) {
  // Форматирование валюты
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency === 'USD' ? 'USD' : 'BYN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Форматирование даты
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
    });
  };

  // Преобразование данных для графика
  const chartData: ChartDataPoint[] = history.map((item) => ({
    date: item.created_at,
    price: item.price_after,
    eventType: item.event_type,
    isPriceChange: item.event_type === 'price_changed' || item.event_type === 'price_changed_byn',
  }));

  // Custom tooltip для графика
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as ChartDataPoint;
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-medium mb-2 text-sm">{formatDate(label)}</p>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span>Цена: </span>
              <span className="font-semibold">{formatCurrency(data.price)}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <span>Событие: </span>
              <span className="capitalize">
                {data.eventType === 'price_changed' || data.eventType === 'price_changed_byn'
                  ? 'Изменение цены'
                  : data.eventType === 'created'
                  ? 'Создано'
                  : data.eventType}
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  // Custom dot для точек на графике
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;

    return (
      <Dot
        cx={cx}
        cy={cy}
        r={payload.isPriceChange ? 6 : 4}
        fill={payload.isPriceChange ? '#ef4444' : '#3b82f6'}
        stroke="#fff"
        strokeWidth={2}
      />
    );
  };

  if (!history || history.length === 0) {
    return (
      <CardContent className="flex items-center justify-center h-[300px]">
        <p className="text-muted-foreground">Нет данных для отображения</p>
      </CardContent>
    );
  }

  // Сортировка данных по дате
  const sortedData = [...chartData].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={sortedData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          className="text-xs"
          tick={{ fontSize: 12 }}
          minTickGap={30}
        />
        <YAxis
          tickFormatter={(value) => `${value.toLocaleString()}`}
          className="text-xs"
          tick={{ fontSize: 12 }}
          domain={['dataMin - 1000', 'dataMax + 1000']}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={<CustomDot />}
          activeDot={{ r: 8 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function PriceHistoryChartWithStyles(props: PriceHistoryChartProps) {
  return (
    <>
      <PriceHistoryChart {...props} />
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
    </>
  );
}
