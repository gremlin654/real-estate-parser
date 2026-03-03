import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import type { PriceTrendPoint } from "@/api/listings";

interface PriceTrendChartProps {
  data: PriceTrendPoint[];
  rooms: number;
  isLoading?: boolean;
}

// Format month/year label (e.g., "Jan 2025")
const formatMonthYear = (year: number, month: number): string => {
  const monthNames = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
  ];
  return `${monthNames[month - 1]} ${year}`;
};

// Format price with $ symbol
const formatPrice = (value: number): string => {
  return `$${value.toLocaleString()}`;
};

export function PriceTrendChart({ data, rooms, isLoading }: PriceTrendChartProps) {
  if (isLoading) {
    return (
      <div className="flex h-[300px] items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center">
        <p className="text-muted-foreground">No data available</p>
      </div>
    );
  }

  // Transform data for chart - add formatted label
  const chartData = data.map((point) => ({
    ...point,
    label: formatMonthYear(point.year, point.month),
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="label"
          className="text-xs text-muted-foreground"
          tick={{ fill: "oklch(0.9 0.01 280)" }}
        />
        <YAxis
          className="text-xs text-muted-foreground"
          tick={{ fill: "oklch(0.9 0.01 280)" }}
          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "oklch(0.2 0.01 280)",
            border: "1px solid oklch(0.3 0.01 280)",
            borderRadius: "8px",
          }}
          labelStyle={{ color: "oklch(0.9 0.01 280)" }}
          formatter={(value) => [formatPrice(typeof value === 'number' ? value : 0), "Avg Price"] as [string, string]}
          labelFormatter={(label) => `${label} (${rooms}-room apartments)`}
        />
        <Line
          type="monotone"
          dataKey="avg_price_usd"
          stroke="oklch(0.7 0.22 40)"
          strokeWidth={2}
          dot={{ fill: "oklch(0.7 0.22 40)", strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, fill: "oklch(0.8 0.19 70)" }}
          name="Average Price"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
