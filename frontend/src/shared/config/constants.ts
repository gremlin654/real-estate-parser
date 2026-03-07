export const CITIES = {
  minsk: 'Минск',
  mogilev: 'Могилёв',
  grodno: 'Гродно',
  brest: 'Брест',
  gomel: 'Гомель',
  vitebsk: 'Витебск',
} as const;

export const CITY_CODES = Object.keys(CITIES) as Array<keyof typeof CITIES>;

export const STATUS_LABELS = {
  new: 'Новое',
  active: 'Активное',
  updated: 'Обновлено',
  price_changed_byn: 'Изменена цена (BYN)',
  deleted: 'Удалено',
  archived: 'Архив',
} as const;

export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

export const SCAN_HISTORY_PAGE_SIZE = 10;
