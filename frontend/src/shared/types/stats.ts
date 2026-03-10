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
