import type { Meta, StoryObj } from '@storybook/react';
import { PriceHistoryChart } from './PriceHistoryChart';
import type { PriceDropHistoryItem } from '@/shared/types';

const meta = {
  title: 'Stats/PriceHistoryChart',
  component: PriceHistoryChart,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof PriceHistoryChart>;

export default meta;
type Story = StoryObj<typeof meta>;

// Пример данных для истории цен
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
  {
    event_type: 'price_changed',
    price_before: 48000,
    price_after: 46500,
    created_at: '2024-02-10T16:45:00Z',
  },
  {
    event_type: 'price_changed',
    price_before: 46500,
    price_after: 44500,
    created_at: '2024-02-20T11:20:00Z',
  },
];

const shortHistory: PriceDropHistoryItem[] = [
  {
    event_type: 'created',
    price_before: 0,
    price_after: 55000,
    created_at: '2024-02-01T10:00:00Z',
  },
  {
    event_type: 'price_changed',
    price_before: 55000,
    price_after: 52000,
    created_at: '2024-02-15T14:30:00Z',
  },
];

const emptyHistory: PriceDropHistoryItem[] = [];

// Story с полной историей
export const FullHistory: Story = {
  args: {
    history: sampleHistory,
    currency: 'USD',
  },
};

// Story с короткой историей
export const ShortHistory: Story = {
  args: {
    history: shortHistory,
    currency: 'USD',
  },
};

// Story для BYN
export const BYN: Story = {
  args: {
    history: sampleHistory,
    currency: 'BYN',
  },
};

// Story с пустой историей
export const Empty: Story = {
  args: {
    history: emptyHistory,
    currency: 'USD',
  },
};

// Story с большим падением
const largeDropHistory: PriceDropHistoryItem[] = [
  {
    event_type: 'created',
    price_before: 0,
    price_after: 70000,
    created_at: '2024-01-01T10:00:00Z',
  },
  {
    event_type: 'price_changed',
    price_before: 70000,
    price_after: 65000,
    created_at: '2024-01-10T14:30:00Z',
  },
  {
    event_type: 'price_changed',
    price_before: 65000,
    price_after: 58000,
    created_at: '2024-01-20T09:15:00Z',
  },
  {
    event_type: 'price_changed',
    price_before: 58000,
    price_after: 50000,
    created_at: '2024-02-01T16:45:00Z',
  },
  {
    event_type: 'price_changed',
    price_before: 50000,
    price_after: 42000,
    created_at: '2024-02-15T11:20:00Z',
  },
];

export const LargeDrop: Story = {
  args: {
    history: largeDropHistory,
    currency: 'USD',
  },
};
