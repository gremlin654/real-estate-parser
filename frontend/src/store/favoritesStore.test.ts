import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useFavoritesStore } from './favoritesStore';

// Mock для localStorage
const mockLocalStorage = {
  data: {} as Record<string, string>,
  getItem: vi.fn((key: string) => mockLocalStorage.data[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    mockLocalStorage.data[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete mockLocalStorage.data[key];
  }),
  clear: vi.fn(() => {
    mockLocalStorage.data = {};
  }),
};

Object.defineProperty(global, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

// Mock для toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('favoritesStore', () => {
  beforeEach(() => {
    // Очистить localStorage
    mockLocalStorage.data = {};
    mockLocalStorage.setItem.mockClear();
    mockLocalStorage.getItem.mockClear();

    // Сбросить store через setState
    useFavoritesStore.setState({
      favorites: new Set<string>(),
      isLoading: false,
      error: null,
    });
  });

  describe('Инициализация', () => {
    it('должен начинать с пустым набором избранных', () => {
      // Сбрасываем store явно
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(0);
    });

    it('должен загружать избранные из localStorage при инициализации', () => {
      // Установить данные в localStorage
      mockLocalStorage.data['kufar-favorites'] = JSON.stringify(['uuid-1', 'uuid-2', 'uuid-3']);

      // Сбрасываем store
      useFavoritesStore.setState({ favorites: new Set<string>() });

      // Загружаем из localStorage
      const { loadFromStorage } = useFavoritesStore.getState();
      loadFromStorage();

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(3);
      expect(favorites.has('uuid-1')).toBe(true);
      expect(favorites.has('uuid-2')).toBe(true);
      expect(favorites.has('uuid-3')).toBe(true);
    });
  });

  describe('setFavorites', () => {
    it('должен устанавливать избранные из массива IDs', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { setFavorites } = useFavoritesStore.getState();
      setFavorites(['uuid-1', 'uuid-2', 'uuid-3']);

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(3);
      expect(favorites.has('uuid-1')).toBe(true);
      expect(favorites.has('uuid-2')).toBe(true);
      expect(favorites.has('uuid-3')).toBe(true);
    });

    it('должен заменять существующие избранные', () => {
      useFavoritesStore.setState({ favorites: new Set(['uuid-1', 'uuid-2']) });
      const { setFavorites } = useFavoritesStore.getState();
      setFavorites(['uuid-3', 'uuid-4', 'uuid-5']);

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(3);
      expect(favorites.has('uuid-1')).toBe(false);
      expect(favorites.has('uuid-3')).toBe(true);
      expect(favorites.has('uuid-4')).toBe(true);
      expect(favorites.has('uuid-5')).toBe(true);
    });
  });

  describe('addFavorite', () => {
    it('должен добавлять объявление в избранные', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { addFavorite } = useFavoritesStore.getState();
      addFavorite('uuid-1');

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(1);
      expect(favorites.has('uuid-1')).toBe(true);
    });

    it('должен добавлять несколько объявлений', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { addFavorite } = useFavoritesStore.getState();
      addFavorite('uuid-1');
      addFavorite('uuid-2');
      addFavorite('uuid-3');

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(3);
    });

    it('не должен дублировать объявления', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { addFavorite } = useFavoritesStore.getState();
      addFavorite('uuid-1');
      addFavorite('uuid-1');
      addFavorite('uuid-1');

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(1);
    });

    it('должен сохранять в localStorage', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { addFavorite } = useFavoritesStore.getState();
      addFavorite('uuid-1');

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'kufar-favorites',
        JSON.stringify(['uuid-1'])
      );
    });
  });

  describe('removeFavorite', () => {
    it('должен удалять объявление из избранных', () => {
      useFavoritesStore.setState({ favorites: new Set(['uuid-1', 'uuid-2']) });
      const { removeFavorite } = useFavoritesStore.getState();
      removeFavorite('uuid-1');

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(1);
      expect(favorites.has('uuid-1')).toBe(false);
      expect(favorites.has('uuid-2')).toBe(true);
    });

    it('не должен падать при удалении несуществующего', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { removeFavorite } = useFavoritesStore.getState();
      expect(() => removeFavorite('uuid-999')).not.toThrow();
      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(0);
    });

    it('должен сохранять в localStorage', () => {
      useFavoritesStore.setState({ favorites: new Set(['uuid-1', 'uuid-2']) });
      const { removeFavorite } = useFavoritesStore.getState();
      removeFavorite('uuid-1');

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'kufar-favorites',
        JSON.stringify(['uuid-2'])
      );
    });
  });

  describe('isFavorite', () => {
    it('должен возвращать true для избранного', () => {
      useFavoritesStore.setState({ favorites: new Set(['uuid-1']) });
      const { isFavorite } = useFavoritesStore.getState();

      expect(isFavorite('uuid-1')).toBe(true);
    });

    it('должен возвращать false для не избранного', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { isFavorite } = useFavoritesStore.getState();
      expect(isFavorite('uuid-1')).toBe(false);
    });

    it('должен возвращать false после удаления', () => {
      useFavoritesStore.setState({ favorites: new Set(['uuid-1']) });
      const { removeFavorite, isFavorite } = useFavoritesStore.getState();
      removeFavorite('uuid-1');

      expect(isFavorite('uuid-1')).toBe(false);
    });
  });

  describe('toggleFavorite', () => {
    const mockAddMutation = {
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    };
    
    const mockRemoveMutation = {
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    };

    beforeEach(() => {
      mockAddMutation.mutateAsync.mockClear();
      mockRemoveMutation.mutateAsync.mockClear();
    });

    it('должен добавлять в избранное если не избранное', async () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { toggleFavorite, isFavorite } = useFavoritesStore.getState();
      await toggleFavorite('uuid-1', mockAddMutation, mockRemoveMutation);

      expect(isFavorite('uuid-1')).toBe(true);
      expect(mockAddMutation.mutateAsync).toHaveBeenCalledWith('uuid-1');
    });

    it('должен удалять из избранного если избранное', async () => {
      useFavoritesStore.setState({ favorites: new Set(['uuid-1']) });
      const { toggleFavorite, isFavorite } = useFavoritesStore.getState();

      await toggleFavorite('uuid-1', mockAddMutation, mockRemoveMutation);

      expect(isFavorite('uuid-1')).toBe(false);
      expect(mockRemoveMutation.mutateAsync).toHaveBeenCalledWith('uuid-1');
    });

    it('должен делать rollback на ошибку', async () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { toggleFavorite, isFavorite } = useFavoritesStore.getState();

      mockAddMutation.mutateAsync.mockRejectedValue(new Error('API Error'));

      await toggleFavorite('uuid-1', mockAddMutation, mockRemoveMutation);

      // Должен быть rollback - объявление не должно быть в избранном
      expect(isFavorite('uuid-1')).toBe(false);
    });

    it('должен устанавливать isLoading во время операции', async () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { toggleFavorite } = useFavoritesStore.getState();
      let isLoadingDuringOperation = false;

      mockAddMutation.mutateAsync.mockImplementation(async () => {
        isLoadingDuringOperation = useFavoritesStore.getState().isLoading;
        return {};
      });

      await toggleFavorite('uuid-1', mockAddMutation, mockRemoveMutation);

      expect(isLoadingDuringOperation).toBe(true);
    });
  });

  describe('saveToStorage', () => {
    it('должен сохранять пустой набор', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { saveToStorage } = useFavoritesStore.getState();
      saveToStorage();

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'kufar-favorites',
        JSON.stringify([])
      );
    });

    it('должен сохранять заполненный набор', () => {
      useFavoritesStore.setState({ favorites: new Set(['uuid-1', 'uuid-2']) });
      const { saveToStorage } = useFavoritesStore.getState();
      saveToStorage();

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'kufar-favorites',
        JSON.stringify(['uuid-1', 'uuid-2'])
      );
    });
  });

  describe('loadFromStorage', () => {
    it('должен загружать из localStorage', () => {
      mockLocalStorage.data['kufar-favorites'] = JSON.stringify(['uuid-1', 'uuid-2', 'uuid-3']);
      useFavoritesStore.setState({ favorites: new Set<string>() });

      const { loadFromStorage } = useFavoritesStore.getState();
      loadFromStorage();

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(3);
      expect(favorites.has('uuid-1')).toBe(true);
      expect(favorites.has('uuid-2')).toBe(true);
      expect(favorites.has('uuid-3')).toBe(true);
    });

    it('должен обрабатывать ошибку при невалидном JSON', () => {
      mockLocalStorage.data['kufar-favorites'] = 'invalid json';
      useFavoritesStore.setState({ favorites: new Set<string>(), error: null });

      const { loadFromStorage } = useFavoritesStore.getState();
      loadFromStorage();

      // Ошибка должна быть установлена
      expect(useFavoritesStore.getState().error).toBe('Не удалось загрузить избранное');
    });

    it('должен обрабатывать отсутствие данных в localStorage', () => {
      useFavoritesStore.setState({ favorites: new Set<string>() });
      const { loadFromStorage } = useFavoritesStore.getState();
      loadFromStorage();

      const { favorites } = useFavoritesStore.getState();
      expect(favorites.size).toBe(0);
    });
  });

  describe('clearError', () => {
    it('должен очищать ошибку', () => {
      useFavoritesStore.setState({ error: 'Some error' });
      
      expect(useFavoritesStore.getState().error).toBe('Some error');
      
      const { clearError } = useFavoritesStore.getState();
      clearError();
      
      expect(useFavoritesStore.getState().error).toBe(null);
    });
  });
});
