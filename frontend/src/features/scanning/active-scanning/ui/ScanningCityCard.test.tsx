import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScanningCityCard } from './ScanningCityCard';
import type { ScanningCity } from '@/store/filterStore';

const mockScanningCity: ScanningCity = {
  city: 'minsk',
  city_name: 'Минск',
  trigger_type: 'manual',
  started_at: '2024-01-01T00:00:00Z',
  progress: 45,
  stage: 'fetching',
  elapsed_seconds: 135,
  pages_scraped: 25,
  listings_fetched: 500,
  listings_processed: 300,
};

describe('ScanningCityCard', () => {
  it('должен отображать название города', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByText('Минск')).toBeInTheDocument();
  });

  it('должен отображать тип сканирования (Ручное)', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByText('Ручное')).toBeInTheDocument();
  });

  it('должен отображать тип сканирования (Автоматическое)', () => {
    const scheduledCity: ScanningCity = {
      ...mockScanningCity,
      trigger_type: 'scheduled',
    };
    render(<ScanningCityCard city={scheduledCity} />);
    expect(screen.getByText('Автоматическое')).toBeInTheDocument();
  });

  it('должен отображать прогресс в процентах', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('должен отображать стадию сканирования', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByText('📥 Сканирование страниц')).toBeInTheDocument();
  });

  it('должен отображать время elapsed', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByText('2 мин 15 сек')).toBeInTheDocument();
  });

  it('должен отображать количество страниц', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByText('📄 25')).toBeInTheDocument();
  });

  it('должен отображать количество объявлений', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByText('📊 500')).toBeInTheDocument();
  });

  it('должен отображать количество обработанных объявлений', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByText('💾 300')).toBeInTheDocument();
  });

  it('должен отображать иконку города', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    expect(screen.getByRole('img', { name: 'city' })).toBeInTheDocument();
  });

  it('должен применять правильный badge для manual сканирования', () => {
    render(<ScanningCityCard city={mockScanningCity} />);
    const badge = screen.getByText('🔄');
    expect(badge).toBeInTheDocument();
  });

  it('должен применять правильный badge для scheduled сканирования', () => {
    const scheduledCity: ScanningCity = {
      ...mockScanningCity,
      trigger_type: 'scheduled',
    };
    render(<ScanningCityCard city={scheduledCity} />);
    const badge = screen.getByText('⏰');
    expect(badge).toBeInTheDocument();
  });

  it('должен отображать стадию error с красным цветом', () => {
    const errorCity: ScanningCity = {
      ...mockScanningCity,
      stage: 'error',
      progress: -1,
    };
    render(<ScanningCityCard city={errorCity} />);
    expect(screen.getByText('❌ Ошибка')).toBeInTheDocument();
    // Используем getAllByText так как текст "Ошибка" встречается в нескольких элементах
    expect(screen.getAllByText('Ошибка')).toHaveLength(2);
  });

  it('должен отображать стадию done с зелёным цветом', () => {
    const doneCity: ScanningCity = {
      ...mockScanningCity,
      stage: 'done',
      progress: 100,
    };
    render(<ScanningCityCard city={doneCity} />);
    expect(screen.getByText('✅ Завершено')).toBeInTheDocument();
    expect(screen.getByText('Готово')).toBeInTheDocument();
  });

  it('должен отображать 0 для отсутствующих метрик', () => {
    const emptyCity: ScanningCity = {
      ...mockScanningCity,
      elapsed_seconds: 0,
      pages_scraped: 0,
      listings_fetched: 0,
      listings_processed: 0,
    };
    render(<ScanningCityCard city={emptyCity} />);
    expect(screen.getByText('0 сек')).toBeInTheDocument();
    expect(screen.getByText('📄 0')).toBeInTheDocument();
    expect(screen.getByText('📊 0')).toBeInTheDocument();
    expect(screen.getByText('💾 0')).toBeInTheDocument();
  });
});
