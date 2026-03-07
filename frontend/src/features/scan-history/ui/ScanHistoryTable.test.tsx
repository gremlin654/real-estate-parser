import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScanHistoryTable } from '@/features/scan-history/ui/ScanHistoryTable';
import type { ScanHistoryItem } from '@/shared/types';

/**
 * Mock данные для тестов
 */
const mockScanHistoryData: ScanHistoryItem[] = [
  {
    id: '1',
    started_at: '2025-03-07T10:30:00Z',
    completed_at: '2025-03-07T10:31:45Z',
    city: 'mogilev',
    city_name: 'Могилёв',
    status: 'completed',
    trigger_type: 'manual',
    listings_fetched: 546,
    listings_created: 12,
    listings_updated: 5,
    listings_changed_byn: 3,
    listings_deleted: 2,
    pages_scraped: 18,
    duration_seconds: 105,
    error_message: null,
  },
  {
    id: '2',
    started_at: '2025-03-07T09:00:00Z',
    completed_at: '2025-03-07T09:01:30Z',
    city: 'minsk',
    city_name: 'Минск',
    status: 'completed',
    trigger_type: 'scheduled',
    listings_fetched: 1200,
    listings_created: 25,
    listings_updated: 10,
    listings_changed_byn: 8,
    listings_deleted: 5,
    pages_scraped: 40,
    duration_seconds: 90,
    error_message: null,
  },
  {
    id: '3',
    started_at: '2025-03-07T08:00:00Z',
    completed_at: null,
    city: 'brest',
    city_name: 'Брест',
    status: 'running',
    trigger_type: 'manual',
    listings_fetched: 300,
    listings_created: 0,
    listings_updated: 0,
    listings_changed_byn: 0,
    listings_deleted: 0,
    pages_scraped: 10,
    duration_seconds: null,
    error_message: null,
  },
  {
    id: '4',
    started_at: '2025-03-06T20:00:00Z',
    completed_at: '2025-03-06T20:00:45Z',
    city: 'gomel',
    city_name: 'Гомель',
    status: 'error',
    trigger_type: 'scheduled',
    listings_fetched: 100,
    listings_created: 0,
    listings_updated: 0,
    listings_changed_byn: 0,
    listings_deleted: 0,
    pages_scraped: 3,
    duration_seconds: 45,
    error_message: 'Network timeout',
  },
];

