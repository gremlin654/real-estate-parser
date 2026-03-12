import type { Meta, StoryObj } from '@storybook/react';
import { PriceDropTooltip } from './PriceDropTooltip';

const meta = {
  title: 'Listing/PriceDropTooltip',
  component: PriceDropTooltip,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    maxPrice: {
      control: { type: 'number', step: 1000 },
    },
    minPrice: {
      control: { type: 'number', step: 1000 },
    },
    currentPrice: {
      control: { type: 'number', step: 1000 },
    },
    dropPercent: {
      control: { type: 'number', min: 0, max: 50, step: 1 },
    },
    currency: {
      control: { type: 'radio', options: ['USD', 'BYN'] },
    },
  },
} satisfies Meta<typeof PriceDropTooltip>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story для USD
export const USD: Story = {
  args: {
    maxPrice: 52000,
    minPrice: 44500,
    currentPrice: 44500,
    dropPercent: 14,
    currency: 'USD',
    children: <span className="text-2xl font-bold">$44,500</span>,
  },
};

// Story для BYN
export const BYN: Story = {
  args: {
    maxPrice: 169000,
    minPrice: 144625,
    currentPrice: 144625,
    dropPercent: 14,
    currency: 'BYN',
    children: <span className="text-2xl font-bold">144 625 BYN</span>,
  },
};

// Story с большим падением
export const HighDrop: Story = {
  args: {
    maxPrice: 60000,
    minPrice: 42000,
    currentPrice: 42000,
    dropPercent: 30,
    currency: 'USD',
    children: <span className="text-2xl font-bold">$42,000</span>,
  },
};

// Story с небольшим падением
export const LowDrop: Story = {
  args: {
    maxPrice: 50000,
    minPrice: 47500,
    currentPrice: 47500,
    dropPercent: 5,
    currency: 'USD',
    children: <span className="text-2xl font-bold">$47,500</span>,
  },
};
