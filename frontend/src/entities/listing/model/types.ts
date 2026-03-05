import type { Listing, HistoryEvent } from '@/shared/types';

export interface ListingFilters {
  city?: string;
  page?: number;
  size?: number;
  status?: string;
  priceFrom?: number | null;
  priceTo?: number | null;
  rooms?: number[];
}

export interface ListingApiResponse {
  items: Listing[];
  total: number;
  page: number;
  size: number;
}

export const getListingPrice = (listing: Listing): number => {
  return listing.price_usd || listing.price;
};

export const getListingCurrency = (listing: Listing): string => {
  return listing.price_usd ? 'USD' : listing.currency;
};

export const isListingNew = (listing: Listing): boolean => {
  return listing.status === 'new';
};

export const isListingDeleted = (listing: Listing): boolean => {
  return listing.status === 'deleted' || listing.status === 'archived';
};

export const getFirstImage = (listing: Listing): string | null => {
  return listing.images?.[0] || null;
};
