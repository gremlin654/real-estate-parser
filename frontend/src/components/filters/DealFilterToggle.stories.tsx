import type { Meta, StoryObj } from '@storybook/react';
import { DealFilterToggle } from './DealFilterToggle';
import { useState } from 'react';

const meta = {
  title: 'Filters/DealFilterToggle',
  component: DealFilterToggle,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    discountThreshold: {
      control: {
        type: 'number',
        step: 5,
      },
    },
  },
} satisfies Meta<typeof DealFilterToggle>;

export default meta;
type Story = StoryObj<typeof meta>;

// Story с интерактивным состоянием
export const Default: Story = {
  render: (args) => {
    const [enabled, setEnabled] = useState(args.enabled);
    return (
      <DealFilterToggle
        {...args}
        enabled={enabled}
        onToggle={setEnabled}
      />
    );
  },
  args: {
    enabled: false,
    discountThreshold: -10,
  },
};

export const Enabled: Story = {
  render: (args) => {
    const [enabled, setEnabled] = useState(args.enabled);
    return (
      <DealFilterToggle
        {...args}
        enabled={enabled}
        onToggle={setEnabled}
      />
    );
  },
  args: {
    enabled: true,
    discountThreshold: -10,
  },
};

export const CustomThreshold: Story = {
  render: (args) => {
    const [enabled, setEnabled] = useState(false);
    return (
      <DealFilterToggle
        {...args}
        enabled={enabled}
        onToggle={setEnabled}
      />
    );
  },
  args: {
    enabled: false,
    discountThreshold: -15,
  },
};

export const Disabled: Story = {
  render: (args) => {
    const [enabled, setEnabled] = useState(args.enabled);
    return (
      <DealFilterToggle
        {...args}
        enabled={enabled}
        onToggle={setEnabled}
      />
    );
  },
  args: {
    enabled: false,
    discountThreshold: -10,
  },
};
