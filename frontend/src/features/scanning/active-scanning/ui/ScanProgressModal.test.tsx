import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScanProgressModal } from './ScanProgressModal';

// Mock useFilterStore с поддержкой селекторов
let mockScanningCities: any[] = [];

vi.mock('@/store/filterStore', () => ({
  useFilterStore: vi.fn((selector) => {
    // Если передан селектор - вызываем его с моковым state
    if (typeof selector === 'function') {
      return selector({
        getScanningCities: () => mockScanningCities || [],
      });
    }
    // Иначе возвращаем весь state
    return {
      getScanningCities: () => mockScanningCities || [],
    };
  }),
}));

describe('ScanProgressModal', () => {
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockScanningCities = [];
  });

  const mockCities = [
    {
      city: 'minsk',
      city_name: 'Минск',
      trigger_type: 'manual' as const,
      started_at: new Date().toISOString(),
      progress: 45,
      stage: 'fetching',
      pages_scraped: 15,
      listings_fetched: 450,
      listings_processed: 0,
      elapsed_seconds: 95,
    },
    {
      city: 'mogilev',
      city_name: 'Могилёв',
      trigger_type: 'scheduled' as const,
      started_at: new Date().toISOString(),
      progress: 80,
      stage: 'upserting',
      pages_scraped: 23,
      listings_fetched: 690,
      listings_processed: 550,
      elapsed_seconds: 142,
    },
  ];

  it('должен рендерить модальное окно когда open=true', () => {
    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText('Прогресс сканирования')).toBeInTheDocument();
  });

  it('не должен рендерить содержимое когда open=false', () => {
    render(<ScanProgressModal open={false} onOpenChange={mockOnOpenChange} />);
    expect(screen.queryByText('Прогресс сканирования')).not.toBeInTheDocument();
  });

  it('должен показывать пустое состояние когда нет активных сканирований', () => {
    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);
    expect(screen.getByText('Нет активных сканирований')).toBeInTheDocument();
  });

  it('должен показывать карточки сканирований когда они есть', () => {
    mockScanningCities = mockCities;
    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText('Минск')).toBeInTheDocument();
    expect(screen.getByText('Могилёв')).toBeInTheDocument();
    expect(screen.getByText(/Активных сканирований:/)).toBeInTheDocument();
  });

  it('должен показывать общую статистику', () => {
    mockScanningCities = mockCities;
    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText('Общая статистика')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Городов
    expect(screen.getByText('38')).toBeInTheDocument(); // Всего страниц (15+23)
    expect(screen.getByText('1140')).toBeInTheDocument(); // Всего объявлений (450+690)
  });

  it('должен закрываться при нажатии на кнопку "Закрыть"', () => {
    mockScanningCities = mockCities;
    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    const closeButton = screen.getByText('Закрыть');
    fireEvent.click(closeButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('должен показывать индикатор загрузки когда сканирование активное', () => {
    mockScanningCities = [mockCities[0]];
    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    const icon = document.querySelector('[class*="animate-spin-slow"]');
    expect(icon).toBeInTheDocument();
  });

  it('должен показывать правильное описание для 1 активного сканирования', () => {
    mockScanningCities = [mockCities[0]];
    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText(/Активных сканирований: 1/)).toBeInTheDocument();
  });

  it('должен показывать правильное описание для нескольких сканирований', () => {
    mockScanningCities = mockCities;
    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText(/Активных сканирований: 2/)).toBeInTheDocument();
  });
});
