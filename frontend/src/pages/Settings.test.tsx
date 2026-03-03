import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { Settings } from './Settings';
import * as listingsApi from '@/api/listings';

vi.mock('@/api/listings', () => ({
  useScanSchedule: vi.fn(),
  useUpdateScanSchedule: vi.fn(),
  useScanCity: vi.fn(),
  useUpdateScanCity: vi.fn(),
  useScanCities: vi.fn(),
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

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockSchedule = {
    scan_interval_minutes: 30,
    enabled: true,
  };

  const mockCity = {
    city: 'mogilev',
    city_name: 'Могилёв',
  };

  const mockCities = [
    { code: 'minsk', name: 'Минск' },
    { code: 'mogilev', name: 'Могилёв' },
    { code: 'grodno', name: 'Гродно' },
    { code: 'brest', name: 'Брест' },
  ];

  it('renders loading state', () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: undefined, 
      isLoading: true,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: undefined });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: undefined });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<Settings />, { wrapper: createWrapper() });

    expect(screen.getByText(/Загрузка настроек/i)).toBeInTheDocument();
  });

  it('renders error state', () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: undefined, 
      isLoading: false,
      error: new Error('Failed to load') 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: undefined });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: undefined });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<Settings />, { wrapper: createWrapper() });

    expect(screen.getByText(/Ошибка загрузки настроек/i)).toBeInTheDocument();
  });

  it('renders settings form with data', async () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: mockSchedule, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Настройки автоматического сканирования/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/Город сканирования/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Автоматическое сканирование/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Интервал сканирования/i)).toBeInTheDocument();
  });

  it('displays current settings', async () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: mockSchedule, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Текущий интервал: 30 мин/i)).toBeInTheDocument();
    });

    expect(screen.getAllByText(/Включено/i)[0]).toBeInTheDocument();
  });

  it('allows changing interval', async () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: mockSchedule, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText(/Интервал сканирования/i)).toBeInTheDocument();
    });

    const intervalInput = screen.getByLabelText(/Интервал сканирования/i);
    fireEvent.change(intervalInput, { target: { value: '60' } });

    expect(intervalInput).toHaveValue(60);
  });

  it('allows toggling enabled switch', async () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: mockSchedule, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText(/Автоматическое сканирование/i)).toBeInTheDocument();
    });

    const enabledSwitch = screen.getByLabelText(/Автоматическое сканирование/i);
    fireEvent.click(enabledSwitch);
  });

  it('allows changing city', async () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: mockSchedule, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    const mockUpdateCity = vi.fn();
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: mockUpdateCity, 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText(/Город сканирования/i)).toBeInTheDocument();
    });

    const citySelect = screen.getByLabelText(/Город сканирования/i);
    fireEvent.click(citySelect);
    
    const minskOption = screen.getByText('Минск');
    fireEvent.click(minskOption);

    await waitFor(() => {
      expect(mockUpdateCity).toHaveBeenCalledWith({ city: 'minsk' });
    });
  });

  it('shows success message after saving', async () => {
    const mockMutateAsync = vi.fn().mockResolvedValue(undefined);
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: mockSchedule, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ 
      mutateAsync: mockMutateAsync, 
      isPending: false 
    });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Сохранить')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Сохранить');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        scan_interval_minutes: 30,
        enabled: true,
      });
    });
  });

  it('shows error message on invalid interval', async () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: mockSchedule, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText(/Интервал сканирования/i)).toBeInTheDocument();
    });

    const intervalInput = screen.getByLabelText(/Интервал сканирования/i);
    fireEvent.change(intervalInput, { target: { value: '2' } });

    const saveButton = screen.getByText('Сохранить');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Интервал должен быть от 5 до 1440 минут/i)).toBeInTheDocument();
    });
  });

  it('shows error message on save failure', async () => {
    const mockMutateAsync = vi.fn().mockRejectedValue(new Error('Save failed'));
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: mockSchedule, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ 
      mutateAsync: mockMutateAsync, 
      isPending: false 
    });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Сохранить')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Сохранить');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Save failed')).toBeInTheDocument();
    });
  });

  it('disables interval input when enabled is false', async () => {
    vi.mocked(listingsApi.useScanSchedule).mockReturnValue({ 
      data: { ...mockSchedule, enabled: false }, 
      isLoading: false,
      error: null 
    });
    vi.mocked(listingsApi.useScanCity).mockReturnValue({ data: mockCity });
    vi.mocked(listingsApi.useScanCities).mockReturnValue({ data: mockCities });
    vi.mocked(listingsApi.useUpdateScanSchedule).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });
    vi.mocked(listingsApi.useUpdateScanCity).mockReturnValue({ 
      mutateAsync: vi.fn(), 
      isPending: false 
    });

    render(<Settings />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByLabelText(/Интервал сканирования/i)).toBeInTheDocument();
    });

    const intervalInput = screen.getByLabelText(/Интервал сканирования/i);
    expect(intervalInput).toBeDisabled();
  });
});
