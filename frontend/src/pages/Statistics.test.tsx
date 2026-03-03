import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import Statistics from './Statistics';
import * as listingsApi from '@/api/listings';

vi.mock('@/api/listings', () => ({
  usePriceTrends: vi.fn(),
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
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
};

describe('Statistics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockTrendData = {
    data: [
      { year: 2024, month: 1, avg_price_usd: 85000, avg_price_byn: 280000 },
      { year: 2024, month: 2, avg_price_usd: 86000, avg_price_byn: 282000 },
    ],
  };

  it('renders Statistics page header', () => {
    vi.mocked(listingsApi.usePriceTrends).mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<Statistics />, { wrapper: createWrapper() });

    expect(screen.getByText('Статистика цен')).toBeInTheDocument();
  });

  it('renders city selector', () => {
    vi.mocked(listingsApi.usePriceTrends).mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<Statistics />, { wrapper: createWrapper() });

    expect(screen.getByText('Минск')).toBeInTheDocument();
  });

  it('renders period selector', () => {
    vi.mocked(listingsApi.usePriceTrends).mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<Statistics />, { wrapper: createWrapper() });

    expect(screen.getByText('12 месяцев')).toBeInTheDocument();
  });

  it('renders tabs for room types', () => {
    vi.mocked(listingsApi.usePriceTrends).mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<Statistics />, { wrapper: createWrapper() });

    expect(screen.getByText('1-комнатные')).toBeInTheDocument();
    expect(screen.getByText('2-комнатные')).toBeInTheDocument();
    expect(screen.getByText('3-комнатные')).toBeInTheDocument();
    expect(screen.getByText('4-комнатные')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(listingsApi.usePriceTrends).mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<Statistics />, { wrapper: createWrapper() });

    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  it('displays chart data when loaded', async () => {
    vi.mocked(listingsApi.usePriceTrends).mockReturnValue({
      data: mockTrendData,
      isLoading: false,
    });

    render(<Statistics />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/2 месяцев данных/i)).toBeInTheDocument();
    });
  });

  it('allows switching tabs', () => {
    vi.mocked(listingsApi.usePriceTrends).mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    render(<Statistics />, { wrapper: createWrapper() });

    fireEvent.click(screen.getByText('2-комнатные'));
    expect(screen.getByText('2-комнатные')).toBeInTheDocument();
  });

  it('renders PriceTrendChart component', () => {
    vi.mocked(listingsApi.usePriceTrends).mockReturnValue({
      data: mockTrendData,
      isLoading: false,
    });

    render(<Statistics />, { wrapper: createWrapper() });

    expect(screen.getByText('1-комнатные квартиры')).toBeInTheDocument();
  });
});
