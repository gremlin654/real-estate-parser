import type { Meta, StoryObj } from '@storybook/react';
import { DealTooltip } from './DealTooltip';

const meta = {
  title: 'Listing/DealTooltip',
  component: DealTooltip,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    currentPricePerM2: {
      control: {
        type: 'number',
        step: 100,
      },
    },
    avgPricePerM2: {
      control: {
        type: 'number',
        step: 100,
      },
    },
    dealPercent: {
      control: {
        type: 'number',
        step: 1,
      },
    },
    currency: {
      control: {
        type: 'radio',
        options: ['USD', 'BYN'],
      },
    },
    area: {
      control: {
        type: 'number',
        step: 1,
      },
    },
  },
} satisfies Meta<typeof DealTooltip>;

export default meta;
type Story = StoryObj<typeof meta>;

export const USD: Story = {
  args: {
    currentPricePerM2: 772,
    avgPricePerM2: 920,
    dealPercent: -16,
    currency: 'USD',
    area: 54,
    children: (
      <span className="text-lg font-bold">$41,688</span>
    ),
  },
};

export const BYN: Story = {
  args: {
    currentPricePerM2: 2500,
    avgPricePerM2: 3000,
    dealPercent: -17,
    currency: 'BYN',
    area: 60,
    children: (
      <span className="text-lg font-bold">150,000 BYN</span>
    ),
  },
};

export const WithoutArea: Story = {
  args: {
    currentPricePerM2: 800,
    avgPricePerM2: 950,
    dealPercent: -16,
    currency: 'USD',
    area: null,
    children: (
      <span className="text-lg font-bold">$48,000</span>
    ),
  },
};

export const SmallDeal: Story = {
  args: {
    currentPricePerM2: 880,
    avgPricePerM2: 920,
    dealPercent: -4,
    currency: 'USD',
    area: 50,
    children: (
      <span className="text-lg font-bold">$44,000</span>
    ),
  },
};

export const LargeDeal: Story = {
  args: {
    currentPricePerM2: 650,
    avgPricePerM2: 920,
    dealPercent: -29,
    currency: 'USD',
    area: 70,
    children: (
      <span className="text-lg font-bold">$45,500</span>
    ),
  },
};
