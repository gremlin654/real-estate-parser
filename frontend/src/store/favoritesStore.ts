import { create } from 'zustand';
import { toast } from 'sonner';

interface FavoritesStore {
  // IDs избранных объявлений (UUID как string)
  favorites: Set<string>;
  isLoading: boolean;
  error: string | null;

  // Actions
  setFavorites: (ids: string[]) => void;
  addFavorite: (listingId: string) => void;
  removeFavorite: (listingId: string) => void;
  toggleFavorite: (listingId: string, addMutation: any, removeMutation: any) => Promise<void>;
  isFavorite: (listingId: string) => boolean;
  loadFromStorage: () => void;
  saveToStorage: () => void;
  clearError: () => void;
}

const STORAGE_KEY = 'kufar-favorites';

export const useFavoritesStore = create<FavoritesStore>((set, get) => ({
  favorites: new Set<string>(),
  isLoading: false,
  error: null,

  setFavorites: (ids) => {
    set({ favorites: new Set(ids) });
  },

  addFavorite: (listingId) => {
    set((state) => {
      const newFavorites = new Set(state.favorites);
      newFavorites.add(listingId);
      return { favorites: newFavorites };
    });
    // Сохраняем в localStorage
    get().saveToStorage();
  },

  removeFavorite: (listingId) => {
    set((state) => {
      const newFavorites = new Set(state.favorites);
      newFavorites.delete(listingId);
      return { favorites: newFavorites };
    });
    // Сохраняем в localStorage
    get().saveToStorage();
  },

  toggleFavorite: async (listingId, addMutation, removeMutation) => {
    const isFav = get().isFavorite(listingId);

    // Optimistic update - обновляем UI до ответа сервера
    if (isFav) {
      get().removeFavorite(listingId);
    } else {
      get().addFavorite(listingId);
    }

    try {
      set({ isLoading: true });

      // Вызываем соответствующую мутацию
      if (isFav) {
        await removeMutation.mutateAsync(listingId);
        toast.success('Удалено из избранных');
      } else {
        await addMutation.mutateAsync(listingId);
        toast.success('Добавлено в избранное');
      }
    } catch (error) {
      // Rollback на ошибку - возвращаем состояние назад
      if (isFav) {
        get().addFavorite(listingId);
      } else {
        get().removeFavorite(listingId);
      }

      const errorMessage = error instanceof Error ? error.message : 'Ошибка операции';
      toast.error(errorMessage);
      set({ error: errorMessage });
    } finally {
      set({ isLoading: false });
    }
  },

  isFavorite: (listingId) => {
    return get().favorites.has(listingId);
  },

  loadFromStorage: () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const ids: string[] = JSON.parse(stored);
        set({ favorites: new Set(ids) });
      }
    } catch (error) {
      console.error('Failed to load favorites from storage:', error);
      set({ error: 'Не удалось загрузить избранное' });
    }
  },

  saveToStorage: () => {
    try {
      const ids = Array.from(get().favorites);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
    } catch (error) {
      console.error('Failed to save favorites to storage:', error);
      set({ error: 'Не удалось сохранить избранное' });
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));

// Автоматическая загрузка при создании store
useFavoritesStore.getState().loadFromStorage();
