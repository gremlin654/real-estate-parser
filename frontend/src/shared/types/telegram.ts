export interface TelegramSubscription {
  id: string;
  user_id: string;
  city: string;
  rooms: number[] | null;
  price_min: number | null;
  price_max: number | null;
  currency: 'usd' | 'byn';
  price_per_m2_max: number | null;
  floor_min: number | null;
  floor_max: number | null;
  notify_only_price_drop: boolean;
  exclude_deal_below_percent: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TelegramSubscriptionCreate {
  city: string;
  rooms?: number[] | null;
  price_min?: number | null;
  price_max?: number | null;
  currency?: 'usd' | 'byn';
  price_per_m2_max?: number | null;
  floor_min?: number | null;
  floor_max?: number | null;
  notify_only_price_drop?: boolean;
  exclude_deal_below_percent?: number | null;
}

export interface TelegramSubscriptionUpdate {
  city?: string;
  rooms?: number[] | null;
  price_min?: number | null;
  price_max?: number | null;
  currency?: 'usd' | 'byn';
  price_per_m2_max?: number | null;
  floor_min?: number | null;
  floor_max?: number | null;
  notify_only_price_drop?: boolean;
  exclude_deal_below_percent?: number | null;
  is_active?: boolean;
}

export interface TelegramWebAppConfig {
  cities: { code: string; name: string }[];
  currencies: { code: string; name: string; symbol: string }[];
  room_options: { value: string; label: string }[];
  max_subscriptions: number;
  current_subscription_count: number;
}

export interface TelegramNotificationStats {
  total_notifications: number;
  successful: number;
  failed: number;
  duplicated: number;
  rate_limited: number;
}