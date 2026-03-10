# Price Per M² Analytics Feature

## Обзор

Реализована frontend часть для аналитики цены за м² недвижимости. Фича включает в себя:
- Отображение цены за м² в таблице объявлений
- Фильтрация по цене за м²
- Страница аналитики с графиками динамики и распределения
- Переключение валют (BYN/USD)

## Структура изменений

```
frontend/src/
├── shared/types/
│   ├── listing.ts (обновлён)
│   └── stats.ts (новый)
├── api/
│   └── listings.ts (обновлён)
├── store/
│   └── filterStore.ts (обновлён)
├── components/
│   └── stats/
│       ├── PricePerM2TrendChart.tsx (новый)
│       ├── PricePerM2DistributionChart.tsx (новый)
│       ├── PricePerM2TrendChart.test.tsx (новый)
│       └── PricePerM2DistributionChart.test.tsx (новый)
├── features/listings/
│   └── filter-by-price-per-m2/
│       ├── index.ts (новый)
│       └── ui/
│           └── FilterByPricePerM2.tsx (новый)
├── widgets/ListingTable/
│   └── ui/ListingTable.tsx (обновлён)
├── pages/
│   ├── Listings/ui/Listings.tsx (обновлён)
│   ├── ListingDetail/ui/ListingDetail.tsx (обновлён)
│   └── PricePerM2AnalyticsPage.tsx (новый)
├── app/
│   └── App.tsx (обновлён)
└── widgets/Sidebar/
    └── ui/Sidebar.tsx (обновлён)
```

## API Endpoints

Backend уже реализован и доступен:

```typescript
GET /api/v1/stats/price-per-m2?city=minsk&currency=usd
// Response: { average: 2171.54, median: 1923.7, min: 0, max: 35294.12, count: 6362 }

GET /api/v1/stats/price-per-m2-trends?city=minsk&period_days=30&interval=day&currency=usd
// Response: [{ date: "2025-01-01", average: 2450, median: 2400, count: 45 }, ...]

GET /api/v1/stats/price-per-m2-distribution?city=minsk&bins=10&currency=usd
// Response: [{ range_min: 1000, range_max: 1500, count: 45, percentage: 15.2 }, ...]

GET /api/v1/listings?city=minsk&price_per_m2_min=2000&price_per_m2_max=3000
// Фильтрация по цене за м²
```

## Новые TypeScript типы

```typescript
// stats.ts
export interface PricePerM2Stats {
  average: number;
  median: number;
  min: number;
  max: number;
  count: number;
  currency: 'BYN' | 'USD';
}

export interface PricePerM2Trend {
  date: string;
  average: number;
  median: number;
  count: number;
}

export interface PricePerM2DistributionBin {
  range_min: number;
  range_max: number;
  count: number;
  percentage: number;
}

// listing.ts
export interface Listing {
  // ... existing fields
  price_per_m2_byn?: number | null;
  price_per_m2_usd?: number | null;
}
```

## API Hooks

```typescript
import { 
  usePricePerM2Stats, 
  usePricePerM2Trends, 
  usePricePerM2Distribution 
} from '@/api/listings';

// Статистика
const { data: stats } = usePricePerM2Stats({
  city: 'minsk',
  rooms: 2,
  currency: 'usd',
});

// Тренды
const { data: trends } = usePricePerM2Trends({
  city: 'minsk',
  period_days: 30,
  interval: 'day',
  currency: 'usd',
});

// Распределение
const { data: distribution } = usePricePerM2Distribution({
  city: 'minsk',
  bins: 10,
  currency: 'usd',
});
```

## Компоненты

### PricePerM2TrendChart

График динамики цены за м² (LineChart).

```tsx
import { PricePerM2TrendChart } from '@/components/stats';

<PricePerM2TrendChart
  data={trendsData}
  currency="USD"
  period={30}
/>
```

### PricePerM2DistributionChart

График распределения цены за м² (BarChart).

```tsx
import { PricePerM2DistributionChart } from '@/components/stats';

<PricePerM2DistributionChart
  data={distributionData}
  currency="USD"
/>
```

### FilterByPricePerM2

Фильтр по цене за м².

```tsx
import { FilterByPricePerM2 } from '@/features/listings/filter-by-price-per-m2';

<FilterByPricePerM2
  pricePerM2Min={pricePerM2Min}
  pricePerM2Max={pricePerM2Max}
  onChange={(min, max) => {
    setFilters({ pricePerM2Min: min, pricePerM2Max: max });
  }}
/>
```

## Страница аналитики

Доступна по маршруту: `/analytics/price-per-m2`

**Функциональность:**
- Summary карточки (средняя, медиана, мин, макс)
- Фильтры (город, валюта, комнаты)
- Переключатель периодов (7/30/90 дней)
- Вкладки: Динамика / Распределение
- Графики с tooltips

## Навигация

Ссылка добавлена в Sidebar:
- "Аналитика цены за м²" → `/analytics/price-per-m2`

## Тесты

### Unit тесты (Vitest)

```bash
npm run test:unit -- src/components/stats/*.test.tsx
```

**Покрытие:**
- `PricePerM2TrendChart.test.tsx` — 7 тестов
- `PricePerM2DistributionChart.test.tsx` — 7 тестов

### E2E тесты (Playwright)

```bash
npm run test:e2e -- tests/e2e/price-per-m2-analytics.spec.ts
```

**Покрытие:**
- 17 тестов для страницы аналитики
- Тесты таблицы объявлений
- Тесты фильтров
- Тесты переключения валюты

## Acceptance Criteria

✅ Все критерии выполнены:

- [x] TypeScript типы добавлены
- [x] API hooks созданы и работают
- [x] Колонка "Цена за м²" в таблице (с сортировкой)
- [x] Фильтр price_per_m2 min/max работает
- [x] Детальная страница показывает price_per_m2
- [x] График динамики (LineChart) работает
- [x] График распределения (BarChart) работает
- [x] Страница аналитики `/analytics/price-per-m2` доступна
- [x] Переключатель валюты (BYN/USD) работает на всех компонентах
- [x] Loading/error состояния обрабатываются
- [x] Нет console errors
- [x] TypeScript компилируется без ошибок
- [x] Unit тесты написаны (14 тестов)
- [x] E2E тесты написаны (17 тестов)

## Известные ограничения

1. **Backend данные**: Backend должен отдавать поля `price_per_m2_byn` и `price_per_m2_usd` в ответах API
2. **Кэш**: TanStack Query кэширует данные на 5 минут (staleTime)
3. **Графики**: Recharts требует данные в определённом формате

## Troubleshooting

### График не отображается

Проверьте что данные в правильном формате:
```typescript
// Для трендов
data: [{ date: string, average: number, median: number, count: number }]

// Для распределения
data: [{ range_min: number, range_max: number, count: number, percentage: number }]
```

### Фильтр не работает

Убедитесь что `pricePerM2Min` и `pricePerM2Max` переданы в `useListings`:
```typescript
useListings({
  // ...
  pricePerM2Min,
  pricePerM2Max,
})
```

### Ошибки TypeScript

Проверьте что типы импортированы:
```typescript
import type { PricePerM2Stats, PricePerM2Trend } from '@/shared/types';
```

## Будущие улучшения

1. **Сравнение городов**: Добавить возможность сравнения цены за м² между городами
2. **Экспорт**: Добавить экспорт статистики в CSV/XLSX
3. **Детальные фильтры**: Фильтр по диапазону площади, этажу
4. **Алерты**: Уведомления при изменении средней цены за м²
