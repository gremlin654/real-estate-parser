import { describe, it, expect, beforeEach } from 'vitest';
import { useFilterStore } from './filterStore';

describe('filterStore - scanningCities', () => {
  beforeEach(() => {
    // Сбросить store перед каждым тестом
    useFilterStore.getState().reset();
  });

  it('должен начинать с пустой Map scanningCities', () => {
    const { getScanningCities } = useFilterStore.getState();
    expect(getScanningCities()).toEqual([]);
  });

  it('должен добавлять город в scanningCities', () => {
    const { addScanningCity, getScanningCities } = useFilterStore.getState();
    
    addScanningCity({
      city: 'minsk',
      city_name: 'Минск',
      trigger_type: 'manual',
      started_at: '2024-01-01T00:00:00Z',
      progress: 0,
      stage: 'starting',
    });

    const cities = getScanningCities();
    expect(cities).toHaveLength(1);
    expect(cities[0].city).toBe('minsk');
    expect(cities[0].city_name).toBe('Минск');
  });

  it('должен добавлять несколько городов в scanningCities', () => {
    const { addScanningCity, getScanningCities } = useFilterStore.getState();
    
    addScanningCity({
      city: 'minsk',
      city_name: 'Минск',
      trigger_type: 'manual',
      started_at: '2024-01-01T00:00:00Z',
      progress: 0,
      stage: 'starting',
    });

    addScanningCity({
      city: 'mogilev',
      city_name: 'Могилёв',
      trigger_type: 'scheduled',
      started_at: '2024-01-01T00:00:00Z',
      progress: 50,
      stage: 'parsing',
    });

    const cities = getScanningCities();
    expect(cities).toHaveLength(2);
    expect(cities.map((c) => c.city)).toContain('minsk');
    expect(cities.map((c) => c.city)).toContain('mogilev');
  });

  it('должен обновлять прогресс города', () => {
    const { addScanningCity, updateScanningCity, getScanningCities } = useFilterStore.getState();
    
    addScanningCity({
      city: 'minsk',
      city_name: 'Минск',
      trigger_type: 'manual',
      started_at: '2024-01-01T00:00:00Z',
      progress: 0,
      stage: 'starting',
    });

    updateScanningCity('minsk', {
      progress: 50,
      stage: 'fetching',
      elapsed_seconds: 30,
    });

    const cities = getScanningCities();
    expect(cities).toHaveLength(1);
    expect(cities[0].progress).toBe(50);
    expect(cities[0].stage).toBe('fetching');
    expect(cities[0].elapsed_seconds).toBe(30);
  });

  it('должен удалять город из scanningCities', () => {
    const { addScanningCity, removeScanningCity, getScanningCities } = useFilterStore.getState();
    
    addScanningCity({
      city: 'minsk',
      city_name: 'Минск',
      trigger_type: 'manual',
      started_at: '2024-01-01T00:00:00Z',
      progress: 0,
      stage: 'starting',
    });

    removeScanningCity('minsk');

    const cities = getScanningCities();
    expect(cities).toHaveLength(0);
  });

  it('должен проверять isCityScanning', () => {
    const { addScanningCity, isCityScanning } = useFilterStore.getState();
    
    expect(isCityScanning('minsk')).toBe(false);

    addScanningCity({
      city: 'minsk',
      city_name: 'Минск',
      trigger_type: 'manual',
      started_at: '2024-01-01T00:00:00Z',
      progress: 0,
      stage: 'starting',
    });

    expect(isCityScanning('minsk')).toBe(true);
    expect(isCityScanning('mogilev')).toBe(false);
  });

  it('должен сохранять другие поля при обновлении', () => {
    const { addScanningCity, updateScanningCity, getScanningCities } = useFilterStore.getState();
    
    addScanningCity({
      city: 'minsk',
      city_name: 'Минск',
      trigger_type: 'manual',
      started_at: '2024-01-01T00:00:00Z',
      progress: 0,
      stage: 'starting',
      elapsed_seconds: 10,
    });

    updateScanningCity('minsk', {
      progress: 50,
    });

    const cities = getScanningCities();
    expect(cities[0].progress).toBe(50);
    expect(cities[0].elapsed_seconds).toBe(10); // Сохранено
    expect(cities[0].city_name).toBe('Минск'); // Сохранено
  });

  it('должен игнорировать обновление несуществующего города', () => {
    const { updateScanningCity, getScanningCities } = useFilterStore.getState();
    
    updateScanningCity('minsk', {
      progress: 50,
    });

    const cities = getScanningCities();
    expect(cities).toHaveLength(0);
  });

  it('должен сбрасывать scanningCities при reset', () => {
    const { addScanningCity, reset, getScanningCities } = useFilterStore.getState();
    
    addScanningCity({
      city: 'minsk',
      city_name: 'Минск',
      trigger_type: 'manual',
      started_at: '2024-01-01T00:00:00Z',
      progress: 0,
      stage: 'starting',
    });

    reset();

    const cities = getScanningCities();
    expect(cities).toHaveLength(0);
  });
});
