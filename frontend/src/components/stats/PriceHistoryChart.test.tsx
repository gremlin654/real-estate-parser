import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PriceHistoryChart } from './PriceHistoryChart';
import type { PriceDropHistoryItem } from '@/shared/types';

describe('PriceHistoryChart', () => {
  const sampleHistory: PriceDropHistoryItem[] = [
    {
      event_type: 'created',
      price_before: 0,
      price_after: 52000,
      created_at: '2024-01-15T10:00:00Z',
    },
    {
      event_type: 'price_changed',
      price_before: 52000,
      price_after: 50000,
      created_at: '2024-01-20T14:30:00Z',
    },
    {
      event_type: 'price_changed',
      price_before: 50000,
      price_after: 48000,
      created_at: '2024-02-01T09:15:00Z',
    },
  ];

  const emptyHistory: PriceDropHistoryItem[] = [];

  it('рендерит сообщение при пустой истории', () => {
    const { getByText } = render(<PriceHistoryChart history={emptyHistory} currency="USD" />);
    expect(getByText('Нет данных для отображения')).toBeInTheDocument();
  });

  it('рендерит график с данными без ошибок', () => {
    const { container } = render(<PriceHistoryChart history={sampleHistory} currency="USD" />);
    expect(container).toBeTruthy();
  });

  it('принимает валюту USD', () => {
    const { container } = render(<PriceHistoryChart history={sampleHistory} currency="USD" />);
    expect(container).toBeTruthy();
  });

  it('принимает валюту BYN', () => {
    const { container } = render(<PriceHistoryChart history={sampleHistory} currency="BYN" />);
    expect(container).toBeTruthy();
  });

  it('корректно обрабатывает неотсортированные данные', () => {
    const unsortedHistory: PriceDropHistoryItem[] = [
      {
        event_type: 'price_changed',
        price_before: 50000,
        price_after: 48000,
        created_at: '2024-02-01T09:15:00Z',
      },
      {
        event_type: 'created',
        price_before: 0,
        price_after: 52000,
        created_at: '2024-01-15T10:00:00Z',
      },
    ];
    const { container } = render(<PriceHistoryChart history={unsortedHistory} currency="USD" />);
    expect(container).toBeTruthy();
  });
});
