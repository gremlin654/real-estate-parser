/**
 * Типы для аналитики цены за м²
 */

export interface PricePerM2Stats {
  average: number;
  median: number;
  min: number;
  max: number;
  count: number;
  currency: 'byn' | 'usd';
}

export interface PricePerM2Trend {
  date: string;
  average: number;
  median: number;
  count: number;
}

export interface PricePerM2TrendsResponse {
  city: string;
  period_days: number;
  interval: 'day' | 'week' | 'month';
  currency: 'byn' | 'usd';
  data: PricePerM2Trend[];
}

export interface PricePerM2DistributionBin {
  range_min: number;
  range_max: number;
  count: number;
  percentage: number;
}

export interface PricePerM2DistributionResponse {
  city: string;
  bins: number;
  currency: 'byn' | 'usd';
  data: PricePerM2DistributionBin[];
}

/**
 * Типы для Deal Finder (поиск выгодных квартир)
 */

export interface DealListing {
  id: string;
  kufar_id: string;
  url: string;
  title: string;
  price: number;
  price_usd?: number | null;
  currency: string;
  city: string | null;
  address: string | null;
  rooms: number | null;
  area: number | null;
  floor: number | null;
  total_floors?: number | null;
  // ✅ Дополнительные поля для совместимости с Listing (точно такие же типы)
  category: string | null;
  description: string | null;
  district: string | null;
  metro: string | null;
  house_year: number | null;
  images: string[];
  status: string;
  first_seen_at: string;
  last_seen_at: string;
  price_per_m2_byn?: number | null;
  price_per_m2_usd?: number | null;
  deal_percent: number;
  avg_price_per_m2: number;
}

export interface DealsResponse {
  items: DealListing[];
  total: number;
  limit: number;
  offset: number;
  avg_price_per_m2: number;
  currency: string;
}

export interface DealStats {
  total_deals: number;
  avg_deal_percent: number;
  best_deal_percent: number;
  avg_price_per_m2: number;
  total_savings: number;
}

/**
 * Типы для Price Drop Tracker (трекинг падения цены)
 */

export interface PriceDropListing {
  id: string;
  kufar_id: string;
  url: string;
  title: string;
  price: number;
  price_usd?: number | null;
  currency: string;
  city: string | null;
  address: string | null;
  rooms: number | null;
  area: number | null;
  floor: number | null;
  total_floors?: number | null;
  category: string | null;
  description: string | null;
  district: string | null;
  metro: string | null;
  house_year: number | null;
  images: string[];
  status: string;
  first_seen_at: string;
  last_seen_at: string;
  price_per_m2_byn?: number | null;
  price_per_m2_usd?: number | null;
  // Price drop метрики
  max_price: number;
  min_price: number;
  drop_percent: number;
  current_price: number;
}

export interface PriceDropResponse {
  items: PriceDropListing[];
  total: number;
  avg_drop_percent: number;
  max_drop_percent: number;
  min_drop_percent: number;
  currency: string;
}

export interface PriceDropHistoryItem {
  event_type: string;
  price_before: number;
  price_after: number;
  price_before_usd?: number | null;
  price_after_usd?: number | null;
  created_at: string;
}

export interface PriceDropHistoryResponse {
  items: PriceDropHistoryItem[];
  first_price: number;
  last_price: number;
  total_drop_percent: number;
}
