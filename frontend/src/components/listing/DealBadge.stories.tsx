import type { Meta, StoryObj } from '@storybook/react';
import { DealBadge } from './DealBadge';

const meta = {
  title: 'Listing/DealBadge',
  component: DealBadge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    dealPercent: {
      control: {
        type: 'range',
        min: -30,
        max: 0,
        step: 1,
      },
    },
  },
} satisfies Meta<typeof DealBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story для всех состояний выгоды
export const Low: Story = {
  args: {
    dealPercent: -12, // -10% to -15%: оранжевый
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
    dealPercent: -17, // -15% to -20%: красно-оранжевый
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
    dealPercent: -25, // -20%+: красный
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
    dealPercent: -10, // Порог отображения
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
    dealPercent: -30, // Экстремальная выгода
  },
  decorators: [
    (Story: Story) => (
      <div className="relative w-64 h-32 bg-gray-100 rounded-lg">
        <Story />
      </div>
    ),
  ],
};
