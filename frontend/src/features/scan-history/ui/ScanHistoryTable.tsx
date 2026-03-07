import { Badge } from '@/shared/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table';
import { Skeleton } from '@/shared/ui/skeleton';
import type { ScanHistoryItem } from '@/shared/types';
import { CITIES } from '@/shared/config';
import { CheckCircle, AlertCircle, Clock, FileText, Home, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';

interface ScanHistoryTableProps {
  data?: ScanHistoryItem[];
  isLoading?: boolean;
  emptyMessage?: string;
}

/**
 * Форматирование даты в DD.MM HH:mm (с конвертацией UTC в Europe/Minsk)
 */
const formatDateTime = (dateString: string) => {
  const date = new Date(dateString);
  
  // Проверяем есть ли в строке указание на timezone
  // Если нет - предполагаем что это UTC и добавляем Z
  const normalizedDate = dateString.includes('Z') || dateString.includes('+') 
    ? date 
    : new Date(dateString + 'Z'); // Добавляем Z для UTC
  
  return normalizedDate.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Minsk',
  });
};

/**
 * Форматирование длительности в секундах в человекочитаемый формат
 */
const formatDuration = (seconds: number | null): string => {
  if (seconds === null) return '—';
  if (seconds < 60) return `${seconds} сек`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return secs > 0 ? `${mins} мин ${secs} сек` : `${mins} мин`;
};

/**
 * Компонент статуса сканирования
 */
const StatusBadge = ({ status }: { status: ScanHistoryItem['status'] }) => {
  const variants = {
    completed: 'default' as const,
    error: 'destructive' as const,
    running: 'secondary' as const,
  };

  const icons = {
    completed: <CheckCircle className="w-3 h-3 mr-1" />,
    error: <AlertCircle className="w-3 h-3 mr-1" />,
    running: <Clock className="w-3 h-3 mr-1" />,
  };

  const labels = {
    completed: 'Завершено',
    error: 'Ошибка',
    running: 'В процессе',
  };

  return (
    <Badge variant={variants[status]} className="text-xs font-medium">
      {icons[status]}
      {labels[status]}
    </Badge>
  );
};

/**
 * Компонент типа запуска
 */
const TriggerTypeBadge = ({ type }: { type: ScanHistoryItem['trigger_type'] }) => {
  const variants = {
    manual: 'outline' as const,
    scheduled: 'secondary' as const,
  };

  const labels = {
    manual: 'Ручное',
    scheduled: 'Авто',
  };

  return (
    <Badge variant={variants[type]} className="text-xs">
      {labels[type]}
    </Badge>
  );
};

/**
 * Компонент отображения статистики объявлений
 */
const ListingsStats = ({ item }: { item: ScanHistoryItem }) => {
  return (
    <div className="flex flex-col gap-1 text-xs">
      {item.listings_created > 0 && (
        <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
          <TrendingUp className="w-3 h-3" />
          <span>+{item.listings_created}</span>
        </div>
      )}
      {item.listings_updated > 0 && (
        <div className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
          <RefreshCw className="w-3 h-3" />
          <span>{item.listings_updated}</span>
        </div>
      )}
      {item.listings_deleted > 0 && (
        <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
          <TrendingDown className="w-3 h-3" />
          <span>-{item.listings_deleted}</span>
        </div>
      )}
      {item.listings_created === 0 && item.listings_updated === 0 && item.listings_deleted === 0 && (
        <span className="text-muted-foreground">—</span>
      )}
    </div>
  );
};

/**
 * Skeleton для строки таблицы
 */
const TableSkeletonRow = () => (
  <TableRow>
    <TableCell>
      <Skeleton className="h-4 w-24" />
    </TableCell>
    <TableCell>
      <Skeleton className="h-5 w-20" />
    </TableCell>
    <TableCell>
      <Skeleton className="h-5 w-16" />
    </TableCell>
    <TableCell>
      <Skeleton className="h-5 w-14" />
    </TableCell>
    <TableCell>
      <Skeleton className="h-8 w-16" />
    </TableCell>
    <TableCell>
      <Skeleton className="h-4 w-12" />
    </TableCell>
    <TableCell>
      <Skeleton className="h-4 w-16" />
    </TableCell>
  </TableRow>
);

/**
 * Компонент Empty State
 */
const EmptyState = ({ message }: { message: string }) => (
  <TableRow>
    <TableCell colSpan={7} className="h-24 text-center">
      <div className="flex flex-col items-center justify-center text-muted-foreground">
        <FileText className="w-8 h-8 mb-2 opacity-50" />
        <p className="text-sm">{message}</p>
      </div>
    </TableCell>
  </TableRow>
);

/**
 * Таблица истории сканирований
 *
 * @example
 * ```tsx
 * <ScanHistoryTable data={historyItems} isLoading={false} />
 * ```
 */
export const ScanHistoryTable = ({
  data = [],
  isLoading = false,
  emptyMessage = 'История сканирований пуста',
}: ScanHistoryTableProps) => {
  if (isLoading) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Дата/время</TableHead>
            <TableHead>Город</TableHead>
            <TableHead>Статус</TableHead>
            <TableHead>Тип</TableHead>
            <TableHead>Объявления</TableHead>
            <TableHead>Страниц</TableHead>
            <TableHead>Длительность</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {[...Array(5)].map((_, i) => (
            <TableSkeletonRow key={i} />
          ))}
        </TableBody>
      </Table>
    );
  }

  if (data.length === 0) {
    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Дата/время</TableHead>
            <TableHead>Город</TableHead>
            <TableHead>Статус</TableHead>
            <TableHead>Тип</TableHead>
            <TableHead>Объявления</TableHead>
            <TableHead>Страниц</TableHead>
            <TableHead>Длительность</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <EmptyState message={emptyMessage} />
        </TableBody>
      </Table>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[140px]">Дата/время</TableHead>
          <TableHead className="w-[120px]">Город</TableHead>
          <TableHead className="w-[100px]">Статус</TableHead>
          <TableHead className="w-[80px]">Тип</TableHead>
          <TableHead className="w-[120px]">Объявления</TableHead>
          <TableHead className="w-[80px] text-center">Страниц</TableHead>
          <TableHead className="w-[100px]">Длительность</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((item) => (
          <TableRow key={item.id} className="hover:bg-muted/50 transition-colors">
            <TableCell className="font-medium">
              {formatDateTime(item.started_at)}
            </TableCell>
            <TableCell>
              <Badge variant="outline" className="text-xs">
                <Home className="w-3 h-3 mr-1" />
                {item.city_name}
              </Badge>
            </TableCell>
            <TableCell>
              <StatusBadge status={item.status} />
            </TableCell>
            <TableCell>
              <TriggerTypeBadge type={item.trigger_type} />
            </TableCell>
            <TableCell>
              <ListingsStats item={item} />
            </TableCell>
            <TableCell className="text-center">
              {item.pages_scraped}
            </TableCell>
            <TableCell>
              {formatDuration(item.duration_seconds)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
