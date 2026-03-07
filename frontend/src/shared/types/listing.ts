export interface Listing {
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
  deleted_at?: string | null;
}

export interface PaginatedResponse {
  items: Listing[];
  total: number;
  page: number;
  size: number;
}

export interface Summary {
  new_today: number;
  deleted_today: number;
  price_changed_usd_today: number;
  active_total: number;
}

export interface ScanProgress {
  is_scanning: boolean;
  city: string | null;
  city_name?: string;
  stage: string;
  pages_scraped: number;
  listings_fetched: number;
  listings_processed: number;
  elapsed_seconds: number;
  is_stable: boolean;
}

export interface HistoryEvent {
  id: string;
  event_type: string;
  price_before?: number | null;
  price_after?: number | null;
  changed_fields?: Record<string, any> | null;
  snapshot?: Record<string, any> | null;
  created_at: string;
}

export interface PriceTrendData {
  year: number;
  month: number;
  avg_price_usd: number;
  listings_count: number;
}

export interface PriceTrendsResponse {
  city: string;
  rooms: number;
  period_months: number;
  data: PriceTrendData[];
}

export interface RoomDistributionItem {
  rooms: number;
  count: number;
  avg_price: number;
}

export interface RoomDistributionResponse {
  city: string;
  data: RoomDistributionItem[];
}

export interface DailyActivityItem {
  date: string;
  new_count: number;
  deleted_count: number;
  price_changed_count: number;
}

export interface DailyActivityResponse {
  city: string;
  period_days: number;
  data: DailyActivityItem[];
}

export interface ScanSchedule {
  scan_interval_minutes: number;
  enabled: boolean;
  updated_at: string;
}

export interface CityComparisonData {
  data: Array<{
    city: string;
    avg_price_usd: number;
    count: number;
  }>;
}

export type City = 'minsk' | 'mogilev' | 'grodno' | 'brest' | 'gomel' | 'vitebsk';

export const CITIES: Record<City, string> = {
  minsk: 'Минск',
  mogilev: 'Могилёв',
  grodno: 'Гродно',
  brest: 'Брест',
  gomel: 'Гомель',
  vitebsk: 'Витебск',
};
