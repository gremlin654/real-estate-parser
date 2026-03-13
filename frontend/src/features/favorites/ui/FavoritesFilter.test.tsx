import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FavoritesFilter } from './FavoritesFilter';
import type { FavoritesFilters } from '@/shared/types';

describe('FavoritesFilter', () => {
  const mockOnChange = vi.fn();
  const mockOnReset = vi.fn();

  const defaultProps = {
    filters: {} as FavoritesFilters,
    onChange: mockOnChange,
    onReset: mockOnReset,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Город фильтр', () => {
    it('должен рендерить select для города', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const citySelect = screen.getByTestId('city-select');
      expect(citySelect).toBeInTheDocument();
    });

    it('должен вызывать onChange при выборе города', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const citySelect = screen.getByTestId('city-select');
      fireEvent.click(citySelect);

      const minskOption = screen.getByText('Минск');
      fireEvent.click(minskOption);

      expect(mockOnChange).toHaveBeenCalledWith({
        city: 'minsk',
      });
    });

    it('должен выбирать "Все города"', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const citySelect = screen.getByTestId('city-select');
      expect(citySelect).toHaveTextContent('Все города');
    });
  });

  describe('Фильтр цены', () => {
    it('должен рендерить input для минимальной цены', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const priceMinInput = screen.getByTestId('price-min-input');
      expect(priceMinInput).toBeInTheDocument();
    });

    it('должен рендерить input для максимальной цены', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const priceMaxInput = screen.getByTestId('price-max-input');
      expect(priceMaxInput).toBeInTheDocument();
    });

    it('должен вызывать onChange при применении цены', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const priceMinInput = screen.getByTestId('price-min-input');
      const priceMaxInput = screen.getByTestId('price-max-input');
      const applyButton = screen.getByTestId('price-apply-button');

      fireEvent.change(priceMinInput, { target: { value: '100000' } });
      fireEvent.change(priceMaxInput, { target: { value: '200000' } });
      fireEvent.click(applyButton);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          priceFrom: 100000,
          priceTo: 200000,
        })
      );
    });

    it('должен сбрасывать цену при нажатии на кнопку сброса', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const clearButton = screen.getByTestId('price-clear-button');
      fireEvent.click(clearButton);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          priceFrom: null,
          priceTo: null,
        })
      );
    });

    it('должен применять цену при нажатии Enter', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const priceMinInput = screen.getByTestId('price-min-input');
      
      fireEvent.change(priceMinInput, { target: { value: '150000' } });
      fireEvent.keyDown(priceMinInput, { key: 'Enter' });

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          priceFrom: 150000,
        })
      );
    });
  });

  describe('Фильтр комнат', () => {
    it('должен рендерить кнопки для комнат', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const room1Button = screen.getByTestId('room-1-button');
      expect(room1Button).toBeInTheDocument();

      const room2Button = screen.getByTestId('room-2-button');
      expect(room2Button).toBeInTheDocument();

      const room5PlusButton = screen.getByTestId('room-5-plus-button');
      expect(room5PlusButton).toBeInTheDocument();
    });

    it('должен вызывать onChange при выборе комнаты', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const room2Button = screen.getByTestId('room-2-button');
      fireEvent.click(room2Button);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          rooms: expect.arrayContaining([2]),
        })
      );
    });

    it('должен выбирать 5+ комнат', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const room5PlusButton = screen.getByTestId('room-5-plus-button');
      fireEvent.click(room5PlusButton);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          roomsOther: true,
        })
      );
    });

    it('должен переключать состояние комнаты при повторном нажатии', () => {
      const filters: FavoritesFilters = {
        rooms: [3],
      };

      render(<FavoritesFilter filters={filters} onChange={mockOnChange} onReset={mockOnReset} />);

      const room3Button = screen.getByTestId('room-3-button');
      
      // Клик - снять выбор (так как комната уже выбрана)
      fireEvent.click(room3Button);
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          rooms: undefined,
        })
      );
    });

    it('должен показывать Badge с количеством выбранных комнат', () => {
      const filters: FavoritesFilters = {
        rooms: [1, 2],
      };

      render(<FavoritesFilter filters={filters} onChange={mockOnChange} onReset={mockOnReset} />);

      const badge = screen.getByText(/Выбрано:/);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('Выбрано: 2');
    });
  });

  describe('Сортировка', () => {
    it('должен рендерить select для сортировки', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const sortSelect = screen.getByTestId('sort-select');
      expect(sortSelect).toBeInTheDocument();
    });

    it('должен вызывать onChange при выборе сортировки', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const sortSelect = screen.getByTestId('sort-select');
      fireEvent.click(sortSelect);

      const priceAscOption = screen.getByText(/Цена \(возрастание\)/);
      fireEvent.click(priceAscOption);

      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          sort: 'price_asc',
        })
      );
    });

    it('должен иметь сортировку по умолчанию created_at_desc', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const sortSelect = screen.getByTestId('sort-select');
      expect(sortSelect).toHaveTextContent(/Дата добавления \(новые\)/);
    });
  });

  describe('Кнопка сброса всех фильтров', () => {
    it('должен рендерить кнопку сброса', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const resetButton = screen.getByTestId('reset-filters-button');
      expect(resetButton).toBeInTheDocument();
    });

    it('должен вызывать onReset при клике', () => {
      const filters: FavoritesFilters = {
        city: 'minsk',
      };

      render(<FavoritesFilter filters={filters} onChange={mockOnChange} onReset={mockOnReset} />);

      const resetButton = screen.getByTestId('reset-filters-button');
      fireEvent.click(resetButton);

      expect(mockOnReset).toHaveBeenCalled();
    });

    it('должен быть disabled когда нет активных фильтров', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const resetButton = screen.getByTestId('reset-filters-button');
      expect(resetButton).toBeDisabled();
    });

    it('должен быть enabled когда есть активные фильтры', () => {
      const filters: FavoritesFilters = {
        city: 'minsk',
      };

      render(<FavoritesFilter filters={filters} onChange={mockOnChange} onReset={mockOnReset} />);

      const resetButton = screen.getByTestId('reset-filters-button');
      expect(resetButton).not.toBeDisabled();
    });
  });

  describe('Синхронизация с props', () => {
    it('должен синхронизировать цену с props', () => {
      const filters: FavoritesFilters = {
        priceFrom: 100000,
        priceTo: 200000,
      };

      render(<FavoritesFilter filters={filters} onChange={mockOnChange} onReset={mockOnReset} />);

      const priceMinInput = screen.getByTestId('price-min-input');
      const priceMaxInput = screen.getByTestId('price-max-input');

      // Input возвращает число, а не строку
      expect(priceMinInput).toHaveValue(100000);
      expect(priceMaxInput).toHaveValue(200000);
    });

    it('должен синхронизировать город с props', () => {
      const filters: FavoritesFilters = {
        city: 'minsk',
      };

      render(<FavoritesFilter filters={filters} onChange={mockOnChange} onReset={mockOnReset} />);

      const citySelect = screen.getByTestId('city-select');
      expect(citySelect).toHaveTextContent('Минск');
    });

    it('должен синхронизировать выбранные комнаты с props', () => {
      const filters: FavoritesFilters = {
        rooms: [1, 3],
      };

      render(<FavoritesFilter filters={filters} onChange={mockOnChange} onReset={mockOnReset} />);

      const room1Button = screen.getByTestId('room-1-button');
      const room2Button = screen.getByTestId('room-2-button');
      const room3Button = screen.getByTestId('room-3-button');

      expect(room1Button).toHaveAttribute('aria-pressed', 'true');
      expect(room2Button).toHaveAttribute('aria-pressed', 'false');
      expect(room3Button).toHaveAttribute('aria-pressed', 'true');
    });
  });

  describe('Иконки и визуальные элементы', () => {
    it('должен рендерить иконку MapPin для города', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const mapPinIcon = document.querySelector('svg.lucide-map-pin');
      expect(mapPinIcon).toBeInTheDocument();
    });

    it('должен рендерить иконку DollarSign для цены', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const dollarIcon = document.querySelector('svg.lucide-dollar-sign');
      expect(dollarIcon).toBeInTheDocument();
    });

    it('должен рендерить иконку ArrowUpDown для сортировки', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const arrowIcon = document.querySelector('svg.lucide-arrow-up-down');
      expect(arrowIcon).toBeInTheDocument();
    });

    it('должен рендерить иконку RotateCcw на кнопке сброса', () => {
      render(<FavoritesFilter {...defaultProps} />);

      const rotateIcons = document.querySelectorAll('svg.lucide-rotate-ccw');
      expect(rotateIcons.length).toBeGreaterThan(0);
    });
  });
});
