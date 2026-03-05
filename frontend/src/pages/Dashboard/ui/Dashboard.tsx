'use client';

import { Link } from 'react-router-dom';
import { useFilterStore } from '@/store/filterStore';
import { useSummary } from '@/api/listings';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import { Skeleton } from '@/shared/ui/skeleton';
import { Badge } from '@/shared/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  CheckCircle,
  Home,
} from 'lucide-react';
import { StatCard } from '@/entities/stats';
import { CITIES } from '@/shared/config';

function StatCardWrapper({
  title,
  value,
  icon,
  color,
  isLoading,
  trend,
}: {
  title: string;
  value: number;
  icon: any;
  color: string;
  isLoading: boolean;
  trend?: 'up' | 'down' | 'neutral';
}) {
  const Icon = icon;
  return (
    <Card className="card-gradient p-6 hover-glow animate-fade-in">
      <div className="flex flex-col items-center justify-center space-y-4 text-center">
        <div className={`p-3 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 ${color}`}>
          <Icon className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground font-medium">{title}</p>
          {isLoading ? (
            <Skeleton className="h-10 w-24 mx-auto" />
          ) : (
            <div className="flex items-center gap-3 justify-center">
              <p className="text-3xl font-bold bg-gradient-to-r from-foreground to-primary bg-clip-text text-transparent">
                {value.toLocaleString()}
              </p>
              {trend && (
                <Badge
                  variant={trend === 'up' ? 'default' : trend === 'down' ? 'destructive' : 'secondary'}
                  className="text-xs"
                >
                  {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
                </Badge>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

export function Dashboard() {
  const { city, setCity } = useFilterStore();
  const { data: summary, isLoading: summaryLoading } = useSummary(city);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Панель управления
          </h1>
          <p className="text-muted-foreground mt-1">Мониторинг недвижимости Kufar.by</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={city} onValueChange={setCity}>
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
          <Link to="/listings">
            <Badge variant="outline" className="text-sm">
              <Home className="w-4 h-4 mr-2" />
              Перейти к объявлениям
            </Badge>
          </Link>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCardWrapper
          title="Активные объявления"
          value={summary?.active_total || 0}
          icon={CheckCircle}
          color="text-green-500"
          isLoading={summaryLoading}
          trend="neutral"
        />
        <StatCardWrapper
          title="Новые сегодня"
          value={summary?.new_today || 0}
          icon={TrendingUp}
          color="text-blue-500"
          isLoading={summaryLoading}
          trend="up"
        />
        <StatCardWrapper
          title="Удалены сегодня"
          value={summary?.deleted_today || 0}
          icon={TrendingDown}
          color="text-red-500"
          isLoading={summaryLoading}
          trend="down"
        />
        <StatCardWrapper
          title="Изменения цены (USD)"
          value={summary?.price_changed_usd_today || 0}
          icon={DollarSign}
          color="text-purple-500"
          isLoading={summaryLoading}
          trend="neutral"
        />
      </div>
    </div>
  );
}
