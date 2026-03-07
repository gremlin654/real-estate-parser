'use client';

import { useEffect, useState } from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/shared/ui/accordion';
import { Badge } from '@/shared/ui/badge';
import type { ScanHistoryItem } from '@/shared/types';
import { CITIES } from '@/shared/config';
import { ScanHistoryTable } from './ScanHistoryTable';
import { Home, ChevronRight } from 'lucide-react';

interface ScanHistoryGroupedProps {
  data?: ScanHistoryItem[];
  isLoading?: boolean;
  emptyMessage?: string;
}

/**
 * Ключ для localStorage
 */
const EXPANDED_CITIES_KEY = 'scan-history-expanded-cities';

/**
 * Компонент группировки истории сканирований по городам
 *
 * Использует Accordion для каждого города, сохраняет состояние
 * развёрнутости в localStorage.
 *
 * @example
 * ```tsx
 * <ScanHistoryGrouped data={historyItems} />
 * ```
 */
export const ScanHistoryGrouped = ({
  data = [],
  isLoading = false,
  emptyMessage = 'История сканирований пуста',
}: ScanHistoryGroupedProps) => {
  // Состояние развёрнутых городов
  const [expandedCities, setExpandedCities] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(EXPANDED_CITIES_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Сохранение состояния в localStorage
  useEffect(() => {
    try {
      localStorage.setItem(EXPANDED_CITIES_KEY, JSON.stringify(expandedCities));
    } catch {
      // Игнорируем ошибки localStorage
    }
  }, [expandedCities]);

  // Группировка данных по городам
  const groupedByCity = data.reduce<Record<string, ScanHistoryItem[]>>((acc, item) => {
    if (!acc[item.city]) {
      acc[item.city] = [];
    }
    acc[item.city].push(item);
    return acc;
  }, {});

  // Сортировка городов по алфавиту
  const sortedCities = Object.keys(groupedByCity).sort((a, b) => {
    const nameA = CITIES[a as keyof typeof CITIES] || a;
    const nameB = CITIES[b as keyof typeof CITIES] || b;
    return nameA.localeCompare(nameB);
  });

  // Обработчик изменения развёрнутости
  const handleValueChange = (value: string[]) => {
    setExpandedCities(value);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="rounded-lg border bg-card p-4">
            <div className="flex items-center gap-2 mb-4">
              <div className="h-5 w-5 rounded bg-muted animate-pulse" />
              <div className="h-4 w-32 bg-muted animate-pulse rounded" />
              <Badge variant="secondary" className="ml-auto">
                <div className="h-3 w-8 bg-muted animate-pulse rounded" />
              </Badge>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
        <Home className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <Accordion
      type="multiple"
      value={expandedCities}
      onValueChange={handleValueChange}
      aria-label="История сканирований по городам"
      role="region"
      className="space-y-3"
    >
      {sortedCities.map((city) => {
        const items = groupedByCity[city];
        const cityName = CITIES[city as keyof typeof CITIES] || city;
        const scanCount = items.length;

        return (
          <AccordionItem key={city} value={city} className="border rounded-lg bg-card overflow-hidden">
            <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 text-primary">
                  <Home className="w-4 h-4" />
                </div>
                <div className="text-left">
                  <p className="font-medium">{cityName}</p>
                  <p className="text-xs text-muted-foreground">
                    {scanCount} {scanCount === 1 ? 'сканирование' : scanCount < 5 ? 'сканирования' : 'сканирований'}
                  </p>
                </div>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4 pt-2">
              <ScanHistoryTable data={items} isLoading={false} emptyMessage="Нет данных" />
            </AccordionContent>
          </AccordionItem>
        );
      })}
    </Accordion>
  );
};
