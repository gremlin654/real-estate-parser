import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, useCallback, useRef } from 'react';
import type {
  Listing,
  PaginatedResponse,
  Summary,
  ScanProgress,
  HistoryEvent,
  PriceTrendsResponse,
  RoomDistributionResponse,
  DailyActivityResponse,
  ScanSchedule,
  CityComparisonData,
  ScanHistoryResponse,
  CitySettingsResponse,
  CitySettingsUpdateRequest,
  PricePerM2Stats,
  PricePerM2TrendsResponse,
  PricePerM2DistributionResponse,
} from '@/shared/types';
import { useFilterStore } from '@/store/filterStore';
import { toast } from 'sonner';
import { calculateProgress } from '@/shared/lib/scan-progress';

const API_BASE = '/api/v1';

/**
 * WebSocket hook для real-time прогресса сканирования.
 * Автоматически подключается к WebSocket при монтировании и отключается при размонтировании.
 * Обновляет данные объявлений после завершения сканирования.
 * Поддерживает параллельные сканирования по городам (v3.1).
 * 
 * Исправления (v3.1.1):
 * - Кэширование методов store через useRef для стабильной идентичности
 * - connect/disconnect стабилизированы через useRef
 * - setProgress вызывается только при реальном изменении данных
 * - WebSocket переподключается только при реальном разрыве соединения
 */
