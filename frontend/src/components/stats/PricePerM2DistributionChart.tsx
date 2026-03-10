'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts';
import type { PricePerM2DistributionBin } from '@/shared/types';
import { CardContent } from '@/shared/ui/card';

interface PricePerM2DistributionChartProps {
  data: PricePerM2DistributionBin[];
  currency: 'BYN' | 'USD';
}

export function PricePerM2DistributionChart({ data, currency }: PricePerM2DistributionChartProps) {
  const formatLabel = (bin: PricePerM2DistributionBin) => {
    return `${Math.floor(bin.range_min).toLocaleString()} - ${Math.floor(bin.range_max).toLocaleString()}`;
  };

  const formatCurrency = (value: number) => {
    return `${value.toLocaleString()} ${currency}/м²`;
  };

  // Генерация градиентных цветов для баров
  const getBarColor = (index: number, total: number) => {
    const hue = 200 + (index / total) * 80; // От синего к фиолетовому
    return `hsl(${hue}, 70%, 50%)`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-medium mb-2">{label}</p>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span>Объявлений: </span>
              <span className="font-semibold">{data.count}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="w-3 h-3 rounded-full bg-blue-300" />
              <span>Процент: </span>
              <span>{data.percentage.toFixed(1)}%</span>
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

  const chartData = data.map((bin) => ({
    ...bin,
    label: formatLabel(bin),
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="label"
          angle={-45}
          textAnchor="end"
          height={100}
          className="text-xs"
          tick={{ fontSize: 11 }}
        />
        <YAxis
          className="text-xs"
          tick={{ fontSize: 12 }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Bar dataKey="count" name="Объявлений" fill="#8884d8">
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={getBarColor(index, chartData.length)}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function PricePerM2DistributionChartWithStyles(props: PricePerM2DistributionChartProps) {
  return (
    <>
      <PricePerM2DistributionChart {...props} />
      <style>{`
        .recharts-surface,
        .recharts-surface *,
        .recharts-bar,
        .recharts-bar path,
        .recharts-rectangle,
        .recharts-rectangle path,
        .recharts-active-bar,
        .recharts-active-rectangle {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
        .recharts-surface:focus,
        .recharts-surface:focus-visible,
        .recharts-bar:focus,
        .recharts-bar:focus-visible,
        .recharts-rectangle:focus,
        .recharts-rectangle:focus-visible,
        .recharts-active-bar:focus,
        .recharts-active-bar:focus-visible,
        .recharts-active-rectangle:focus,
        .recharts-active-rectangle:focus-visible {
          outline: none !important;
          outline-width: 0 !important;
          outline-color: transparent !important;
          box-shadow: none !important;
        }
        .recharts-cartesian-axis-tick-value {
          fill: white !important;
        }
        .recharts-cartesian-axis-tick-value text {
          fill: white !important;
        }
        .recharts-cartesian-axis-tick-value tspan {
          fill: white !important;
        }
        .recharts-active-bar,
        .recharts-active-rectangle {
          fill-opacity: 1 !important;
        }
      `}</style>
    </>
  );
}
