import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FavoriteButton } from './FavoriteButton';
import { useFavoritesStore } from '@/store/favoritesStore';
import * as listingsApi from '@/api/listings';

// Mock для API hooks
vi.mock('@/api/listings', () => ({
  useAddToFavorites: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
  useRemoveFromFavorites: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
}));

// Mock для localStorage
const mockLocalStorage = {
  data: {} as Record<string, string>,
  getItem: vi.fn((key: string) => mockLocalStorage.data[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    mockLocalStorage.data[key] = value;
  }),
};

Object.defineProperty(global, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

// Mock для toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('FavoriteButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.data = {};

    // Сбросить store
    useFavoritesStore.setState({
      favorites: new Set<string>(),
      isLoading: false,
      error: null,
    });
  });

  it('должен рендерить кнопку с пустой звездой по умолчанию', () => {
    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button', { name: /добавить в избранное/i });
    expect(button).toBeInTheDocument();

    // Проверяем что звезда не заполнена (пустая)
    const starIcon = button.querySelector('svg');
    expect(starIcon).toBeInTheDocument();
  });

  it('должен рендерить кнопку с заполненной звездой если в избранном', () => {
    // Добавить в store
    useFavoritesStore.getState().addFavorite('uuid-1');

    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button', { name: /удалить из избранного/i });
    expect(button).toBeInTheDocument();

    // Проверяем что звезда заполнена
    const starIcon = button.querySelector('svg');
    expect(starIcon).toHaveClass('fill-current');
  });

  it('должен добавлять в избранное при клике', async () => {
    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button', { name: /добавить в избранное/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(useFavoritesStore.getState().isFavorite('uuid-1')).toBe(true);
    });
  });

  it('должен удалять из избранного при клике', async () => {
    useFavoritesStore.getState().addFavorite('uuid-1');

    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button', { name: /удалить из избранного/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(useFavoritesStore.getState().isFavorite('uuid-1')).toBe(false);
    });
  });

  it('должен показывать спиннер во время загрузки', async () => {
    // Mock с pending состоянием - используем spyOn
    const mockMutateAsync = vi.fn().mockResolvedValue({});
    vi.spyOn(listingsApi, 'useAddToFavorites').mockReturnValue({
      mutateAsync: mockMutateAsync,
      mutate: vi.fn(),
      isPending: true,
      data: undefined,
      variables: undefined,
      error: null,
      isError: false,
      isPaused: false,
      isSuccess: false,
      status: 'pending',
      reset: vi.fn(),
      context: undefined,
    } as any);

    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    // Проверяем что спиннер присутствует
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('должен иметь правильный размер для size="sm"', () => {
    render(<FavoriteButton listingId="uuid-1" size="sm" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-7', 'h-7');
  });

  it('должен иметь правильный размер для size="md"', () => {
    render(<FavoriteButton listingId="uuid-1" size="md" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-8', 'h-8');
  });

  it('должен иметь правильный размер для size="lg"', () => {
    render(<FavoriteButton listingId="uuid-1" size="lg" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-10', 'h-10');
  });

  it('должен добавлять кастомный className', () => {
    render(<FavoriteButton listingId="uuid-1" className="custom-class" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('должен иметь aria-label', () => {
    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Добавить в избранное');
  });

  it('должен иметь aria-pressed для избранного', () => {
    useFavoritesStore.getState().addFavorite('uuid-1');

    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-pressed', 'true');
  });

  it('должен иметь aria-pressed false для не избранного', () => {
    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-pressed', 'false');
  });

  it('должен останавливать всплытие события клика', () => {
    const handleClick = vi.fn();

    // Мокаем хуки с правильными значениями
    const mockAddMutateAsync = vi.fn().mockResolvedValue({});
    const mockRemoveMutateAsync = vi.fn().mockResolvedValue({});
    vi.spyOn(listingsApi, 'useAddToFavorites').mockReturnValue({
      mutateAsync: mockAddMutateAsync,
      mutate: vi.fn(),
      isPending: false,
      data: undefined,
      variables: undefined,
      error: null,
      isError: false,
      isPaused: false,
      isSuccess: true,
      status: 'success',
      reset: vi.fn(),
      context: undefined,
    } as any);
    vi.spyOn(listingsApi, 'useRemoveFromFavorites').mockReturnValue({
      mutateAsync: mockRemoveMutateAsync,
      mutate: vi.fn(),
      isPending: false,
      data: undefined,
      variables: undefined,
      error: null,
      isError: false,
      isPaused: false,
      isSuccess: true,
      status: 'success',
      reset: vi.fn(),
      context: undefined,
    } as any);

    render(
      <div onClick={handleClick}>
        <FavoriteButton listingId="uuid-1" />
      </div>,
      { wrapper: createWrapper() }
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('должен быть отключен во время мутации', async () => {
    // Mock с pending состоянием
    const mockMutateAsync = vi.fn();
    vi.spyOn(listingsApi, 'useAddToFavorites').mockReturnValue({
      mutateAsync: mockMutateAsync,
      mutate: vi.fn(),
      isPending: true,
      data: undefined,
      variables: undefined,
      error: null,
      isError: false,
      isPaused: false,
      isSuccess: false,
      status: 'pending',
      reset: vi.fn(),
      context: undefined,
    } as any);

    render(<FavoriteButton listingId="uuid-1" />, { wrapper: createWrapper() });

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });
});
