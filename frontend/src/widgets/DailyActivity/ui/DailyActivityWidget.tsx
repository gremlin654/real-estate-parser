'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import type { DailyActivityResponse } from '@/shared/types';
import { formatDateShort } from '@/shared/lib/date-format';

interface DailyActivityWidgetProps {
  data: DailyActivityResponse['data'];
  city?: string;
  periodDays?: number;
  isLoading?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="p-3 rounded-lg border bg-card/95 backdrop-blur-sm shadow-lg">
        <p className="font-semibold text-foreground mb-2">{label}</p>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-400" />
            <span className="text-sm">Новые: {data.new_count}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-rose-400" />
            <span className="text-sm">Удаленные: {data.deleted_count}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-violet-400" />
            <span className="text-sm">Изменения цены: {data.price_changed_count}</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export function DailyActivityWidget({
  data,
  city = 'Минск',
  periodDays = 30,
  isLoading,
}: DailyActivityWidgetProps) {
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
    date: formatDateShort(item.date),
    new_count: item.new_count,
    deleted_count: item.deleted_count,
    price_changed_count: item.price_changed_count,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Активность объявлений за 30 дней</CardTitle>
        <CardDescription>
          Динамика новых, удаленных и измененных объявлений
        </CardDescription>
      </CardHeader>
      <CardContent className="outline-none">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              content={<CustomTooltip />}
              cursor={{ fill: 'transparent' }}
            />
            <Bar
              dataKey="new_count"
              name="Новые"
              fill="#10b981"
              radius={[4, 4, 0, 0]}
              stroke="transparent"
              strokeWidth={0}
              isAnimationActive={false}
              animationDuration={0}
            />
            <Bar
              dataKey="deleted_count"
              name="Удаленные"
              fill="#f43f5e"
              radius={[4, 4, 0, 0]}
              stroke="transparent"
              strokeWidth={0}
              isAnimationActive={false}
              animationDuration={0}
            />
            <Bar
              dataKey="price_changed_count"
              name="Изменения цены"
              fill="#8b5cf6"
              radius={[4, 4, 0, 0]}
              stroke="transparent"
              strokeWidth={0}
              isAnimationActive={false}
              animationDuration={0}
            />
          </BarChart>
        </ResponsiveContainer>
        <style>{`
          .recharts-surface,
          .recharts-surface *,
          .recharts-bar,
          .recharts-bar *,
          .recharts-bar-rectangle,
          .recharts-bar-rectangle *,
          .recharts-bar-rectangle path {
            outline: none !important;
            outline-width: 0 !important;
            outline-color: transparent !important;
            box-shadow: none !important;
            cursor: default !important;
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
          .recharts-tooltip-wrapper {
            pointer-events: auto !important;
          }
          .recharts-tooltip-cursor {
            pointer-events: none !important;
          }
          .recharts-active-bar {
            display: none !important;
          }
        `}</style>
      </CardContent>
    </Card>
  );
}