export const useScanProgressWebSocket = () => {
  const [progress, setProgress] = useState<ScanProgress>({
    is_scanning: false,
    city: null,
    city_name: undefined,
    stage: 'idle',
    pages_scraped: 0,
    listings_fetched: 0,
    listings_processed: 0,
    elapsed_seconds: 0,
    is_stable: true,
  });
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const queryClient = useQueryClient();

  // 🔧 ИСПРАВЛЕНИЕ 1: Используем useRef для стабильной ссылки на store методы
  // Это предотвращает пересоздание connect при каждом рендере
  const store = useFilterStore();
  const storeMethodsRef = useRef({
    getScanningCities: store.getScanningCities,
    addScanningCity: store.addScanningCity,
    removeScanningCity: store.removeScanningCity,
    updateScanningCity: store.updateScanningCity,
  });

  // Обновляем ref только когда методы реально меняются (не при каждом рендере)
  storeMethodsRef.current = {
    getScanningCities: store.getScanningCities,
    addScanningCity: store.addScanningCity,
    removeScanningCity: store.removeScanningCity,
    updateScanningCity: store.updateScanningCity,
  };

  // 🔧 ИСПРАВЛЕНИЕ 2: connect стабилизирован - пустые зависимости
  // storeMethodsRef.current всегда актуален благодаря ref
  const connect = useCallback(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/scan/progress`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const storeMethods = storeMethodsRef.current;

          // Поддержка параллельных сканирований (v3.1)
          if (data.scanning_cities) {
            const activeCities = data.scanning_cities.map((s: any) => s.city);
            const currentScanningCities = storeMethods.getScanningCities();

            // Обновить или добавить активные сканирования
            data.scanning_cities.forEach((scan: any) => {
              const progressPercent = calculateProgress(scan);
              const existing = currentScanningCities.find((s) => s.city === scan.city);

              if (existing) {
                storeMethods.updateScanningCity(scan.city, {
                  progress: progressPercent,
                  stage: scan.stage,
                  elapsed_seconds: scan.elapsed_seconds,
                  pages_scraped: scan.pages_scraped,
                  listings_fetched: scan.listings_fetched,
                  listings_processed: scan.listings_processed,
                });
              } else {
                storeMethods.addScanningCity({
                  city: scan.city,
                  city_name: scan.city_name,
                  trigger_type: scan.trigger_type,
                  started_at: new Date().toISOString(),
                  progress: progressPercent,
                  stage: scan.stage,
                  elapsed_seconds: scan.elapsed_seconds,
                  pages_scraped: scan.pages_scraped,
                  listings_fetched: scan.listings_fetched,
                  listings_processed: scan.listings_processed,
                });
              }
            });

            // Удалить завершённые сканирования
            currentScanningCities.forEach((s) => {
              if (!activeCities.includes(s.city)) {
                storeMethods.removeScanningCity(s.city);
                // Инвалидировать кэш после завершения
                queryClient.invalidateQueries({ queryKey: ['scanHistory'] });
                queryClient.invalidateQueries({ queryKey: ['listings'] });
                queryClient.invalidateQueries({ queryKey: ['summary'] });
              }
            });
          }

          // 🔧 ИСПРАВЛЕНИЕ 3: Сравниваем данные ПЕРЕД вызовом setProgress
          // Это предотвращает лишние ре-рендеры
          setProgress((prev) => {
            const hasChanges =
              prev.is_scanning !== data.is_scanning ||
              prev.stage !== data.stage ||
              prev.city !== data.city ||
              prev.pages_scraped !== data.pages_scraped ||
              prev.listings_fetched !== data.listings_fetched ||
              prev.listings_processed !== data.listings_processed ||
              prev.elapsed_seconds !== data.elapsed_seconds;

            if (hasChanges) {
              return data;
            }
            return prev;
          });
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        setIsConnected(false);

        // Попытка переподключения через 3 секунды
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      wsRef.current = ws;
    } catch (error) {
      // Failed to create WebSocket
    }
  }, [queryClient]); // 🔧 Только queryClient в зависимостях

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // 🔧 ИСПРАВЛЕНИЕ 4: useEffect с пустыми зависимостями - запускается 1 раз
  useEffect(() => {
    connect();
    return () => disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { progress, isConnected };
};

export const useListings = (filters: {
  city?: string;
  page?: number;
  size?: number;
  status?: string;
  priceFrom?: number | null;
  priceTo?: number | null;
  pricePerM2Min?: number | null;
  pricePerM2Max?: number | null;
  rooms?: number[];
  roomsOther?: boolean;
  currency?: string;
  sort?: string;
}) => {
  return useQuery<PaginatedResponse>({
    queryKey: ['listings', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.city) params.set('city', filters.city);
      if (filters.page) params.set('page', String(filters.page));
      if (filters.size) params.set('size', String(filters.size));
      if (filters.status) params.set('status', filters.status);
      if (filters.priceFrom !== null && filters.priceFrom !== undefined) {
        params.set('price_from', String(filters.priceFrom));
      }
      if (filters.priceTo !== null && filters.priceTo !== undefined) {
        params.set('price_to', String(filters.priceTo));
      }
      if (filters.pricePerM2Min !== null && filters.pricePerM2Min !== undefined) {
        params.set('price_per_m2_min', String(filters.pricePerM2Min));
      }
      if (filters.pricePerM2Max !== null && filters.pricePerM2Max !== undefined) {
        params.set('price_per_m2_max', String(filters.pricePerM2Max));
      }
      if (filters.rooms && filters.rooms.length > 0) {
        filters.rooms.forEach((room) => params.append('rooms', String(room)));
      }
      if (filters.roomsOther) {
        params.set('rooms_other', 'true');
      }
      // currency используется только для отображения на frontend, не передаём на backend

      // Маппинг значений сортировки
      if (filters.sort) {
        const sortMap: Record<string, string> = {
          'newest': 'newest',
          'oldest': 'oldest',
          'price_asc': 'asc',
          'price_desc': 'desc',
        };
        params.set('sort_order', sortMap[filters.sort] || filters.sort);
      }

      const response = await fetch(`${API_BASE}/listings?${params}`);
      if (!response.ok) throw new Error('Failed to fetch listings');
      return response.json();
    },
  });
};

export const useListing = (id: string) => {
  return useQuery<Listing>({
    queryKey: ['listing', id],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/listings/${id}`);
      if (!response.ok) throw new Error('Failed to fetch listing');
      return response.json();
    },
    enabled: !!id,
  });
};

export const useSummary = (city?: string) => {
  return useQuery<Summary>({
    queryKey: ['summary', city],
    queryFn: async () => {
      const params = city ? `?city=${city}` : '';
      const response = await fetch(`${API_BASE}/stats/summary${params}`);
      if (!response.ok) throw new Error('Failed to fetch summary');
      return response.json();
    },
  });
};

export const useManualScan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ city }: { city: string }) => {
      const response = await fetch(`${API_BASE}/scan/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city }),
      });
      if (!response.ok) throw new Error('Failed to trigger scan');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] });
      queryClient.invalidateQueries({ queryKey: ['summary'] });
    },
  });
};

export const useListingHistory = (listingId: string) => {
  return useQuery<HistoryEvent[]>({
    queryKey: ['history', listingId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/history/${listingId}`);
      if (!response.ok) throw new Error('Failed to fetch history');
      return response.json();
    },
    enabled: !!listingId,
  });
};

