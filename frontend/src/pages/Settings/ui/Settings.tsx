'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Switch } from '@/shared/ui/switch';
import { Slider } from '@/shared/ui/slider';
import { Badge } from '@/shared/ui/badge';
import { Skeleton } from '@/shared/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { useScanSchedule, useUpdateScanSchedule, useScanCities, useCurrentScanCity, useUpdateCurrentCity } from '@/api/listings';
import {
  Clock,
  MapPin,
  Bell,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Save,
} from 'lucide-react';
import { ChangeInterval } from '@/features/settings/change-interval';
import { ToggleAutoScan } from '@/features/settings/toggle-auto-scan';
import { ChangeCity } from '@/features/settings/change-city';
import { CITIES } from '@/shared/config';

export function Settings() {
  const { data: schedule, isLoading: isScheduleLoading } = useScanSchedule();
  const { data: cities } = useScanCities();
  const { data: currentCity } = useCurrentScanCity();
  const { mutate: updateSchedule } = useUpdateScanSchedule();
  const { mutate: updateCity } = useUpdateCurrentCity();

  const [interval, setInterval] = useState(schedule?.scan_interval_minutes || 30);
  const [enabled, setEnabled] = useState(schedule?.enabled ?? true);
  const [selectedCity, setSelectedCity] = useState(currentCity || 'mogilev');
  const [isSaving, setIsSaving] = useState(false);

  const handleSaveInterval = () => {
    setIsSaving(true);
    updateSchedule(
      { scan_interval_minutes: interval, enabled },
      {
        onSuccess: () => {
          setTimeout(() => setIsSaving(false), 1000);
        },
        onError: () => {
          setIsSaving(false);
        },
      }
    );
  };

  const handleSaveCity = (city: string) => {
    setSelectedCity(city);
    setIsSaving(true);
    updateCity(
      { city },
      {
        onSuccess: () => {
          setTimeout(() => setIsSaving(false), 1000);
        },
        onError: () => {
          setIsSaving(false);
        },
      }
    );
  };

  if (isScheduleLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Настройки
          </h1>
          <p className="text-muted-foreground mt-1">
            Управление параметрами сканирования
          </p>
        </div>
        {isSaving && (
          <Badge variant="secondary" className="animate-pulse">
            <CheckCircle className="w-3 h-3 mr-1" />
            Сохранение...
          </Badge>
        )}
      </div>

      {/* Scan Interval */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Интервал сканирования
          </CardTitle>
          <CardDescription>
            Как часто проверять новые объявления
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <ChangeInterval value={interval} onChange={setInterval} />
          <ToggleAutoScan enabled={enabled} onToggle={setEnabled} />
          <Button onClick={handleSaveInterval} className="w-full" disabled={isSaving}>
            {isSaving ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Сохранить изменения
          </Button>
        </CardContent>
      </Card>

      {/* City Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Город сканирования
          </CardTitle>
          <CardDescription>
            Выберите город для мониторинга
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ChangeCity value={selectedCity} onChange={handleSaveCity} />
          <div className="flex flex-wrap gap-2">
            {Object.entries(CITIES).map(([code, name]) => (
              <Badge
                key={code}
                variant={selectedCity === code ? 'default' : 'outline'}
                className="cursor-pointer transition-all"
                onClick={() => handleSaveCity(code)}
              >
                {name}
              </Badge>
            ))}
          </div>
          {currentCity && (
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              Текущий город: <strong>{CITIES[currentCity as keyof typeof CITIES]}</strong>
            </p>
          )}
        </CardContent>
      </Card>

      {/* Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Информация
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            • Автоматическое сканирование работает по установленному интервалу
          </p>
          <p>• Можно запустить ручное сканирование на странице объявлений</p>
          <p>• Изменения вступают в силу немедленно</p>
        </CardContent>
      </Card>
    </div>
  );
}
