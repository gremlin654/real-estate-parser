import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { City } from '@/shared/types';

export interface ScanningCity {
  city: string;
  city_name: string;
  trigger_type: 'manual' | 'scheduled';
  started_at: string;
  progress: number;
  stage: string;
  elapsed_seconds?: number;
  pages_scraped?: number;
  listings_fetched?: number;
  listings_processed?: number;
}

interface FilterState {
  city: string;
  status: string;
  currency: 'BYN' | 'USD';
  priceFrom: number | null;
  priceTo: number | null;
  pricePerM2Min: number | null;
  pricePerM2Max: number | null;
  rooms: number[];
  roomsOther: boolean;
  sort: string;
  size: number;
  page: number;
  isManualScanning: boolean;
  scanningCities: Map<string, ScanningCity>;
  setCity: (city: string) => void;
  setStatus: (status: string) => void;
  setCurrency: (currency: 'BYN' | 'USD') => void;
  setPriceRange: (from: number | null, to: number | null) => void;
  setPricePerM2Range: (min: number | null, max: number | null) => void;
  setRooms: (rooms: number[], other?: boolean) => void;
  setFilters: (filters: Partial<FilterState>) => void;
  setPage: (page: number) => void;
  setManualScanning: (scanning: boolean) => void;
  addScanningCity: (city: ScanningCity) => void;
  removeScanningCity: (city: string) => void;
  updateScanningCity: (city: string, progress: Partial<ScanningCity>) => void;
  getScanningCities: () => ScanningCity[];
  isCityScanning: (city: string) => boolean;
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
      pricePerM2Min: null,
      pricePerM2Max: null,
      rooms: [],
      roomsOther: false,
      sort: 'newest',
      size: 20,
      page: 1,
      isManualScanning: false,
      scanningCities: new Map(),

      setCity: (city) => set({ city, page: 1 }),
      setStatus: (status) => set({ status, page: 1 }),
      setCurrency: (currency) => set({ currency }),
      setPriceRange: (from, to) => set({ priceFrom: from, priceTo: to, page: 1 }),
      setPricePerM2Range: (min, max) => set({ pricePerM2Min: min, pricePerM2Max: max, page: 1 }),
      setRooms: (rooms, other) => set({ rooms, roomsOther: other ?? false, page: 1 }),
      setFilters: (filters) => set({ ...filters, page: 1 }),
      setPage: (page) => set({ page }),
      setManualScanning: (scanning) => set({ isManualScanning: scanning }),
      
      addScanningCity: (cityData) => {
        set((state) => {
          const newMap = new Map(state.scanningCities);
          newMap.set(cityData.city, cityData);
          return { scanningCities: newMap };
        });
      },
      
      removeScanningCity: (city) => {
        set((state) => {
          const newMap = new Map(state.scanningCities);
          newMap.delete(city);
          return { scanningCities: newMap };
        });
      },
      
      updateScanningCity: (city, progress) => {
        // Throttle: обновляем только если изменились значимые данные
        set((state) => {
          const newMap = new Map(state.scanningCities);
          const existing = newMap.get(city);
          
          if (existing) {
            // Не обновляем если прогресс не изменился (защита от лишних ре-рендеров)
            if (
              existing.progress === progress.progress &&
              existing.stage === progress.stage &&
              existing.elapsed_seconds === progress.elapsed_seconds
            ) {
              return state; // Нет изменений
            }
            
            newMap.set(city, { ...existing, ...progress });
          }
          return { scanningCities: newMap };
        });
      },
      
      getScanningCities: () => {
        return Array.from(get().scanningCities.values());
      },
      
      isCityScanning: (city) => {
        return get().scanningCities.has(city);
      },
      
      reset: () =>
        set({
          city: 'mogilev',
          status: 'all',
          currency: 'USD',
          priceFrom: null,
          priceTo: null,
          pricePerM2Min: null,
          pricePerM2Max: null,
          rooms: [],
          roomsOther: false,
          sort: 'newest',
          size: 20,
          page: 1,
          isManualScanning: false,
          scanningCities: new Map(),
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