export const usePriceTrends = (city?: string, rooms?: number, periodMonths?: number) => {
  return useQuery<PriceTrendsResponse>({
    queryKey: ['priceTrends', city, rooms, periodMonths],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (city) params.set('city', city);
      if (rooms) params.set('rooms', String(rooms));
      if (periodMonths) params.set('period_months', String(periodMonths));

      const response = await fetch(`${API_BASE}/stats/price-trends?${params}`);
      if (!response.ok) throw new Error('Failed to fetch price trends');
      return response.json();
    },
    enabled: !!city && !!rooms,
  });
};

export const useRoomDistribution = (city?: string) => {
  return useQuery<RoomDistributionResponse>({
    queryKey: ['roomDistribution', city],
    queryFn: async () => {
      const params = city ? `?city=${city}` : '';
      const response = await fetch(`${API_BASE}/stats/room-distribution${params}`);
      if (!response.ok) throw new Error('Failed to fetch room distribution');
      return response.json();
    },
    enabled: !!city,
  });
};

export const useDailyActivity = (city?: string, periodDays?: number) => {
  return useQuery<DailyActivityResponse>({
    queryKey: ['dailyActivity', city, periodDays],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (city) params.set('city', city);
      if (periodDays) params.set('period_days', String(periodDays));

      const response = await fetch(`${API_BASE}/stats/daily-activity?${params}`);
      if (!response.ok) throw new Error('Failed to fetch daily activity');
      return response.json();
    },
    enabled: !!city,
  });
};

export const useScanSchedule = () => {
  return useQuery<ScanSchedule>({
    queryKey: ['scanSchedule'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/scan/schedule`);
      if (!response.ok) throw new Error('Failed to fetch scan schedule');
      return response.json();
    },
  });
};

export const useUpdateScanSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { scan_interval_minutes: number; enabled: boolean }) => {
      const response = await fetch(`${API_BASE}/scan/schedule`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update scan schedule');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scanSchedule'] });
      queryClient.invalidateQueries({ queryKey: ['scanStatus'] });
    },
  });
};

export const useCurrentScanCity = () => {
  return useQuery<string>({
    queryKey: ['currentScanCity'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/scan/city`);
      if (!response.ok) throw new Error('Failed to fetch current city');
      const data = await response.json();
      return data.city;
    },
  });
};

export const useUpdateCurrentCity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { city: string }) => {
      const response = await fetch(`${API_BASE}/scan/city`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update city');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['currentScanCity'] });
      queryClient.invalidateQueries({ queryKey: ['scanSchedule'] });
    },
  });
};

export const useScanCities = () => {
  return useQuery<string[]>({
    queryKey: ['scanCities'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/scan/cities`);
      if (!response.ok) throw new Error('Failed to fetch cities');
      const data = await response.json();
      return data.cities || [];
    },
    initialData: [],
  });
};

export const useCityComparison = () => {
  return useQuery<CityComparisonData>({
    queryKey: ['cityComparison'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/stats/city-comparison`);
      if (!response.ok) throw new Error('Failed to fetch city comparison');
      return response.json();
    },
  });
};

export const useScanHistory = (filters?: {
  page?: number;
  size?: number;
  city?: string;
  status?: 'running' | 'completed' | 'error';
  trigger_type?: 'manual' | 'scheduled';
  date_from?: string;
  date_to?: string;
}) => {
  return useQuery<ScanHistoryResponse>({
    queryKey: ['scanHistory', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.size) params.set('size', String(filters.size));
      if (filters?.city) params.set('city', filters.city);
      if (filters?.status) params.set('status', filters.status);
      if (filters?.trigger_type) params.set('trigger_type', filters.trigger_type);
      if (filters?.date_from) params.set('date_from', filters.date_from);
      if (filters?.date_to) params.set('date_to', filters.date_to);

      const response = await fetch(`${API_BASE}/scan/history?${params}`);
      if (!response.ok) throw new Error('Failed to fetch scan history');
      return response.json();
    },
    staleTime: 30 * 1000, // 30 секунд
    retry: 2,
    retryDelay: 1000,
  });
};

/**
 * Hook для получения настроек сканирования для конкретного города
 */
