/**
 * Типы для системы избранных объявлений (Favorites)
 */

import type { Listing } from './listing';

/**
 * Избранное объявление
 * Backend использует UUID для listing_id, поэтому тип string
 */
export interface Favorite {
  id: string;
  user_id: string;
  listing_id: string; // UUID как string (backend использует UUID)
  created_at: string;
  listing: Listing; // Вложенное объявление
}

/**
 * Response для списка избранных
 */
export interface FavoritesResponse {
  items: Favorite[];
  total: number;
  page: number;
  size: number;
}

/**
 * Response для добавления в избранное
 */
export interface FavoriteCreateResponse {
  id: string;
  user_id: string;
  listing_id: string;
  created_at: string;
  listing: Listing;
}

/**
 * Response для проверки избранного
 */
export interface FavoriteCheckResponse {
  is_favorite: boolean;
  listing_id: string;
}

/**
 * Фильтры для списка избранных
 */
export interface FavoritesFilters {
  city?: string;
  priceFrom?: number | null;
  priceTo?: number | null;
  rooms?: number[];
  roomsOther?: boolean;
  sort?: 'created_at_desc' | 'created_at_asc' | 'price_asc' | 'price_desc' | 'newest' | 'oldest';
}
