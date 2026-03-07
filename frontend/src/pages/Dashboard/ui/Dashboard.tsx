'use client';

import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useFilterStore } from '@/store/filterStore';
import { useSummary, useScanHistory } from '@/api/listings';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import { Skeleton } from '@/shared/ui/skeleton';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/shared/ui/pagination';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  CheckCircle,
  Home,
  FileText,
} from 'lucide-react';
import { StatCard } from '@/entities/stats';
import { CITIES, SCAN_HISTORY_PAGE_SIZE } from '@/shared/config';
import { ScanHistoryTable } from '@/features/scan-history';
import { ActiveScanningWidget, ScanProgressModal } from '@/features/scanning/active-scanning';
import { Eye } from 'lucide-react';

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
  const [showProgressModal, setShowProgressModal] = useState(false);
  const { city, setCity, getScanningCities } = useFilterStore();
  const scanningCities = getScanningCities();
  const hasAnyScanning = scanningCities.length > 0;
  const { data: summary, isLoading: summaryLoading } = useSummary(city);
  
  // Состояние для фильтров истории сканирований
  const [historyPage, setHistoryPage] = useState(1);
  const [historyStatus, setHistoryStatus] = useState<string>('all');
  const [historyTriggerType, setHistoryTriggerType] = useState<string>('all');

  // Hook для истории сканирований
  const { data: scanHistory, isLoading: historyLoading } = useScanHistory({
    page: historyPage,
    size: SCAN_HISTORY_PAGE_SIZE,
    city: city !== 'all' ? city : undefined,
    status: historyStatus !== 'all' ? historyStatus as 'running' | 'completed' | 'error' : undefined,
    trigger_type: historyTriggerType !== 'all' ? historyTriggerType as 'manual' | 'scheduled' : undefined,
  });

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

      {/* Active Scanning Widget */}
      {hasAnyScanning && (
        <div className="space-y-2">
          <ActiveScanningWidget />
        </div>
      )}

      {/* Кнопка "Посмотреть прогресс" */}
      <div className="flex justify-end">
        <Button
          variant="outline"
          onClick={() => setShowProgressModal(true)}
          disabled={!hasAnyScanning}
          className="flex items-center gap-2"
        >
          <Eye className="w-4 h-4" />
          Посмотреть прогресс сканирования
        </Button>
      </div>

      {/* Модальное окно просмотра прогресса */}
      <ScanProgressModal open={showProgressModal} onOpenChange={setShowProgressModal} />

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

      {/* Scan History Section */}
      <Card className="border-muted/50 shadow-lg">
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                📊 История сканирований
              </CardTitle>
              <CardDescription>
                Последние сканирования недвижимости
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              {/* Фильтр по статусу */}
              <Select value={historyStatus} onValueChange={setHistoryStatus}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="Статус" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все статусы</SelectItem>
                  <SelectItem value="completed">Завершено</SelectItem>
                  <SelectItem value="error">Ошибка</SelectItem>
                  <SelectItem value="running">В процессе</SelectItem>
                </SelectContent>
              </Select>
              
              {/* Фильтр по типу запуска */}
              <Select value={historyTriggerType} onValueChange={setHistoryTriggerType}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="Тип" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все типы</SelectItem>
                  <SelectItem value="manual">Ручное</SelectItem>
                  <SelectItem value="scheduled">Авто</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Таблица истории */}
          <ScanHistoryTable 
            data={scanHistory?.items || []} 
            isLoading={historyLoading}
            emptyMessage="История сканирований пуста"
          />

          {/* Пагинация */}
          {scanHistory && scanHistory.total_pages > 1 && (
            <Pagination className="mt-4">
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      if (historyPage > 1) setHistoryPage(historyPage - 1);
                    }}
                    className={historyPage === 1 ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
                
                {[...Array(scanHistory.total_pages)].map((_, i) => (
                  <PaginationItem key={i}>
                    <PaginationLink
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        setHistoryPage(i + 1);
                      }}
                      isActive={historyPage === i + 1}
                    >
                      {i + 1}
                    </PaginationLink>
                  </PaginationItem>
                ))}
                
                <PaginationItem>
                  <PaginationNext
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      if (historyPage < scanHistory.total_pages) setHistoryPage(historyPage + 1);
                    }}
                    className={historyPage === scanHistory.total_pages ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}

          {/* Информация о пагинации */}
          {scanHistory && !historyLoading && (
            <div className="mt-3 text-xs text-muted-foreground text-center">
              Показано {scanHistory.items.length} из {scanHistory.total} записей
              {scanHistory.total_pages > 1 && ` (страница ${scanHistory.page} из ${scanHistory.total_pages})`}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
