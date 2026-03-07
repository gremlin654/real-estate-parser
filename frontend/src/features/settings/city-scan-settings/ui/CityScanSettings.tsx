'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Switch } from '@/shared/ui/switch';
import { Slider } from '@/shared/ui/slider';
import { Badge } from '@/shared/ui/badge';
import {
  MapPin,
  Save,
  RefreshCw,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { useCityScanSettings, useUpdateCityScanSettings } from '@/api/listings';
import type { CitySettingsUpdateRequest } from '@/shared/types';

interface CityScanSettingsProps {
  city: string;
  cityName: string;
}

export function CityScanSettings({ city, cityName }: CityScanSettingsProps) {
  const { data: settings, isLoading, error } = useCityScanSettings(city);
  const { mutate: updateSettings, isPending } = useUpdateCityScanSettings();

  // Local state для управления изменениями
  const [enabled, setEnabled] = useState(false);
  const [interval, setInterval] = useState(30);
  const [isDirty, setIsDirty] = useState(false);

  // Инициализация локального состояния при загрузке данных
  useEffect(() => {
    if (settings) {
      setEnabled(settings.enabled);
      setInterval(settings.scan_interval_minutes);
      setIsDirty(false);
    }
  }, [settings]);

  // Обработчик переключения enabled
  const handleToggle = (checked: boolean) => {
    setEnabled(checked);
    setIsDirty(true);
  };

  // Обработчик изменения интервала
  const handleIntervalChange = (values: number[]) => {
    setInterval(values[0]);
    setIsDirty(true);
  };

  // Обработчик сохранения
  const handleSave = () => {
    const updateData: CitySettingsUpdateRequest = {
      enabled,
      scan_interval_minutes: interval,
    };

    updateSettings({ city, data: updateData });
    setIsDirty(false);
  };

  // Loading state
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            {cityName}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="h-4 w-32 bg-muted animate-pulse rounded" />
              <div className="h-3 w-20 bg-muted animate-pulse rounded" />
            </div>
            <div className="h-6 w-12 bg-muted animate-pulse rounded" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <div className="h-4 w-28 bg-muted animate-pulse rounded" />
              <div className="h-4 w-16 bg-muted animate-pulse rounded" />
            </div>
            <div className="h-6 w-full bg-muted animate-pulse rounded" />
          </div>
          <div className="h-10 w-full bg-muted animate-pulse rounded" />
          <div className="h-6 w-48 bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            {cityName}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">Ошибка загрузки настроек</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="w-5 h-5" />
          {cityName}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Switch "Автоматическое сканирование" */}
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Автоматическое сканирование</div>
            <div className="text-xs text-muted-foreground">
              {enabled ? 'Включено' : 'Выключено'}
            </div>
          </div>
          <Switch checked={enabled} onCheckedChange={handleToggle} />
        </div>

        {/* Slider интервала */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm">Интервал сканирования</span>
            <span className="text-sm text-muted-foreground">{interval} мин</span>
          </div>
          <Slider
            value={[interval]}
            onValueChange={handleIntervalChange}
            min={5}
            max={1440}
            step={5}
            disabled={!enabled}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>5 мин</span>
            <span>24 часа</span>
          </div>
        </div>

        {/* Кнопка "Сохранить" */}
        <Button onClick={handleSave} disabled={isPending || !isDirty} className="w-full">
          {isPending ? (
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Сохранить изменения
        </Button>

        {/* Badge статуса */}
        <Badge variant={enabled ? 'default' : 'secondary'} className={enabled ? 'bg-green-600' : ''}>
          {enabled ? (
            <>
              <CheckCircle className="w-3 h-3 mr-1" />
              Автосканирование включено
            </>
          ) : (
            <>
              <AlertCircle className="w-3 h-3 mr-1" />
              Автосканирование отключено
            </>
          )}
        </Badge>
      </CardContent>
    </Card>
  );
}
