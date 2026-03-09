export * from './listing';
export * from './stats';

export interface PriceTrendData {
  year: number;
  month: number;
  avg_price_usd: number;
  listings_count: number;
}
