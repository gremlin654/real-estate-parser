import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActiveScanningWidget } from './ActiveScanningWidget';
import type { ScanningCity } from '@/store/filterStore';

// Мок store с поддержкой селекторов
let mockScanningCities: ScanningCity[] = [];

vi.mock('@/store/filterStore', () => ({
  useFilterStore: vi.fn((selector) => {
    if (typeof selector === 'function') {
      return selector({
        getScanningCities: () => mockScanningCities,
      });
    }
    return {
      getScanningCities: () => mockScanningCities,
    };
  }),
}));

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
    mockScanningCities = [];
  });

  it('должен возвращать null если нет активных сканирований', () => {
    const { container } = render(<ActiveScanningWidget />);
    expect(container.firstChild).toBeNull();
  });

  it('должен отображать одну карточку для одного активного города', () => {
    mockScanningCities = [createMockScanningCity('minsk', 'Минск', 45)];
    render(<ActiveScanningWidget />);
    expect(screen.getByText('Минск')).toBeInTheDocument();
    expect(screen.getByText('1 город')).toBeInTheDocument();
  });

  it('должен отображать три карточки для трёх активных городов', () => {
    mockScanningCities = [
      createMockScanningCity('minsk', 'Минск', 45),
      createMockScanningCity('mogilev', 'Могилёв', 60),
      createMockScanningCity('grodno', 'Гродно', 30),
    ];
    render(<ActiveScanningWidget />);
    expect(screen.getByText('Минск')).toBeInTheDocument();
    expect(screen.getByText('Могилёв')).toBeInTheDocument();
    expect(screen.getByText('Гродно')).toBeInTheDocument();
    expect(screen.getByText('3 города')).toBeInTheDocument();
  });

  it('должен отображать "+N ещё" если активных городов больше 3', () => {
    mockScanningCities = [
      createMockScanningCity('minsk', 'Минск', 45),
      createMockScanningCity('mogilev', 'Могилёв', 60),
      createMockScanningCity('grodno', 'Гродно', 30),
      createMockScanningCity('brest', 'Брест', 20),
    ];
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
    mockScanningCities = [
      createMockScanningCity('minsk', 'Минск', 45),
      createMockScanningCity('mogilev', 'Могилёв', 60),
      createMockScanningCity('grodno', 'Гродно', 30),
      createMockScanningCity('brest', 'Брест', 20),
      createMockScanningCity('gomel', 'Гомель', 10),
      createMockScanningCity('vitebsk', 'Витебск', 5),
    ];
    render(<ActiveScanningWidget />);
    expect(screen.getByText('+3')).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes('ещё'))).toBeInTheDocument();
    expect(screen.getByText('6 городов')).toBeInTheDocument();
  });

  it('должен отображать заголовок "🔄 Активные сканирования"', () => {
    mockScanningCities = [createMockScanningCity('minsk', 'Минск', 45)];
    render(<ActiveScanningWidget />);
    expect(screen.getByText('🔄 Активные сканирования')).toBeInTheDocument();
  });

  it('должен отображать индикатор real-time обновления', () => {
    mockScanningCities = [createMockScanningCity('minsk', 'Минск', 45)];
    render(<ActiveScanningWidget />);
    expect(screen.getByText('Real-time обновление')).toBeInTheDocument();
  });

  it('должен отображать общее количество активных сканирований', () => {
    mockScanningCities = [
      createMockScanningCity('minsk', 'Минск', 45),
      createMockScanningCity('mogilev', 'Могилёв', 60),
    ];
    render(<ActiveScanningWidget />);
    expect(screen.getByText('Всего активных: 2')).toBeInTheDocument();
  });
});
