export * from './listing';

export interface PriceTrendData {
  year: number;
  month: number;
  avg_price_usd: number;
  listings_count: number;
}
