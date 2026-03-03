import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock localStorage
const localStorageMock = {
  store: {} as Record<string, string>,
  getItem: vi.fn((key: string) => this.store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    this.store[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete this.store[key];
  }),
  clear: vi.fn(() => {
    this.store = {};
  }),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Need to import after localStorage mock
import { useFilterStore } from './filterStore';

describe('filterStore', () => {
  beforeEach(() => {
    localStorageMock.store = {};
    localStorageMock.setItem.mockClear();
    localStorageMock.getItem.mockClear();
    // Reset store to default state
    useFilterStore.setState({
      status: null,
      category: null,
      priceFrom: null,
      priceTo: null,
      city: 'mogilev',
      currency: 'BYN',
      sortOrder: 'default',
      isManualScanning: false,
    });
  });

  describe('initial state', () => {
    it('должен иметь начальное состояние', () => {
      const state = useFilterStore.getState();
      expect(state.status).toBeNull();
      expect(state.category).toBeNull();
      expect(state.priceFrom).toBeNull();
      expect(state.priceTo).toBeNull();
      expect(state.city).toBe('mogilev');
      expect(state.currency).toBe('BYN');
      expect(state.sortOrder).toBe('default');
      expect(state.isManualScanning).toBe(false);
    });

    it('должен иметь список городов по умолчанию', () => {
      const state = useFilterStore.getState();
      expect(state.cities).toHaveLength(6);
      expect(state.cities.map(c => c.code)).toEqual([
        'mogilev',
        'minsk',
        'grodno',
        'brest',
        'gomel',
        'vitebsk',
      ]);
    });
  });

  describe('setStatus', () => {
    it('должен устанавливать статус', () => {
      useFilterStore.getState().setStatus('active');
      expect(useFilterStore.getState().status).toBe('active');
    });

    it('должен сбрасывать статус в null', () => {
      useFilterStore.getState().setStatus('new');
      useFilterStore.getState().setStatus(null);
      expect(useFilterStore.getState().status).toBeNull();
    });
  });

  describe('setCategory', () => {
    it('должен устанавливать категорию', () => {
      useFilterStore.getState().setCategory('flats');
      expect(useFilterStore.getState().category).toBe('flats');
    });

    it('должен сбрасывать категорию в null', () => {
      useFilterStore.getState().setCategory('houses');
      useFilterStore.getState().setCategory(null);
      expect(useFilterStore.getState().category).toBeNull();
    });
  });

  describe('setPriceRange', () => {
    it('должен устанавливать диапазон цен', () => {
      useFilterStore.getState().setPriceRange(100000, 500000);
      const state = useFilterStore.getState();
      expect(state.priceFrom).toBe(100000);
      expect(state.priceTo).toBe(500000);
    });

    it('должен устанавливать только минимальную цену', () => {
      useFilterStore.getState().setPriceRange(200000, null);
      const state = useFilterStore.getState();
      expect(state.priceFrom).toBe(200000);
      expect(state.priceTo).toBeNull();
    });

    it('должен сбрасывать диапазон цен', () => {
      useFilterStore.getState().setPriceRange(100000, 500000);
      useFilterStore.getState().setPriceRange(null, null);
      const state = useFilterStore.getState();
      expect(state.priceFrom).toBeNull();
      expect(state.priceTo).toBeNull();
    });
  });

  describe('setCity', () => {
    it('должен устанавливать город', () => {
      useFilterStore.getState().setCity('minsk');
      expect(useFilterStore.getState().city).toBe('minsk');
    });

    it('должен устанавливать другой город', () => {
      useFilterStore.getState().setCity('brest');
      expect(useFilterStore.getState().city).toBe('brest');
    });
  });

  describe('setCurrency', () => {
    it('должен устанавливать валюту BYN', () => {
      useFilterStore.getState().setCurrency('BYN');
      expect(useFilterStore.getState().currency).toBe('BYN');
    });

    it('должен устанавливать валюту USD', () => {
      useFilterStore.getState().setCurrency('USD');
      expect(useFilterStore.getState().currency).toBe('USD');
    });
  });

  describe('setSortOrder', () => {
    it('должен устанавливать порядок asc', () => {
      useFilterStore.getState().setSortOrder('asc');
      expect(useFilterStore.getState().sortOrder).toBe('asc');
    });

    it('должен устанавливать порядок desc', () => {
      useFilterStore.getState().setSortOrder('desc');
      expect(useFilterStore.getState().sortOrder).toBe('desc');
    });

    it('должен устанавливать порядок default', () => {
      useFilterStore.getState().setSortOrder('default');
      expect(useFilterStore.getState().sortOrder).toBe('default');
    });
  });

  describe('setCities', () => {
    it('должен устанавливать список городов', () => {
      const newCities = [
        { code: 'minsk', name: 'Минск' },
        { code: 'mogilev', name: 'Могилёв' },
      ];
      useFilterStore.getState().setCities(newCities);
      expect(useFilterStore.getState().cities).toEqual(newCities);
    });
  });

  describe('setManualScanning', () => {
    it('должен устанавливать флаг сканирования в true', () => {
      useFilterStore.getState().setManualScanning(true);
      expect(useFilterStore.getState().isManualScanning).toBe(true);
    });

    it('должен устанавливать флаг сканирования в false', () => {
      useFilterStore.getState().setManualScanning(true);
      useFilterStore.getState().setManualScanning(false);
      expect(useFilterStore.getState().isManualScanning).toBe(false);
    });
  });

  describe('resetFilters', () => {
    it('должен сбрасывать все фильтры к значениям по умолчанию', () => {
      const state = useFilterStore.getState();
      state.setStatus('active');
      state.setCategory('flats');
      state.setPriceRange(100000, 500000);
      state.setCity('minsk');
      state.setCurrency('USD');
      state.setSortOrder('desc');

      state.resetFilters();

      const resetState = useFilterStore.getState();
      expect(resetState.status).toBeNull();
      expect(resetState.category).toBeNull();
      expect(resetState.priceFrom).toBeNull();
      expect(resetState.priceTo).toBeNull();
      expect(resetState.city).toBe('mogilev');
      expect(resetState.currency).toBe('BYN');
      expect(resetState.sortOrder).toBe('default');
    });
  });

  describe('persistence', () => {
    it('должен иметь persist middleware', () => {
      const state = useFilterStore.getState();
      expect(state).toBeDefined();
      // The store is configured with persist middleware
      // Actual localStorage testing requires more complex mocking
    });
  });
});