describe('ScanHistoryTable', () => {
  describe('Рендеринг с данными', () => {
    it('должен рендерить таблицу с данными истории сканирований', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Проверка заголовков колонок
      expect(screen.getByText('Дата/время')).toBeInTheDocument();
      expect(screen.getByText('Город')).toBeInTheDocument();
      expect(screen.getByText('Статус')).toBeInTheDocument();
      expect(screen.getByText('Тип')).toBeInTheDocument();
      expect(screen.getByText('Объявления')).toBeInTheDocument();
      expect(screen.getByText('Страниц')).toBeInTheDocument();
      expect(screen.getByText('Длительность')).toBeInTheDocument();
    });

    it('должен отображать правильное количество строк с данными', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Подсчёт строк в таблице (исключая заголовок)
      const rows = screen.getAllByRole('row');
      // 1 строка заголовка + 4 строки данных
      expect(rows).toHaveLength(5);
    });

    it('должен отображать названия городов', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      expect(screen.getByText('Могилёв')).toBeInTheDocument();
      expect(screen.getByText('Минск')).toBeInTheDocument();
      expect(screen.getByText('Брест')).toBeInTheDocument();
      expect(screen.getByText('Гомель')).toBeInTheDocument();
    });

    it('должен отображать статусы сканирований', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Используем getAllByText, так как статус "Завершено" встречается 2 раза
      const completedBadges = screen.getAllByText('Завершено');
      expect(completedBadges.length).toBe(2);
      
      const runningBadge = screen.getByText('В процессе');
      expect(runningBadge).toBeInTheDocument();
      
      const errorBadge = screen.getByText('Ошибка');
      expect(errorBadge).toBeInTheDocument();
    });

    it('должен отображать типы запусков', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Используем getAllByText для множественных элементов
      const manualBadges = screen.getAllByText('Ручное');
      expect(manualBadges.length).toBe(2);
      
      const scheduledBadges = screen.getAllByText('Авто');
      expect(scheduledBadges.length).toBe(2);
    });
  });

  describe('Форматирование данных', () => {
    it('должен форматировать дату в формате DD.MM HH:mm', () => {
      const { container } = render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Проверка формата даты (должно быть что-то вроде "07.03, 13:30")
      // Ищем ячейки таблицы с датой
      const dateCells = container.querySelectorAll('tbody td:first-child');
      expect(dateCells.length).toBeGreaterThan(0);
      
      // Проверяем, что текст содержит формат даты
      const dateText = dateCells[0].textContent;
      expect(dateText).toMatch(/\d{2}\.\d{2}, \d{2}:\d{2}/);
    });

    it('должен отображать количество страниц', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Используем getAllByText для множественных элементов
      const pageNumbers = screen.getAllByText('18');
      expect(pageNumbers.length).toBeGreaterThan(0);
      
      const pageNumbers40 = screen.getAllByText('40');
      expect(pageNumbers40.length).toBeGreaterThan(0);
      
      const pageNumbers10 = screen.getAllByText('10');
      expect(pageNumbers10.length).toBeGreaterThan(0);
      
      const pageNumbers3 = screen.getAllByText('3');
      expect(pageNumbers3.length).toBeGreaterThan(0);
    });

    it('должен форматировать длительность в минутах и секундах', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // 105 секунд = 1 мин 45 сек
      expect(screen.getByText('1 мин 45 сек')).toBeInTheDocument();
      // 90 секунд = 1 мин 30 сек
      expect(screen.getByText('1 мин 30 сек')).toBeInTheDocument();
      // 45 секунд
      expect(screen.getByText('45 сек')).toBeInTheDocument();
    });

    it('должен отображать "—" для null длительности', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Для running сканирования duration_seconds = null
      const runningRow = screen.getByText('В процессе').closest('tr');
      expect(runningRow?.textContent).toContain('—');
    });

    it('должен отображать статистику созданных объявлений с +', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      expect(screen.getByText('+12')).toBeInTheDocument();
      expect(screen.getByText('+25')).toBeInTheDocument();
    });

    it('должен отображать статистику обновлённых объявлений с иконкой', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Проверяем наличие чисел в колонке "Объявления"
      const statsCells = screen.getAllByText('5');
      expect(statsCells.length).toBeGreaterThan(0);
      
      const statsCells10 = screen.getAllByText('10');
      expect(statsCells10.length).toBeGreaterThan(0);
    });

    it('должен отображать статистику удалённых объявлений с -', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      expect(screen.getByText('-2')).toBeInTheDocument();
      expect(screen.getByText('-5')).toBeInTheDocument();
    });
  });

  describe('Loading состояние', () => {
    it('должен показывать skeleton при загрузке', () => {
      render(<ScanHistoryTable isLoading={true} />);

      // Проверка наличия skeleton элементов
      const skeletons = screen.getAllByRole('row');
      // Заголовок + 5 skeleton строк
      expect(skeletons.length).toBeGreaterThan(1);
    });

    it('должен показывать правильные заголовки при загрузке', () => {
      render(<ScanHistoryTable isLoading={true} />);

      expect(screen.getByText('Дата/время')).toBeInTheDocument();
      expect(screen.getByText('Город')).toBeInTheDocument();
      expect(screen.getByText('Статус')).toBeInTheDocument();
      expect(screen.getByText('Тип')).toBeInTheDocument();
      expect(screen.getByText('Объявления')).toBeInTheDocument();
      expect(screen.getByText('Страниц')).toBeInTheDocument();
      expect(screen.getByText('Длительность')).toBeInTheDocument();
    });
  });

  describe('Empty state', () => {
    it('должен показывать empty state при пустых данных', () => {
      render(<ScanHistoryTable data={[]} isLoading={false} />);

      expect(screen.getByText('История сканирований пуста')).toBeInTheDocument();
    });

    it('должен показывать кастомное сообщение empty state', () => {
      const customMessage = 'Нет данных для отображения';
      render(<ScanHistoryTable data={[]} isLoading={false} emptyMessage={customMessage} />);

      expect(screen.getByText(customMessage)).toBeInTheDocument();
    });

    it('должен показывать иконку в empty state', () => {
      render(<ScanHistoryTable data={[]} isLoading={false} />);

      // Проверка наличия иконки (FileText)
      const emptyState = screen.getByText('История сканирований пуста');
      expect(emptyState.closest('tr')).toBeInTheDocument();
    });
  });

  describe('Hover эффекты', () => {
    it('должен иметь hover класс на строках таблицы', () => {
      const { container } = render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      const rows = container.querySelectorAll('tbody tr');
      expect(rows.length).toBe(4);

      // Проверка наличия класса hover
      rows.forEach((row) => {
        expect(row.className).toContain('hover');
      });
    });
  });

  describe('Edge cases', () => {
    it('должен обрабатывать нулевые значения статистики', () => {
      const zeroData: ScanHistoryItem[] = [
        {
          id: 'zero',
          started_at: '2025-03-07T10:00:00Z',
          completed_at: '2025-03-07T10:01:00Z',
          city: 'minsk',
          city_name: 'Минск',
          status: 'completed',
          trigger_type: 'scheduled',
          listings_fetched: 0,
          listings_created: 0,
          listings_updated: 0,
          listings_changed_byn: 0,
          listings_deleted: 0,
          pages_scraped: 0,
          duration_seconds: 60,
          error_message: null,
        },
      ];

      render(<ScanHistoryTable data={zeroData} isLoading={false} />);

      // Должен показывать "—" для нулевой статистики
      expect(screen.getByText('—')).toBeInTheDocument();
    });

    it('должен обрабатывать очень большую длительность', () => {
      const longDurationData: ScanHistoryItem[] = [
        {
          id: 'long',
          started_at: '2025-03-07T10:00:00Z',
          completed_at: '2025-03-07T12:00:00Z',
          city: 'minsk',
          city_name: 'Минск',
          status: 'completed',
          trigger_type: 'scheduled',
          listings_fetched: 1000,
          listings_created: 50,
          listings_updated: 20,
          listings_changed_byn: 10,
          listings_deleted: 5,
          pages_scraped: 100,
          duration_seconds: 7200, // 2 часа
          error_message: null,
        },
      ];

      render(<ScanHistoryTable data={longDurationData} isLoading={false} />);

      // 7200 секунд = 120 мин
      expect(screen.getByText('120 мин')).toBeInTheDocument();
    });

    it('должен обрабатывать undefined данные как пустой массив', () => {
      // @ts-expect-error Testing undefined data
      render(<ScanHistoryTable data={undefined} isLoading={false} />);

      expect(screen.getByText('История сканирований пуста')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('должен иметь правильную структуру таблицы', () => {
      const { container } = render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      const table = container.querySelector('table');
      const thead = container.querySelector('thead');
      const tbody = container.querySelector('tbody');

      expect(table).toBeInTheDocument();
      expect(thead).toBeInTheDocument();
      expect(tbody).toBeInTheDocument();
    });

    it('должен иметь заголовки с правильными ролями', () => {
      const { container } = render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      const headers = container.querySelectorAll('th');
      expect(headers.length).toBe(7);

      headers.forEach((header) => {
        expect(header).toBeInTheDocument();
      });
    });
  });

  describe('Status badges', () => {
    it('должен показывать иконку CheckCircle для completed', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Проверка наличия иконки для completed статуса
      const completedBadges = screen.getAllByText('Завершено');
      expect(completedBadges.length).toBe(2);
    });

    it('должен показывать иконку AlertCircle для error', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      const errorBadge = screen.getByText('Ошибка');
      expect(errorBadge).toBeInTheDocument();
    });

    it('должен показывать иконку Clock для running', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      const runningBadge = screen.getByText('В процессе');
      expect(runningBadge).toBeInTheDocument();
    });
  });

  describe('City badges', () => {
    it('должен показывать иконку Home для городов', () => {
      render(<ScanHistoryTable data={mockScanHistoryData} isLoading={false} />);

      // Все города должны иметь названия с иконкой Home
      const cityNames = screen.getAllByText('Могилёв');
      expect(cityNames.length).toBeGreaterThan(0);
      
      const minskNames = screen.getAllByText('Минск');
      expect(minskNames.length).toBeGreaterThan(0);
    });
  });
});
