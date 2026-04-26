import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  TelegramSubscription,
  TelegramSubscriptionCreate,
  TelegramSubscriptionUpdate,
  TelegramWebAppConfig,
  TelegramNotificationStats,
} from '@/shared/types/telegram';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export const useTelegramSubscriptions = () => {
  return useQuery<TelegramSubscription[]>({
    queryKey: ['telegram', 'subscriptions'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/telegram/subscriptions`);
      if (!response.ok) {
        throw new Error('Failed to fetch subscriptions');
      }
      return response.json();
    },
    staleTime: 30000,
  });
};

export const useTelegramSubscription = (id: string) => {
  return useQuery<TelegramSubscription>({
    queryKey: ['telegram', 'subscriptions', id],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/telegram/subscriptions/${id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch subscription');
      }
      return response.json();
    },
    enabled: !!id,
  });
};

export const useCreateTelegramSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TelegramSubscriptionCreate) => {
      const response = await fetch(`${API_BASE}/telegram/subscriptions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Failed to create subscription');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['telegram', 'subscriptions'] });
    },
  });
};

export const useUpdateTelegramSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TelegramSubscriptionUpdate }) => {
      const response = await fetch(`${API_BASE}/telegram/subscriptions/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Failed to update subscription');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['telegram', 'subscriptions'] });
    },
  });
};

export const useDeleteTelegramSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await fetch(`${API_BASE}/telegram/subscriptions/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete subscription');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['telegram', 'subscriptions'] });
    },
  });
};

export const useTelegramWebAppConfig = () => {
  return useQuery<TelegramWebAppConfig>({
    queryKey: ['telegram', 'webapp', 'config'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/telegram/webapp/config`);
      if (!response.ok) {
        throw new Error('Failed to fetch config');
      }
      return response.json();
    },
    staleTime: 60000,
  });
};

export const useTelegramNotificationStats = () => {
  return useQuery<TelegramNotificationStats>({
    queryKey: ['telegram', 'stats'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/telegram/stats`);
      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }
      return response.json();
    },
    staleTime: 30000,
  });
};