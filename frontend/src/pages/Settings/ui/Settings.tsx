'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Bell } from 'lucide-react';
import { useAllScanSettings } from '@/api/listings';
import { CityScanSettings } from '@/features/settings/city-scan-settings';
import { CITIES } from '@/shared/config';

export function Settings() {
  const { data: allSettings, isLoading } = useAllScanSettings();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Настройки автосканирования
          </h1>
          <p className="text-muted-foreground mt-1">
            Управление параметрами сканирования для каждого города
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Object.entries(CITIES).map(([code]) => (
            <Card key={code}>
              <CardHeader>
                <div className="h-6 w-32 bg-muted animate-pulse rounded" />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="h-10 w-full bg-muted animate-pulse rounded" />
                <div className="h-10 w-full bg-muted animate-pulse rounded" />
                <div className="h-10 w-full bg-muted animate-pulse rounded" />
                <div className="h-6 w-48 bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          Настройки автосканирования
        </h1>
        <p className="text-muted-foreground mt-1">
          Управление параметрами сканирования для каждого города
        </p>
      </div>

      {/* Список городов */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(CITIES).map(([code, name]) => (
          <CityScanSettings key={code} city={code} cityName={name} />
        ))}
      </div>

      {/* Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Информация
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>• Автоматическое сканирование работает только для включённых городов</p>
          <p>• Интервал сканирования настраивается отдельно для каждого города</p>
          <p>• Изменения вступают в силу немедленно</p>
        </CardContent>
      </Card>
    </div>
  );
}
