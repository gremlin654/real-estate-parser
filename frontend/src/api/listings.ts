import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = '/api/v1';

export interface Listing {
  id: string;
  kufar_id: string;
  url: string;
  title: string;
  price: number;
  price_usd?: number | null;
  currency: string;
  city: string | null;
  address: string | null;
  rooms: number | null;
  area: number | null;
  floor: number | null;
  images: string[];
  status: string;
  first_seen_at: string;
  last_seen_at: string;
}

export interface PaginatedResponse {
  items: Listing[];
  total: number;
  page: number;
  size: number;
}

export interface Summary {
  new_today: number;
  deleted_today: number;
  price_changed_usd_today: number;
  active_total: number;
}

export interface ScanProgress {
  is_scanning: boolean;
  city: string | null;
  stage: string;
  pages_scraped: number;
  listings_fetched: number;
  elapsed_seconds: number;
}

export interface HistoryEvent {
  id: string;
  event_type: string;
  price_before?: number | null;
  price_after?: number | null;
  created_at: string;
}

export const useListings = (filters: { city?: string; page?: number; size?: number }) => {
  return useQuery<PaginatedResponse>({
    queryKey: ['listings', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.city) params.set('city', filters.city);
      if (filters.page) params.set('page', String(filters.page));
      if (filters.size) params.set('size', String(filters.size));

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
