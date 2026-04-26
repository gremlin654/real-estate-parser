export interface TelegramWebApp {
  ready: () => void;
  expand: () => void;
  close: () => void;
  MainButton: {
    text: string;
    show: () => void;
    hide: () => void;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
    setText: (text: string) => void;
    enable: () => void;
    disable: () => void;
  };
  BackButton: {
    show: () => void;
    hide: () => void;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
  };
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
    notificationOccurred: (type: 'success' | 'warning' | 'error') => void;
    selectionChanged: () => void;
  };
  themeParams: {
    bg_color?: string;
    text_color?: string;
    button_color?: string;
    button_text_color?: string;
    hint_color?: string;
    link_color?: string;
    secondary_bg_color?: string;
  };
  viewportHeight: number;
  viewportStableHeight: number;
  colorScheme: 'light' | 'dark';
  initData: string;
  initDataUnsafe: {
    query_id?: string;
    user?: {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
      language_code?: string;
    };
    start_param?: string;
  };
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

export const isTelegramWebApp = (): boolean => {
  return typeof window !== 'undefined' && !!window.Telegram?.WebApp;
};

export const getTelegramWebApp = (): TelegramWebApp | null => {
  if (isTelegramWebApp()) {
    return window.Telegram!.WebApp;
  }
  return null;
};

export const initTelegramApp = (): TelegramWebApp | null => {
  const app = getTelegramWebApp();
  if (app) {
    app.ready();
    app.expand();
  }
  return app;
};

export const formatPrice = (
  value: number | null | undefined,
  currency: string
): string => {
  if (value === null || value === undefined) return 'Любая';
  const symbol = currency === 'usd' ? '$' : 'Br';
  return `${symbol}${value.toLocaleString()}`;
};

export const formatRooms = (rooms: number[] | null): string => {
  if (!rooms || rooms.length === 0) return 'Любые';
  if (rooms.length === 1) {
    if (rooms[0] === 1) return '1 комната';
    if (rooms[0] === 5) return '5+ комнат';
    return `${rooms[0]} комнаты`;
  }
  return rooms.join(', ');
};

export const CITY_NAMES: Record<string, string> = {
  minsk: 'Минск',
  mogilev: 'Могилёв',
  grodno: 'Гродно',
  brest: 'Брест',
  gomel: 'Гомель',
  vitebsk: 'Витебск',
};

export const ROOM_OPTIONS = [
  { value: 'any', label: 'Любые' },
  { value: '1', label: '1 комната' },
  { value: '2', label: '2 комнаты' },
  { value: '3', label: '3 комнаты' },
  { value: '4', label: '4 комнаты' },
  { value: '5', label: '5+ комнат' },
];

export const CURRENCIES = [
  { code: 'usd', name: 'USD', symbol: '$' },
  { code: 'byn', name: 'BYN', symbol: 'Br' },
];