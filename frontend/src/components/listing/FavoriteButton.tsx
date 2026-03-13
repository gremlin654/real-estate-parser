import { useState } from 'react';
import { Star } from 'lucide-react';
import { useAddToFavorites, useRemoveFromFavorites } from '@/api/listings';
import { useFavoritesStore } from '@/store/favoritesStore';
import { cn } from '@/lib/utils';

interface FavoriteButtonProps {
  listingId: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const FavoriteButton = ({ listingId, className, size = 'md' }: FavoriteButtonProps) => {
  const [isAnimating, setIsAnimating] = useState(false);
  
  const isFavorite = useFavoritesStore((state) => state.isFavorite(listingId));
  const toggleFavorite = useFavoritesStore((state) => state.toggleFavorite);

  const addMutation = useAddToFavorites();
  const removeMutation = useRemoveFromFavorites();

  const handleToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsAnimating(true);
    
    try {
      // Используем готовый метод из store с optimistic update + rollback
      await toggleFavorite(listingId, addMutation, removeMutation);
    } finally {
      setTimeout(() => setIsAnimating(false), 300);
    }
  };

  const sizeClasses = {
    sm: 'w-7 h-7 p-1',
    md: 'w-8 h-8 p-1.5',
    lg: 'w-10 h-10 p-2',
  };

  const iconSizeClasses = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <button
      type="button"
      onClick={handleToggle}
      disabled={addMutation.isPending || removeMutation.isPending}
      className={cn(
        'rounded-full transition-all duration-200 ease-in-out',
        'inline-flex items-center justify-center',
        'hover:scale-110 active:scale-95',
        'focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        isFavorite
          ? 'bg-amber-400/90 hover:bg-amber-500 text-white'
          : 'bg-gray-100/90 hover:bg-gray-200 text-gray-400 hover:text-gray-600',
        sizeClasses[size],
        isAnimating && 'scale-125',
        className
      )}
      aria-label={isFavorite ? 'Удалить из избранного' : 'Добавить в избранное'}
      aria-pressed={isFavorite}
    >
      {addMutation.isPending || removeMutation.isPending ? (
        <div className={cn('animate-spin', iconSizeClasses[size])}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
        </div>
      ) : isFavorite ? (
        <Star className={cn(iconSizeClasses[size], 'fill-current')} />
      ) : (
        <Star className={iconSizeClasses[size]} />
      )}
    </button>
  );
};
