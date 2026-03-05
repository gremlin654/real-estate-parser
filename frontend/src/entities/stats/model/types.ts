import type {
  PriceTrendsResponse,
  RoomDistributionResponse,
  DailyActivityResponse,
  CityComparisonData,
} from '@/shared/types';

export interface StatsState {
  priceTrends: PriceTrendsResponse | null;
  roomDistribution: RoomDistributionResponse | null;
  dailyActivity: DailyActivityResponse | null;
  cityComparison: CityComparisonData | null;
}

export const calculatePriceChange = (data: PriceTrendsResponse['data']): number => {
  if (data.length < 2) return 0;

  const first = data[0].avg_price_usd;
  const last = data[data.length - 1].avg_price_usd;

  return ((last - first) / first) * 100;
};

export const getTotalListings = (data: RoomDistributionResponse['data']): number => {
  return data.reduce((sum, item) => sum + item.count, 0);
};

export const getAveragePrice = (data: RoomDistributionResponse['data']): number => {
  const total = getTotalListings(data);
  if (total === 0) return 0;

  const weightedSum = data.reduce((sum, item) => sum + item.avg_price * item.count, 0);
  return weightedSum / total;
};

export const getMostActiveDay = (data: DailyActivityResponse['data']): string | null => {
  if (data.length === 0) return null;

  const maxActivity = data.reduce((max, day) => {
    const activity = day.new_count + day.deleted_count + day.price_changed_count;
    return activity > max.activity ? { date: day.date, activity } : max;
  }, { date: data[0].date, activity: 0 });

  return maxActivity.date;
};
