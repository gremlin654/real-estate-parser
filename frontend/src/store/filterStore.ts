import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface FilterState {
  city: string;
  status: string;
  currency: 'BYN' | 'USD';
  priceFrom: number | null;
  priceTo: number | null;
  rooms: number[];
  sortOrder: string;
  page: number;
  isManualScanning: boolean;
  setCity: (city: string) => void;
  setStatus: (status: string) => void;
  setCurrency: (currency: 'BYN' | 'USD') => void;
  setPriceRange: (from: number | null, to: number | null) => void;
  setRooms: (rooms: number[]) => void;
  setSortOrder: (order: string) => void;
  setPage: (page: number) => void;
  setManualScanning: (scanning: boolean) => void;
  reset: () => void;
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set) => ({
      city: 'mogilev',
      status: '',
      currency: 'BYN',
      priceFrom: null,
      priceTo: null,
      rooms: [],
      sortOrder: '',
      page: 1,
      isManualScanning: false,

      setCity: (city) => set({ city, page: 1 }),
      setStatus: (status) => set({ status, page: 1 }),
      setCurrency: (currency) => set({ currency }),
      setPriceRange: (from, to) => set({ priceFrom: from, priceTo: to }),
      setRooms: (rooms) => set({ rooms }),
      setSortOrder: (order) => set({ sortOrder: order }),
      setPage: (page) => set({ page }),
      setManualScanning: (scanning) => set({ isManualScanning: scanning }),
      reset: () => set({
        city: 'mogilev',
        status: '',
        currency: 'BYN',
        priceFrom: null,
        priceTo: null,
        rooms: [],
        sortOrder: '',
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
