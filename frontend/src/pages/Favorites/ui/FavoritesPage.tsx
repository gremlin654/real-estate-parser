'use client';

import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFavoritesQuery } from '@/api/listings';
import { useFavoritesStore } from '@/store/favoritesStore';
import { Card } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/shared/ui/pagination';
import { Star, ArrowLeft } from 'lucide-react';
import { FavoritesFilter } from '@/features/favorites/ui/FavoritesFilter';
import { FavoritesExport } from '@/features/favorites/ui/FavoritesExport';
import { ListingCardWidget } from '@/widgets/ListingCard/ui/ListingCardWidget';
import type { FavoritesFilters } from '@/shared/types';

const PAGE_SIZE = 20;

export function FavoritesPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<FavoritesFilters>({});
  
  // Синхронизируем store с серверными данными
  const setFavorites = useFavoritesStore((state) => state.setFavorites);

  // Мемоизируем filters чтобы queryKey не менялся при каждом рендере
  const memoizedFilters = useMemo(() => filters, [filters]);

  const { data, isLoading, error, refetch } = useFavoritesQuery(page, PAGE_SIZE, memoizedFilters, {
    refetchOnMount: 'always', // Всегда обновлять данные при монтировании компонента
  });

  // Синхронизация store с сервером при загрузке данных
  useEffect(() => {
    if (data?.items) {
      const listingIds = data.items.map((fav) => fav.listing_id);
      setFavorites(listingIds);
    }
  }, [data?.items, setFavorites]);

  const totalPages = Math.ceil((data?.total || 0) / PAGE_SIZE);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleResetFilters = () => {
    setFilters({});
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(-1)}
            className="shrink-0"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-amber-500 to-orange-500 bg-clip-text text-transparent flex items-center gap-3">
              <Star className="w-8 h-8 text-amber-500 fill-current" />
              Избранные объявления
            </h1>
            <p className="text-muted-foreground mt-1">
              {data?.total || 0} избранных объявлений
            </p>
          </div>
        </div>

        <FavoritesExport filters={filters} disabled={isLoading} />
      </div>

      {/* Filters */}
      <FavoritesFilter
        filters={filters}
        onChange={setFilters}
        onReset={handleResetFilters}
      />

      {/* Loading state */}
      {isLoading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <Card className="p-6 bg-red-50 border-red-200">
          <p className="text-red-600 font-medium">
            Ошибка загрузки избранных: {(error as Error).message}
          </p>
        </Card>
      )}

      {/* Empty state */}
      {!isLoading && !error && data && data.items.length === 0 && (
        <Card className="p-12 text-center">
          <Star className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-700 mb-2">
            Нет избранных объявлений
          </h2>
          <p className="text-gray-500 mb-6">
            Добавьте объявления в избранное, чтобы быстро доступа к ним
          </p>
          <Button onClick={() => navigate('/listings')}>
            Перейти к объявлениям
          </Button>
        </Card>
      )}

      {/* Listings grid */}
      {!isLoading && !error && data && data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.items.map((favorite) => (
              <ListingCardWidget
                key={favorite.id}
                listing={favorite.listing}
                withFavoriteButton={true}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      if (page > 1) handlePageChange(page - 1);
                    }}
                    className={page === 1 ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
                
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                  <PaginationItem key={pageNum}>
                    <PaginationLink
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        handlePageChange(pageNum);
                      }}
                      isActive={pageNum === page}
                    >
                      {pageNum}
                    </PaginationLink>
                  </PaginationItem>
                ))}
                
                <PaginationItem>
                  <PaginationNext
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      if (page < totalPages) handlePageChange(page + 1);
                    }}
                    className={page === totalPages ? 'pointer-events-none opacity-50' : ''}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}
        </>
      )}
    </div>
  );
}
