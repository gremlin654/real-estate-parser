import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as listingsModule from './listings';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch as any;

describe('API Hooks - listings.ts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('useListingHistory', () => {
    it('fetches history successfully', async () => {
      const mockHistory = [
        { id: '1', event_type: 'created', created_at: '2026-03-01T10:00:00' },
      ];
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistory,
      });

      const { result } = renderHook(() => listingsModule.useListingHistory('123'), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockHistory);
    });

    it('handles fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => listingsModule.useListingHistory('123'), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useSummary', () => {
    it('fetches summary for city', async () => {
      const mockSummary = { city: 'minsk', new_today: 10, active_total: 500 };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockSummary });

      const { result } = renderHook(() => listingsModule.useSummary('minsk'), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockSummary);
    });

    it('fetches summary without city', async () => {
      const mockSummary = { city: 'default', new_today: 0 };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockSummary });

      const { result } = renderHook(() => listingsModule.useSummary(), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useCities', () => {
    it('fetches cities successfully', async () => {
      const mockCities = [{ code: 'minsk', name: 'Минск' }];
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockCities });

      const { result } = renderHook(() => listingsModule.useCities(), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockCities);
    });
  });

  describe('useListings', () => {
    it('fetches listings with filters', async () => {
      const mockListings = { items: [], total: 0 };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockListings });

      const { result } = renderHook(() => listingsModule.useListings(1, 20, { status: 'active', city: 'minsk' }), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });

    it('fetches listings without filters', async () => {
      const mockListings = { items: [], total: 0 };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockListings });

      const { result } = renderHook(() => listingsModule.useListings(), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useListing', () => {
    it('fetches single listing', async () => {
      const mockListing = { id: '123', title: 'Test' };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockListing });

      const { result } = renderHook(() => listingsModule.useListing('123'), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockListing);
    });
  });

  describe('useTriggerScan', () => {
    it('triggers scan successfully', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ message: 'started' }) });

      const { result } = renderHook(() => listingsModule.useTriggerScan(), { wrapper: createWrapper() });

      result.current.mutate({ city: 'minsk' });

      // Just check that mutate was called and fetch was invoked
      await waitFor(() => expect(mockFetch).toHaveBeenCalled());
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/scan/trigger'),
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('handles trigger error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Failed'));

      const { result } = renderHook(() => listingsModule.useTriggerScan(), { wrapper: createWrapper() });

      result.current.mutate({ city: 'minsk' });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('useScanProgress', () => {
    it('fetches scan progress', async () => {
      const mockProgress = { is_scanning: true, stage: 'fetching' };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockProgress });

      const { result } = renderHook(() => listingsModule.useScanProgress(true), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockProgress);
    });
  });

  describe('useScanSchedule', () => {
    it('fetches scan schedule', async () => {
      const mockSchedule = { scan_interval_minutes: 30, enabled: true };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockSchedule });

      const { result } = renderHook(() => listingsModule.useScanSchedule(), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useUpdateScanSchedule', () => {
    it('updates scan schedule', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ success: true }) });

      const { result } = renderHook(() => listingsModule.useUpdateScanSchedule(), { wrapper: createWrapper() });

      result.current.mutate({ scan_interval_minutes: 60, enabled: false });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useScanCity', () => {
    it('fetches current scan city', async () => {
      const mockCity = { city: 'mogilev', city_name: 'Могилёв' };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockCity });

      const { result } = renderHook(() => listingsModule.useScanCity(), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useUpdateScanCity', () => {
    it('updates scan city', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ success: true }) });

      const { result } = renderHook(() => listingsModule.useUpdateScanCity(), { wrapper: createWrapper() });

      result.current.mutate({ city: 'minsk' });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useScanCities', () => {
    it('fetches all available cities', async () => {
      const mockCities = [{ code: 'minsk', name: 'Минск' }];
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockCities });

      const { result } = renderHook(() => listingsModule.useScanCities(), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useScanHistory', () => {
    it('fetches scan history with pagination', async () => {
      const mockHistory = { items: [], total: 0 };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockHistory });

      const { result } = renderHook(() => listingsModule.useScanHistory(1, 20, 'minsk'), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });

    it('fetches scan history without filters', async () => {
      const mockHistory = { items: [], total: 0 };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockHistory });

      const { result } = renderHook(() => listingsModule.useScanHistory(), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useScanHistorySummary', () => {
    it('fetches scan history summary', async () => {
      const mockSummary = { total_scans: 100, completed_scans: 95 };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockSummary });

      const { result } = renderHook(() => listingsModule.useScanHistorySummary('minsk'), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useChangeCity', () => {
    it('changes city successfully', async () => {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ success: true }) });

      const { result } = renderHook(() => listingsModule.useChangeCity(), { wrapper: createWrapper() });

      result.current.mutate({ city: 'minsk' });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('useCurrentCity', () => {
    it('fetches current city', async () => {
      const mockCity = { city: 'mogilev', city_name: 'Могилёв' };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockCity });

      const { result } = renderHook(() => listingsModule.useCurrentCity(), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('usePriceTrends', () => {
    it('fetches price trends for 1-room apartments', async () => {
      const mockTrends = {
        city: 'minsk',
        rooms: 1,
        period_months: 12,
        data: [
          { year: 2024, month: 1, avg_price_usd: 85000, listings_count: 150 },
          { year: 2024, month: 2, avg_price_usd: 87500, listings_count: 165 },
        ],
      };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockTrends });

      const { result } = renderHook(() => listingsModule.usePriceTrends('minsk', 1, 12), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockTrends);
    });

    it('fetches price trends for 2-room apartments', async () => {
      const mockTrends = {
        city: 'mogilev',
        rooms: 2,
        period_months: 6,
        data: [
          { year: 2024, month: 3, avg_price_usd: 65000, listings_count: 80 },
        ],
      };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockTrends });

      const { result } = renderHook(() => listingsModule.usePriceTrends('mogilev', 2, 6), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockTrends);
    });

    it('fetches price trends for 3-room apartments', async () => {
      const mockTrends = {
        city: 'grodno',
        rooms: 3,
        period_months: 24,
        data: [
          { year: 2023, month: 1, avg_price_usd: 95000, listings_count: 50 },
          { year: 2024, month: 1, avg_price_usd: 105000, listings_count: 60 },
        ],
      };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockTrends });

      const { result } = renderHook(() => listingsModule.usePriceTrends('grodno', 3, 24), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockTrends);
    });

    it('fetches price trends for 4-room apartments', async () => {
      const mockTrends = {
        city: 'brest',
        rooms: 4,
        period_months: 12,
        data: [
          { year: 2024, month: 6, avg_price_usd: 150000, listings_count: 30 },
        ],
      };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockTrends });

      const { result } = renderHook(() => listingsModule.usePriceTrends('brest', 4, 12), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockTrends);
    });

    it('handles fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => listingsModule.usePriceTrends('minsk', 2, 12), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });

    it('is disabled when city is empty', async () => {
      const { result } = renderHook(() => listingsModule.usePriceTrends('', 2, 12), { wrapper: createWrapper() });

      // Query should not be enabled
      expect(result.current.isPending).toBe(true);
    });

    it('is disabled when rooms is out of range', async () => {
      const { result } = renderHook(() => listingsModule.usePriceTrends('minsk', 0, 12), { wrapper: createWrapper() });

      expect(result.current.isPending).toBe(true);
    });

    it('uses default period of 12 months', async () => {
      const mockTrends = {
        city: 'minsk',
        rooms: 2,
        period_months: 12,
        data: [],
      };
      mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockTrends });

      const { result } = renderHook(() => listingsModule.usePriceTrends('minsk', 2), { wrapper: createWrapper() });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('period_months=12')
      );
    });
  });
});
