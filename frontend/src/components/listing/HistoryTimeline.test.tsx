import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HistoryTimeline } from '@/components/listing/HistoryTimeline';
import type { HistoryEvent } from '@/api/listings';

describe('HistoryTimeline', () => {
  const mockEvents: HistoryEvent[] = [
    {
      id: '1',
      listing_id: 'l1',
      event_type: 'created',
      created_at: '2024-01-01T10:00:00Z',
    },
    {
      id: '2',
      listing_id: 'l1',
      event_type: 'price_changed',
      price_before: 100000,
      price_after: 95000,
      created_at: '2024-01-02T10:00:00Z',
    },
    {
      id: '3',
      listing_id: 'l1',
      event_type: 'edited',
      changed_fields: {
        title: ['Old Title', 'New Title'],
        description: ['Old desc', 'New desc'],
      },
      created_at: '2024-01-03T10:00:00Z',
    },
  ];

  describe('loading state', () => {
    it('должен показывать индикатор загрузки', () => {
      render(<HistoryTimeline events={[]} isLoading />);

      const spinner = screen.getByTestId('loading-spinner');
      expect(spinner).toHaveClass('animate-spin');
    });
  });

  describe('empty state', () => {
    it('должен показывать пустое состояние для пустого массива', () => {
      render(<HistoryTimeline events={[]} />);

      expect(screen.getByText('История пуста')).toBeInTheDocument();
      expect(screen.getByText('Изменений пока не было')).toBeInTheDocument();
    });

    it('должен показывать пустое состояние для null', () => {
      render(<HistoryTimeline events={null as any} />);

      expect(screen.getByText('История пуста')).toBeInTheDocument();
    });

    it('должен показывать пустое состояние если только restored события', () => {
      const restoredEvents: HistoryEvent[] = [
        {
          id: '1',
          listing_id: 'l1',
          event_type: 'restored',
          created_at: '2024-01-01T10:00:00Z',
        },
      ];

      render(<HistoryTimeline events={restoredEvents} />);

      expect(screen.getByText('История пуста')).toBeInTheDocument();
    });
  });

  describe('event rendering', () => {
    it('должен рендерить created событие', () => {
      render(<HistoryTimeline events={[mockEvents[0]]} />);

      expect(screen.getByText('Создано')).toBeInTheDocument();
    });

    it('должен рендерить price_changed событие', () => {
      render(<HistoryTimeline events={[mockEvents[1]]} />);

      expect(screen.getByText('Изменение цены')).toBeInTheDocument();
      expect(screen.getByText('Было')).toBeInTheDocument();
      expect(screen.getByText('Стало')).toBeInTheDocument();
      expect(screen.getByText(/100[,\s]000\sBYN/)).toBeInTheDocument();
      expect(screen.getByText(/95[,\s]000\sBYN/)).toBeInTheDocument();
    });

    it('должен рендерить edited событие', () => {
      render(<HistoryTimeline events={[mockEvents[2]]} />);

      expect(screen.getByText('Редактировано')).toBeInTheDocument();
      expect(screen.getByText('Изменённые поля:')).toBeInTheDocument();
      expect(screen.getByText('Заголовок:')).toBeInTheDocument();
    });

    it('должен фильтровать restored события', () => {
      const eventsWithRestored: HistoryEvent[] = [
        ...mockEvents,
        {
          id: '4',
          listing_id: 'l1',
          event_type: 'restored',
          created_at: '2024-01-04T10:00:00Z',
        },
      ];

      render(<HistoryTimeline events={eventsWithRestored} />);

      const restoredBadges = screen.queryAllByText('Восстановлено');
      expect(restoredBadges).toHaveLength(0);
    });
  });

  describe('price change display', () => {
    it('должен показывать старую цену зачёркнутой', () => {
      render(<HistoryTimeline events={[mockEvents[1]]} />);

      const oldPrice = screen.getByText(/100[,\s]000\sBYN/);
      expect(oldPrice).toHaveClass('line-through');
    });

    it('должен показывать новую цену зелёным', () => {
      render(<HistoryTimeline events={[mockEvents[1]]} />);

      const newPrice = screen.getByText(/95[,\s]000\sBYN/);
      expect(newPrice).toHaveClass('text-green-500');
    });

    it('должен показывать стрелку между ценами', () => {
      render(<HistoryTimeline events={[mockEvents[1]]} />);

      expect(screen.getByText('→')).toBeInTheDocument();
    });
  });

  describe('changed fields display', () => {
    it('должен показывать старое значение зачёркнутым', () => {
      render(<HistoryTimeline events={[mockEvents[2]]} />);

      const oldTitle = screen.getByText('Old Title');
      expect(oldTitle).toHaveClass('line-through');
      expect(oldTitle).toHaveClass('text-red-500');
    });

    it('должен показывать новое значение зелёным', () => {
      render(<HistoryTimeline events={[mockEvents[2]]} />);

      const newTitle = screen.getByText('New Title');
      expect(newTitle).toHaveClass('text-green-500');
      expect(newTitle).toHaveClass('font-medium');
    });

    it('должен показывать перевод полей на русский', () => {
      render(<HistoryTimeline events={[mockEvents[2]]} />);

      expect(screen.getByText('Заголовок:')).toBeInTheDocument();
    });
  });

  describe('date formatting', () => {
    it('должен отображать дату события', () => {
      render(<HistoryTimeline events={[mockEvents[0]]} />);

      // Date should be formatted in Russian
      expect(screen.getByText(/января 2024/)).toBeInTheDocument();
    });
  });

  describe('badge colors', () => {
    it('должен иметь синий badge для created', () => {
      render(<HistoryTimeline events={[mockEvents[0]]} />);

      const badge = screen.getByText('Создано').closest('div');
      expect(badge).toHaveClass('bg-blue-500');
    });

    it('должен иметь жёлтый badge для price_changed', () => {
      render(<HistoryTimeline events={[mockEvents[1]]} />);

      const badge = screen.getByText('Изменение цены').closest('div');
      expect(badge).toHaveClass('bg-yellow-500');
    });

    it('должен иметь фиолетовый badge для edited', () => {
      render(<HistoryTimeline events={[mockEvents[2]]} />);

      const badge = screen.getByText('Редактировано').closest('div');
      expect(badge).toHaveClass('bg-purple-500');
    });
  });

  describe('timeline structure', () => {
    it('должен рендерить несколько событий', () => {
      render(<HistoryTimeline events={mockEvents} />);

      expect(screen.getByText('Создано')).toBeInTheDocument();
      expect(screen.getByText('Изменение цены')).toBeInTheDocument();
      expect(screen.getByText('Редактировано')).toBeInTheDocument();
    });

    it('должен иметь линию между событиями', () => {
      const { container } = render(<HistoryTimeline events={mockEvents} />);

      // Should have divider lines between events
      const lines = container.querySelectorAll('.w-0\\.5');
      expect(lines.length).toBeGreaterThan(0);
    });
  });
});
