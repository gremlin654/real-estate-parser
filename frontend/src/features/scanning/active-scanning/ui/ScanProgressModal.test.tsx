import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ScanProgressModal } from './ScanProgressModal';
import { useFilterStore } from '@/store/filterStore';

// Mock store
vi.mock('@/store/filterStore', () => ({
  useFilterStore: vi.fn(),
}));

describe('ScanProgressModal', () => {
  const mockOnOpenChange = vi.fn();

  const mockScanningCities = [
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

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('должен рендерить модальное окно когда open=true', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => [],
    } as any);

    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText('Прогресс сканирования')).toBeInTheDocument();
  });

  it('не должен рендерить содержимое когда open=false', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => [],
    } as any);

    render(<ScanProgressModal open={false} onOpenChange={mockOnOpenChange} />);

    expect(screen.queryByText('Прогресс сканирования')).not.toBeInTheDocument();
  });

  it('должен показывать пустое состояние когда нет активных сканирований', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => [],
    } as any);

    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText('Нет активных сканирований')).toBeInTheDocument();
    expect(
      screen.getByText(/Запустите ручное сканирование города/)
    ).toBeInTheDocument();
  });

  it('должен показывать карточки сканирований когда они есть', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => mockScanningCities,
    } as any);

    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText('Минск')).toBeInTheDocument();
    expect(screen.getByText('Могилёв')).toBeInTheDocument();
    expect(screen.getByText(/Активных сканирований:/)).toBeInTheDocument();
  });

  it('должен показывать общую статистику', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => mockScanningCities,
    } as any);

    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText('Общая статистика')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // Городов
    expect(screen.getByText('38')).toBeInTheDocument(); // Всего страниц (15+23)
    expect(screen.getByText('1140')).toBeInTheDocument(); // Всего объявлений (450+690)
  });

  it('должен закрываться при нажатии на кнопку "Закрыть"', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => [],
    } as any);

    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    const closeButton = screen.getByText('Закрыть');
    fireEvent.click(closeButton);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('должен показывать индикатор загрузки когда сканирование активное', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => mockScanningCities,
    } as any);

    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    // Ищем иконку RefreshCw по role или классу
    const icon = document.querySelector('[class*="animate-spin-slow"]');
    expect(icon).toBeInTheDocument();
  });

  it('должен показывать правильное описание для 1 активного сканирования', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => [mockScanningCities[0]],
    } as any);

    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText('Активных сканирований: 1. Данные обновляются в реальном времени.')).toBeInTheDocument();
  });

  it('должен показывать правильное описание для нескольких сканирований', () => {
    vi.mocked(useFilterStore).mockReturnValue({
      getScanningCities: () => mockScanningCities,
    } as any);

    render(<ScanProgressModal open={true} onOpenChange={mockOnOpenChange} />);

    expect(screen.getByText('Активных сканирований: 2. Данные обновляются в реальном времени.')).toBeInTheDocument();
  });
});
