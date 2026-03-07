import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActiveScanningWidget } from './ActiveScanningWidget';
import { useFilterStore } from '@/store/filterStore';
import type { ScanningCity } from '@/store/filterStore';

// Мок store
vi.mock('@/store/filterStore', () => ({
  useFilterStore: vi.fn(),
}));

const mockUseFilterStore = vi.mocked(useFilterStore);

const createMockScanningCity = (city: string, city_name: string, progress: number): ScanningCity => ({
  city,
  city_name,
  trigger_type: 'manual',
  started_at: '2024-01-01T00:00:00Z',
  progress,
  stage: 'fetching',
  elapsed_seconds: 60,
  pages_scraped: 10,
  listings_fetched: 100,
  listings_processed: 50,
});

describe('ActiveScanningWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('должен возвращать null если нет активных сканирований', () => {
    mockUseFilterStore.mockReturnValue({
      getScanningCities: () => [],
    } as any);

    const { container } = render(<ActiveScanningWidget />);
    expect(container.firstChild).toBeNull();
  });

  it('должен отображать одну карточку для одного активного города', () => {
    const cities = [createMockScanningCity('minsk', 'Минск', 45)];
    mockUseFilterStore.mockReturnValue({
      getScanningCities: () => cities,
    } as any);

    render(<ActiveScanningWidget />);
    expect(screen.getByText('Минск')).toBeInTheDocument();
    expect(screen.getByText('1 город')).toBeInTheDocument();
  });

  it('должен отображать три карточки для трёх активных городов', () => {
    const cities = [
      createMockScanningCity('minsk', 'Минск', 45),
      createMockScanningCity('mogilev', 'Могилёв', 60),
      createMockScanningCity('grodno', 'Гродно', 30),
    ];
    mockUseFilterStore.mockReturnValue({
      getScanningCities: () => cities,
    } as any);

    render(<ActiveScanningWidget />);
    expect(screen.getByText('Минск')).toBeInTheDocument();
    expect(screen.getByText('Могилёв')).toBeInTheDocument();
    expect(screen.getByText('Гродно')).toBeInTheDocument();
    expect(screen.getByText('3 города')).toBeInTheDocument();
  });

  it('должен отображать "+N ещё" если активных городов больше 3', () => {
    const cities = [
      createMockScanningCity('minsk', 'Минск', 45),
      createMockScanningCity('mogilev', 'Могилёв', 60),
      createMockScanningCity('grodno', 'Гродно', 30),
      createMockScanningCity('brest', 'Брест', 20),
    ];
    mockUseFilterStore.mockReturnValue({
      getScanningCities: () => cities,
    } as any);

    render(<ActiveScanningWidget />);
    // Первые 3 города видны
    expect(screen.getByText('Минск')).toBeInTheDocument();
    expect(screen.getByText('Могилёв')).toBeInTheDocument();
    expect(screen.getByText('Гродно')).toBeInTheDocument();
    // Четвёртый скрыт, показываем "+1 ещё"
    expect(screen.getByText('+1')).toBeInTheDocument();
    expect(screen.getByText('ещё город')).toBeInTheDocument();
    expect(screen.getByText('4 города')).toBeInTheDocument();
  });

  it('должен отображать "+N ещё городов" для множественного числа', () => {
    const cities = [
      createMockScanningCity('minsk', 'Минск', 45),
      createMockScanningCity('mogilev', 'Могилёв', 60),
      createMockScanningCity('grodno', 'Гродно', 30),
      createMockScanningCity('brest', 'Брест', 20),
      createMockScanningCity('gomel', 'Гомель', 10),
      createMockScanningCity('vitebsk', 'Витебск', 5),
    ];
    mockUseFilterStore.mockReturnValue({
      getScanningCities: () => cities,
    } as any);

    render(<ActiveScanningWidget />);
    expect(screen.getByText('+3')).toBeInTheDocument();
    // Проверяем что есть текст "ещё город" (остальная часть может быть разбита)
    expect(screen.getByText((content) => content.includes('ещё'))).toBeInTheDocument();
    expect(screen.getByText('6 городов')).toBeInTheDocument();
  });

  it('должен отображать заголовок "🔄 Активные сканирования"', () => {
    const cities = [createMockScanningCity('minsk', 'Минск', 45)];
    mockUseFilterStore.mockReturnValue({
      getScanningCities: () => cities,
    } as any);

    render(<ActiveScanningWidget />);
    expect(screen.getByText('🔄 Активные сканирования')).toBeInTheDocument();
  });

  it('должен отображать индикатор real-time обновления', () => {
    const cities = [createMockScanningCity('minsk', 'Минск', 45)];
    mockUseFilterStore.mockReturnValue({
      getScanningCities: () => cities,
    } as any);

    render(<ActiveScanningWidget />);
    expect(screen.getByText('Real-time обновление')).toBeInTheDocument();
  });

  it('должен отображать общее количество активных сканирований', () => {
    const cities = [
      createMockScanningCity('minsk', 'Минск', 45),
      createMockScanningCity('mogilev', 'Могилёв', 60),
    ];
    mockUseFilterStore.mockReturnValue({
      getScanningCities: () => cities,
    } as any);

    render(<ActiveScanningWidget />);
    expect(screen.getByText('Всего активных: 2')).toBeInTheDocument();
  });
});
