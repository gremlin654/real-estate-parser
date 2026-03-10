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
  price_per_m2_byn?: number | null;
  price_per_m2_usd?: number | null;
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
  // Поддержка параллельных сканирований (v3.1)
  scanning_cities?: Array<{
    city: string;
    city_name: string;
    trigger_type: 'manual' | 'scheduled';
    stage: 'starting' | 'marking_deleted' | 'fetching' | 'parsing' | 'upserting' | 'marking_deleted_final' | 'done' | 'error';
    pages_scraped: number;
    listings_fetched: number;
    listings_processed: number;
    elapsed_seconds: number;
    is_stable: boolean;
  }>;
}

export interface HistoryEvent {
  id: string;
  event_type: string;
  price_before?: number | null;
  price_after?: number | null;
  price_before_usd?: number | null;
  price_after_usd?: number | null;
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

export interface ScanHistoryItem {
  id: string;
  started_at: string;
  completed_at: string | null;
  city: string;
  city_name: string;
  status: 'running' | 'completed' | 'error';
  trigger_type: 'manual' | 'scheduled';
  listings_fetched: number;
  listings_created: number;
  listings_updated: number;
  listings_changed_byn: number;
  listings_deleted: number;
  pages_scraped: number;
  duration_seconds: number | null;
  error_message: string | null;
}

export interface ScanHistoryResponse {
  items: ScanHistoryItem[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
  date_from?: string;
  date_to?: string;
}

export type City = 'minsk' | 'mogilev' | 'grodno' | 'brest' | 'gomel' | 'vitebsk';

/**
 * Настройки сканирования для конкретного города
 */
export interface CitySettingsResponse {
  enabled: boolean;
  scan_interval_minutes: number;
  updated_at: string | null;
}

/**
 * Запрос на обновление настроек города
 */
export interface CitySettingsUpdateRequest {
  enabled?: boolean;
  scan_interval_minutes?: number;
}

// Re-export из constants для устранения дублирования
export { CITIES } from '../config/constants';
