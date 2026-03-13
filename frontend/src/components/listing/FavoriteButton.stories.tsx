import type { Meta, StoryObj } from '@storybook/react';
import { FavoriteButton } from './FavoriteButton';

const meta = {
  title: 'Components/FavoriteButton',
  component: FavoriteButton,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
  },
} satisfies Meta<typeof FavoriteButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    listingId: 1,
    size: 'md',
  },
};

export const Small: Story = {
  args: {
    listingId: 1,
    size: 'sm',
  },
};

export const Large: Story = {
  args: {
    listingId: 1,
    size: 'lg',
  },
};

export const Favorited: Story = {
  args: {
    listingId: 1,
    size: 'md',
  },
  parameters: {
    favorites: {
      initialFavorites: [1],
    },
  },
};
