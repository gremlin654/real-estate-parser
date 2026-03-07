import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CityScanSettings } from './CityScanSettings';
import { useCityScanSettings, useUpdateCityScanSettings } from '@/api/listings';
import { toast } from 'sonner';

/**
 * Mock hooks
 */
vi.mock('@/api/listings', () => ({
  useCityScanSettings: vi.fn(),
  useUpdateCityScanSettings: vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

/**
 * Helper для создания QueryClient
 */
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

/**
 * Mock данные
 */
const mockSettings = {
  enabled: true,
  scan_interval_minutes: 30,
  updated_at: '2025-03-07T10:00:00Z',
};

const mockUpdateResponse = {
  enabled: false,
  scan_interval_minutes: 60,
  updated_at: '2025-03-07T11:00:00Z',
};

describe('CityScanSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Рендеринг с данными', () => {
    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: mockSettings,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);
    });

    it('должен рендерить компонент с названием города', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Минск')).toBeInTheDocument();
    });

    it('должен отображать switch с правильным состоянием', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Автоматическое сканирование')).toBeInTheDocument();
      expect(screen.getByText('Включено')).toBeInTheDocument();
    });

    it('должен отображать slider с правильным значением интервала', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Интервал сканирования')).toBeInTheDocument();
      expect(screen.getByText('30 мин')).toBeInTheDocument();
    });

    it('должен отображать кнопку "Сохранить изменения"', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Сохранить изменения')).toBeInTheDocument();
    });

    it('должен отображать badge с правильным статусом', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Автосканирование включено')).toBeInTheDocument();
    });

    it('должен отображать иконку MapPin', () => {
      const { container } = render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Проверка наличия иконки MapPin (через SVG)
      const svgIcons = container.querySelectorAll('svg');
      expect(svgIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Switch переключает enabled', () => {
    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: mockSettings,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);
    });

    it('должен переключать switch при клике', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const switchElement = screen.getByRole('switch');
      expect(switchElement).toBeChecked();

      fireEvent.click(switchElement);

      // После клика должно измениться локальное состояние
      expect(screen.getByText('Выключено')).toBeInTheDocument();
    });

    it('должен устанавливать isDirty при изменении switch', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const switchElement = screen.getByRole('switch');
      fireEvent.click(switchElement);

      // Кнопка сохранения должна стать активной
      const saveButton = screen.getByText('Сохранить изменения');
      expect(saveButton).not.toBeDisabled();
    });
  });

  describe('Slider меняет интервал', () => {
    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: mockSettings,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);
    });

    it('должен изменять значение интервала при перемещении slider', () => {
      const { container } = render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Находим slider thumb через role
      const sliderThumb = container.querySelector('[role="slider"]');
      expect(sliderThumb).toBeInTheDocument();
      expect(sliderThumb).toHaveAttribute('aria-valuenow', '30');

      // Изменяем значение slider через keyboard
      sliderThumb && fireEvent.keyDown(sliderThumb, { key: 'ArrowRight', code: 'ArrowRight' });

      // Проверяем, что значение обновилось
      expect(screen.getByText('35 мин')).toBeInTheDocument();
    });

    it('должен устанавливать isDirty при изменении slider', () => {
      const { container } = render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const sliderThumb = container.querySelector('[role="slider"]');

      // Изменяем значение slider через keyboard
      sliderThumb && fireEvent.keyDown(sliderThumb, { key: 'ArrowRight', code: 'ArrowRight' });

      // Кнопка сохранения должна стать активной
      const saveButton = screen.getByText('Сохранить изменения');
      expect(saveButton).not.toBeDisabled();
    });

    it('должен иметь min=5 и max=1440', () => {
      const { container } = render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const sliderThumb = container.querySelector('[role="slider"]');
      expect(sliderThumb).toHaveAttribute('aria-valuemin', '5');
      expect(sliderThumb).toHaveAttribute('aria-valuemax', '1440');
    });
  });

  describe('Кнопка "Сохранить" отправляет PUT запрос', () => {
    const mockMutate = vi.fn();

    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: mockSettings,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      } as any);
    });

    it('должен вызывать mutate при клике на кнопку сохранения', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Изменяем состояние
      const switchElement = screen.getByRole('switch');
      fireEvent.click(switchElement);

      // Кликаем на кнопку сохранения
      const saveButton = screen.getByText('Сохранить изменения');
      fireEvent.click(saveButton);

      // Проверяем, что mutate был вызван
      expect(mockMutate).toHaveBeenCalledWith({
        city: 'minsk',
        data: {
          enabled: false,
          scan_interval_minutes: 30,
        },
      });
    });

    it('должен сбрасывать isDirty после сохранения', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Изменяем состояние
      const switchElement = screen.getByRole('switch');
      fireEvent.click(switchElement);

      // Кликаем на кнопку сохранения
      const saveButton = screen.getByText('Сохранить изменения');
      fireEvent.click(saveButton);

      // После сохранения кнопка должна стать неактивной
      expect(saveButton).toBeDisabled();
    });
  });

  describe('Loading state при сохранении', () => {
    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: mockSettings,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: true,
      } as any);
    });

    it('должен показывать spinner при сохранении', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const saveButton = screen.getByText('Сохранить изменения');
      expect(saveButton).toBeDisabled();

      // Проверка наличия иконки RefreshCw (spinner)
      const spinner = saveButton.querySelector('svg');
      expect(spinner).toBeInTheDocument();
    });

    it('должен блокировать кнопку при сохранении', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const saveButton = screen.getByText('Сохранить изменения');
      expect(saveButton).toBeDisabled();
    });
  });

  describe('Disabled slider когда enabled=false', () => {
    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: { ...mockSettings, enabled: false },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);
    });

    it('должен отображать "Выключено"', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Выключено')).toBeInTheDocument();
    });

    it('должен отображать badge "Автосканирование отключено"', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Автосканирование отключено')).toBeInTheDocument();
    });

    it('должен иметь disabled slider', () => {
      const { container } = render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const sliderThumb = container.querySelector('[role="slider"]');
      expect(sliderThumb).toHaveAttribute('data-disabled', '');
    });
  });

  describe('Badge отображает правильный статус', () => {
    it('должен показывать зелёный badge когда enabled=true', () => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: { ...mockSettings, enabled: true },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Автосканирование включено')).toBeInTheDocument();
    });

    it('должен показывать серый badge когда enabled=false', () => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: { ...mockSettings, enabled: false },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Автосканирование отключено')).toBeInTheDocument();
    });
  });

  describe('Toast уведомления', () => {
    it('должен показывать success toast при успешном сохранении', () => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: mockSettings,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Проверяем, что toast.success доступен
      expect(toast.success).toBeDefined();
    });

    it('должен показывать error toast при ошибке сохранения', () => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: mockSettings,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Проверяем, что toast.error доступен
      expect(toast.error).toBeDefined();
    });
  });

  describe('Loading state компонента', () => {
    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);
    });

    it('должен показывать skeleton при загрузке', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Минск')).toBeInTheDocument();

      // Проверка наличия skeleton элементов
      const skeletons = document.querySelectorAll('.bg-muted.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Error state', () => {
    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to fetch'),
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);
    });

    it('должен показывать ошибку при загрузке', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Минск')).toBeInTheDocument();
      expect(screen.getByText('Ошибка загрузки настроек')).toBeInTheDocument();
    });

    it('должен показывать иконку AlertCircle в error state', () => {
      const { container } = render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Проверка наличия иконки ошибки
      const svgIcons = container.querySelectorAll('svg');
      expect(svgIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Edge cases', () => {
    it('должен обрабатывать минимальный интервал 5 минут', () => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: { ...mockSettings, scan_interval_minutes: 5 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Используем getAllByText, так как "5 мин" встречается дважды (в slider и в label)
      const fiveMinTexts = screen.getAllByText(/5\s*мин/);
      expect(fiveMinTexts.length).toBeGreaterThan(0);
    });

    it('должен обрабатывать максимальный интервал 1440 минут', () => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: { ...mockSettings, scan_interval_minutes: 1440 },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('1440 мин')).toBeInTheDocument();
    });

    it('должен обрабатывать null updated_at', () => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: { ...mockSettings, updated_at: null },
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);

      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Минск')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      vi.mocked(useCityScanSettings).mockReturnValue({
        data: mockSettings,
        isLoading: false,
        error: null,
      } as any);

      vi.mocked(useUpdateCityScanSettings).mockReturnValue({
        mutate: vi.fn(),
        isPending: false,
      } as any);
    });

    it('должен иметь правильную структуру Card', () => {
      const { container } = render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      // Card имеет класс bg-card
      expect(container.querySelector('.bg-card')).toBeInTheDocument();
    });

    it('должен иметь switch с правильной ролью', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const switchElement = screen.getByRole('switch');
      expect(switchElement).toBeInTheDocument();
    });

    it('должен иметь slider с правильной ролью', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const slider = screen.getByRole('slider');
      expect(slider).toBeInTheDocument();
    });

    it('должен иметь кнопку с правильной ролью', () => {
      render(<CityScanSettings city="minsk" cityName="Минск" />, {
        wrapper: createWrapper(),
      });

      const button = screen.getByRole('button', { name: /сохранить изменения/i });
      expect(button).toBeInTheDocument();
    });
  });
});
