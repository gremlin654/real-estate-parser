'use client';

import { Input } from '@/shared/ui/input';
import { Button } from '@/shared/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select';
import { useState, useEffect } from 'react';
import type { FavoritesFilters } from '@/shared/types';
import { Badge } from '@/shared/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip';
import { cn } from '@/lib/utils';
import { MapPin, RotateCcw, ArrowUpDown, DollarSign } from 'lucide-react';

interface FavoritesFilterProps {
  filters: FavoritesFilters;
  onChange: (filters: FavoritesFilters) => void;
  onReset: () => void;
}

const CITIES = [
  { value: 'minsk', label: 'Минск' },
  { value: 'mogilev', label: 'Могилёв' },
  { value: 'grodno', label: 'Гродно' },
  { value: 'brest', label: 'Брест' },
  { value: 'gomel', label: 'Гомель' },
  { value: 'vitebsk', label: 'Витебск' },
];

const SORT_OPTIONS = [
  { value: 'created_at_desc', label: 'Дата добавления (новые)', icon: '🆕' },
  { value: 'created_at_asc', label: 'Дата добавления (старые)', icon: '📅' },
  { value: 'price_asc', label: 'Цена (возрастание)', icon: '💰' },
  { value: 'price_desc', label: 'Цена (убывание)', icon: '💎' },
  { value: 'newest', label: 'Дата обновления (новые)', icon: '🔄' },
  { value: 'oldest', label: 'Дата обновления (старые)', icon: '⏳' },
];

