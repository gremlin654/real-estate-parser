import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { City } from '@/shared/types';

interface FilterState {
  city: string;
  status: string;
  currency: 'BYN' | 'USD';
  priceFrom: number | null;
  priceTo: number | null;
  rooms: number[];
  sort: string;
  size: number;
  page: number;
  isManualScanning: boolean;
  setCity: (city: string) => void;
  setStatus: (status: string) => void;
  setCurrency: (currency: 'BYN' | 'USD') => void;
  setPriceRange: (from: number | null, to: number | null) => void;
  setRooms: (rooms: number[]) => void;
  setFilters: (filters: Partial<FilterState>) => void;
  setPage: (page: number) => void;
  setManualScanning: (scanning: boolean) => void;
  reset: () => void;
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      city: 'mogilev',
      status: 'all',
      currency: 'USD',
      priceFrom: null,
      priceTo: null,
      rooms: [],
      sort: 'newest',
      size: 20,
      page: 1,
      isManualScanning: false,

      setCity: (city) => set({ city, page: 1 }),
      setStatus: (status) => set({ status, page: 1 }),
      setCurrency: (currency) => set({ currency }),
      setPriceRange: (from, to) => set({ priceFrom: from, priceTo: to, page: 1 }),
      setRooms: (rooms) => set({ rooms, page: 1 }),
      setFilters: (filters) => set({ ...filters, page: 1 }),
      setPage: (page) => set({ page }),
      setManualScanning: (scanning) => set({ isManualScanning: scanning }),
      reset: () =>
        set({
          city: 'mogilev',
          status: 'all',
          currency: 'USD',
          priceFrom: null,
          priceTo: null,
          rooms: [],
          sort: 'newest',
          size: 20,
          page: 1,
        }),
    }),
    {
      name: 'filter-storage',
      partialize: (state) => ({
        city: state.city,
        currency: state.currency,
      }),
    }
  )
);
