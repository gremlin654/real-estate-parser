import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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

const API_BASE = '/api/v1';

export const useListings = (filters: {
  city?: string;
  page?: number;
  size?: number;
  status?: string;
  priceFrom?: number | null;
  priceTo?: number | null;
  rooms?: number[];
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

export const useScanProgress = () => {
  return useQuery<ScanProgress>({
    queryKey: ['scanProgress'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/scan/progress`);
      if (!response.ok) throw new Error('Failed to fetch progress');
      return response.json();
    },
    refetchInterval: 2000,
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