export const useCityScanSettings = (city: string) => {
  return useQuery<CitySettingsResponse>({
    queryKey: ['scanSettings', city],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/scan/settings/${city}`);
      if (!response.ok) throw new Error('Failed to fetch settings');
      return response.json();
    },
    enabled: !!city,
    staleTime: 60 * 1000, // 1 минута
  });
};

/**
 * Hook для получения всех настроек сканирования
 */
export const useAllScanSettings = () => {
  return useQuery<Record<string, CitySettingsResponse>>({
    queryKey: ['allScanSettings'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/scan/settings`);
      if (!response.ok) throw new Error('Failed to fetch settings');
      return response.json();
    },
    staleTime: 60 * 1000,
  });
};

/**
 * Hook для обновления настроек сканирования города
 */
export const useUpdateCityScanSettings = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ city, data }: { city: string; data: CitySettingsUpdateRequest }) => {
      const response = await fetch(`${API_BASE}/scan/settings/${city}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update settings');
      return response.json();
    },
    onSuccess: (data, { city }) => {
      queryClient.invalidateQueries({ queryKey: ['scanSettings', city] });
      queryClient.invalidateQueries({ queryKey: ['allScanSettings'] });
      toast.success('Настройки сохранены');
    },
    onError: (error) => {
      toast.error('Ошибка сохранения: ' + error.message);
    },
  });
};

/**
 * Hook для получения статуса сканирования (поддержка параллельных сканирований).
 * Polling каждые 5 секунд.
 */
export const useScanStatus = () => {
  return useQuery<{
    scanning_cities?: Array<{
      city: string;
      city_name: string;
      trigger_type: 'manual' | 'scheduled';
      stage: string;
      pages_scraped: number;
      listings_fetched: number;
      listings_processed: number;
      elapsed_seconds: number;
      is_stable: boolean;
    }>;
    is_scanning?: boolean;
    city?: string | null;
  }>({
    queryKey: ['scanStatus'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/scan/status`);
      if (!response.ok) throw new Error('Failed to fetch scan status');
      return response.json();
    },
    refetchInterval: 5000, // Polling каждые 5 секунд
    retry: 2,
    retryDelay: 1000,
  });
};

/**
 * Hook для получения статистики цены за м²
 */
export const usePricePerM2Stats = (filters: {
  city: string;
  rooms?: number;
  currency?: 'byn' | 'usd';
}) => {
  return useQuery<PricePerM2Stats>({
    queryKey: ['pricePerM2Stats', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.city) params.set('city', filters.city);
      if (filters.rooms) params.set('rooms', String(filters.rooms));
      if (filters.currency) params.set('currency', filters.currency);

      const response = await fetch(`${API_BASE}/stats/price-per-m2?${params}`);
      if (!response.ok) throw new Error('Failed to fetch price per m² stats');
      return response.json();
    },
    enabled: !!filters.city,
    staleTime: 5 * 60 * 1000, // 5 минут
  });
};

/**
 * Hook для получения трендов цены за м²
 */
export const usePricePerM2Trends = (filters: {
  city: string;
  rooms?: number;
  period_days?: number;
  interval?: 'day' | 'week' | 'month';
  currency?: 'byn' | 'usd';
}) => {
  return useQuery<PricePerM2TrendsResponse>({
    queryKey: ['pricePerM2Trends', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.city) params.set('city', filters.city);
      if (filters.rooms) params.set('rooms', String(filters.rooms));
      if (filters.period_days) params.set('period_days', String(filters.period_days));
      if (filters.interval) params.set('interval', filters.interval);
      if (filters.currency) params.set('currency', filters.currency);

      const response = await fetch(`${API_BASE}/stats/price-per-m2-trends?${params}`);
      if (!response.ok) throw new Error('Failed to fetch price per m² trends');
      return response.json();
    },
    enabled: !!filters.city,
    staleTime: 5 * 60 * 1000, // 5 минут
  });
};

/**
 * Hook для получения распределения цены за м²
 */
export const usePricePerM2Distribution = (filters: {
  city: string;
  rooms?: number;
  bins?: number;
  currency?: 'byn' | 'usd';
}) => {
  return useQuery<PricePerM2DistributionResponse>({
    queryKey: ['pricePerM2Distribution', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.city) params.set('city', filters.city);
      if (filters.rooms) params.set('rooms', String(filters.rooms));
      if (filters.bins) params.set('bins', String(filters.bins));
      if (filters.currency) params.set('currency', filters.currency);

      const response = await fetch(`${API_BASE}/stats/price-per-m2-distribution?${params}`);
      if (!response.ok) throw new Error('Failed to fetch price per m² distribution');
      return response.json();
    },
    enabled: !!filters.city,
    staleTime: 5 * 60 * 1000, // 5 минут
  });
};