export function FavoritesFilter({ filters, onChange, onReset }: FavoritesFilterProps) {
  const [localPriceFrom, setLocalPriceFrom] = useState(filters.priceFrom?.toString() || '');
  const [localPriceTo, setLocalPriceTo] = useState(filters.priceTo?.toString() || '');

  // Синхронизация локального state с props
  useEffect(() => {
    setLocalPriceFrom(filters.priceFrom?.toString() || '');
  }, [filters.priceFrom]);

  useEffect(() => {
    setLocalPriceTo(filters.priceTo?.toString() || '');
  }, [filters.priceTo]);

  const handleApplyPrice = () => {
    onChange({
      ...filters,
      priceFrom: localPriceFrom ? parseInt(localPriceFrom, 10) : null,
      priceTo: localPriceTo ? parseInt(localPriceTo, 10) : null,
    });
  };

  const handleClearPrice = () => {
    setLocalPriceFrom('');
    setLocalPriceTo('');
    onChange({
      ...filters,
      priceFrom: null,
      priceTo: null,
    });
  };

  const handleCityChange = (value: string) => {
    onChange({
      ...filters,
      city: value === 'all' ? undefined : value,
    });
  };

  const handleRoomChange = (room: number, checked: boolean) => {
    const currentRooms = filters.rooms || [];
    const newRooms = checked
      ? [...currentRooms, room]
      : currentRooms.filter((r) => r !== room);

    onChange({
      ...filters,
      rooms: newRooms.length > 0 ? newRooms : undefined,
    });
  };

  const handleRoomOtherChange = (checked: boolean) => {
    onChange({
      ...filters,
      roomsOther: checked || undefined,
    });
  };

  const handleSortChange = (value: string) => {
    onChange({
      ...filters,
      sort: value as FavoritesFilters['sort'],
    });
  };

  const hasActiveFilters = filters.city || filters.priceFrom || filters.priceTo || filters.rooms?.length || filters.roomsOther || filters.sort;

  return (
    <TooltipProvider>
      <div className="flex flex-col gap-4 p-4 bg-card rounded-xl border shadow-sm">
        {/* Верхняя строка: Город, Цена, Сортировка */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Город */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              Город
            </label>
            <Select
              value={filters.city || 'all'}
              onValueChange={handleCityChange}
            >
              <SelectTrigger 
                className="w-[160px] h-9 shadow-sm transition-colors hover:border-primary/50" 
                data-testid="city-select"
              >
                <SelectValue placeholder="Все города" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все города</SelectItem>
                {CITIES.map((city) => (
                  <SelectItem key={city.value} value={city.value}>
                    {city.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Цена */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              Цена, $
            </label>
            <div className="flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Input
                    type="number"
                    placeholder="От"
                    className="w-[90px] h-9 shadow-sm transition-colors hover:border-primary/50 focus:border-primary"
                    value={localPriceFrom}
                    onChange={(e) => setLocalPriceFrom(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleApplyPrice()}
                    data-testid="price-min-input"
                  />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Минимальная цена в USD</p>
                </TooltipContent>
              </Tooltip>
              
              <span className="text-muted-foreground">—</span>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Input
                    type="number"
                    placeholder="До"
                    className="w-[90px] h-9 shadow-sm transition-colors hover:border-primary/50 focus:border-primary"
                    value={localPriceTo}
                    onChange={(e) => setLocalPriceTo(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleApplyPrice()}
                    data-testid="price-max-input"
                  />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Максимальная цена в USD</p>
                </TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    size="sm" 
                    onClick={handleApplyPrice} 
                    data-testid="price-apply-button"
                    className="h-9 px-3 transition-all hover:shadow-md"
                  >
                    Применить
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Применить фильтр по цене (Enter)</p>
                </TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleClearPrice}
                    data-testid="price-clear-button"
                    className="h-9 px-3 transition-colors hover:text-destructive hover:bg-destructive/10"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Сбросить фильтр цены</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>

          {/* Сортировка */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1">
              <ArrowUpDown className="h-3 w-3" />
              Сортировка
            </label>
            <Select
              value={filters.sort || 'created_at_desc'}
              onValueChange={handleSortChange}
            >
              <SelectTrigger 
                className="w-[200px] h-9 shadow-sm transition-colors hover:border-primary/50" 
                data-testid="sort-select"
              >
                <SelectValue placeholder="Сортировка" />
              </SelectTrigger>
              <SelectContent>
                {SORT_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <span className="flex items-center gap-2">
                      <span>{option.icon}</span>
                      <span>{option.label}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Сбросить все фильтры */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-transparent">.</label>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={onReset}
                  className={cn(
                    "h-9 px-4 transition-all hover:shadow-md",
                    !hasActiveFilters && "opacity-50 hover:opacity-80"
                  )}
                  data-testid="reset-filters-button"
                  disabled={!hasActiveFilters}
                >
                  <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
                  Сбросить все
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Сбросить все активные фильтры</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Разделитель */}
        <div className="h-px bg-border" />

        {/* Комнаты */}
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs font-medium text-muted-foreground">Комнаты:</label>
          <div className="flex flex-wrap items-center gap-2">
            {[1, 2, 3, 4].map((room) => {
              const isSelected = filters.rooms?.includes(room) || false;
              return (
                <Tooltip key={room}>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={() => handleRoomChange(room, !isSelected)}
                      className={cn(
                        "min-w-[36px] h-9 px-3 rounded-md border text-sm font-medium transition-all duration-200",
                        "flex items-center justify-center",
                        isSelected
                          ? "bg-primary border-primary text-primary-foreground shadow-sm hover:bg-primary/90"
                          : "bg-background border-input text-foreground hover:border-primary/50 hover:bg-accent/50"
                      )}
                      data-testid={`room-${room}-button`}
                      aria-pressed={isSelected}
                    >
                      {room}
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{isSelected ? 'Убрать' : 'Выбрать'} {room} {room === 1 ? 'комнату' : 'комнаты'}</p>
                  </TooltipContent>
                </Tooltip>
              );
            })}
            
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={() => handleRoomOtherChange(!filters.roomsOther)}
                  className={cn(
                    "min-w-[48px] h-9 px-3 rounded-md border text-sm font-medium transition-all duration-200",
                    "flex items-center justify-center",
                    filters.roomsOther
                      ? "bg-primary border-primary text-primary-foreground shadow-sm hover:bg-primary/90"
                      : "bg-background border-input text-foreground hover:border-primary/50 hover:bg-accent/50"
                  )}
                  data-testid="room-5-plus-button"
                  aria-pressed={filters.roomsOther}
                >
                  5+
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{filters.roomsOther ? 'Убрать' : 'Выбрать'} 5+ комнат</p>
              </TooltipContent>
            </Tooltip>
          </div>
          
          {/* Индикатор выбранных комнат */}
          {(filters.rooms?.length || filters.roomsOther) && (
            <Badge variant="secondary" className="ml-2 animate-in fade-in zoom-in duration-200">
              Выбрано: {filters.rooms?.length || 0}{filters.roomsOther ? '+' : ''}
            </Badge>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}
