import type { Meta, StoryObj } from '@storybook/react';
import { PriceDropBadge } from './PriceDropBadge';

const meta = {
  title: 'Listing/PriceDropBadge',
  component: PriceDropBadge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    dropPercent: {
      control: {
        type: 'range',
        min: 0,
        max: 50,
        step: 1,
      },
    },
  },
} satisfies Meta<typeof PriceDropBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story для всех состояний падения цены
export const Low: Story = {
  args: {
    dropPercent: 7, // 5% to 10%: жёлтый
  },
  decorators: [
    (Story: Story) => (
      <div className="relative w-64 h-32 bg-gray-100 rounded-lg">
        <Story />
      </div>
    ),
  ],
};

export const Medium: Story = {
  args: {
    dropPercent: 15, // 10% to 20%: оранжевый
  },
  decorators: [
    (Story: Story) => (
      <div className="relative w-64 h-32 bg-gray-100 rounded-lg">
        <Story />
      </div>
    ),
  ],
};

export const High: Story = {
  args: {
    dropPercent: 25, // 20%+: красный
  },
  decorators: [
    (Story: Story) => (
      <div className="relative w-64 h-32 bg-gray-100 rounded-lg">
        <Story />
      </div>
    ),
  ],
};

export const Threshold: Story = {
  args: {
    dropPercent: 5, // Порог отображения
  },
  decorators: [
    (Story: Story) => (
      <div className="relative w-64 h-32 bg-gray-100 rounded-lg">
        <Story />
      </div>
    ),
  ],
};

export const Extreme: Story = {
  args: {
    dropPercent: 40, // Экстремальное падение
  },
  decorators: [
    (Story: Story) => (
      <div className="relative w-64 h-32 bg-gray-100 rounded-lg">
        <Story />
      </div>
    ),
  ],
};

export const BelowThreshold: Story = {
  args: {
    dropPercent: 3, // Ниже порога - не отображается
  },
  decorators: [
    (Story: Story) => (
      <div className="relative w-64 h-32 bg-gray-100 rounded-lg">
        <Story />
      </div>
    ),
  ],
};
