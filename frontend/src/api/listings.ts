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
} from '@/shared/types';
import { useFilterStore } from '@/store/filterStore';

const API_BASE = '/api/v1';

/**
 * WebSocket hook для real-time прогресса сканирования.
 * Автоматически подключается к WebSocket при монтировании и отключается при размонтировании.
 * Обновляет данные объявлений после завершения сканирования.
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
  const { setManualScanning } = useFilterStore();
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    // Используем относительный URL для WebSocket
    // Vite dev server проксирует /ws на backend:8000
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/scan/progress`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected to', wsUrl);
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setProgress((prev) => {
            // Если сканирование завершилось, сбрасываем флаг и обновляем данные
            if (prev.is_scanning && !data.is_scanning) {
              setManualScanning(false);
              // Обновить данные объявлений, summary и статистику
              queryClient.invalidateQueries({ queryKey: ['listings'] });
              queryClient.invalidateQueries({ queryKey: ['summary'] });
              queryClient.invalidateQueries({ queryKey: ['stats'] });
              console.log('Scan completed, data invalidated');
            }
            return data;
          });
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);

        // Попытка переподключения через 3 секунды
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [setManualScanning, queryClient]);

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

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { progress, isConnected };
};

export const useListings = (filters: {
  city?: string;
  page?: number;
  size?: number;
  status?: string;
  priceFrom?: number | null;
  priceTo?: number | null;
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
      if (filters.priceFrom) params.set('price_from', String(filters.priceFrom));
      if (filters.priceTo) params.set('price_to', String(filters.priceTo));
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
