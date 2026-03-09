'use client';

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useListing, useListingHistory } from '@/api/listings';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Button } from '@/shared/ui/button';
import { Badge } from '@/shared/ui/badge';
import { Skeleton } from '@/shared/ui/skeleton';
import { Separator } from '@/shared/ui/separator';
import { ScrollArea } from '@/shared/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog';
import {
  ArrowLeft,
  ExternalLink,
  Home,
  MapPin,
  DollarSign,
  Building,
  Maximize,
  Layers,
  Calendar,
  Image as ImageIcon,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  CheckCircle,
  TrendingUp,
  AlertCircle,
  Archive,
  Activity,
  FileText,
  Clock,
  Eye,
  Tag,
} from 'lucide-react';
import { formatDateTime } from '@/shared/lib/date-format';
import { CITIES, STATUS_LABELS } from '@/shared/config';
import { ListingInfo } from '@/entities/listing';
import { useFilterStore } from '@/store/filterStore';

export function ListingDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currency } = useFilterStore();
  const { data: listing, isLoading } = useListing(id || '');
  const { data: history } = useListingHistory(id || '');

  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [isGalleryOpen, setIsGalleryOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-32" />
        <div className="grid gap-6 md:grid-cols-2">
          <Skeleton className="h-96 rounded-xl" />
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!listing) {
    return (
      <Card className="p-12 text-center animate-scale-in">
        <div className="flex flex-col items-center gap-4">
          <div className="p-4 rounded-full bg-destructive/10">
            <AlertCircle className="w-12 h-12 text-destructive" />
          </div>
          <h2 className="text-2xl font-bold">Объявление не найдено</h2>
          <p className="text-muted-foreground">Возможно, оно было удалено</p>
          <Button onClick={() => navigate('/listings')} variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            К списку объявлений
          </Button>
        </div>
      </Card>
    );
  }

  const price = currency === 'USD' ? (listing.price_usd ?? listing.price) : listing.price;
  const displayCurrency = currency === 'USD' && listing.price_usd ? 'USD' : currency;
  const city = listing.city ? CITIES[listing.city as keyof typeof CITIES] : null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/listings')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Назад
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            {listing.title}
          </h1>
          <div className="flex items-center gap-2 text-muted-foreground mt-1">
            <MapPin className="w-4 h-4" />
            {listing.address}
            {city && <span>• {city}</span>}
          </div>
        </div>
        <Badge
          variant={
            listing.status === 'active'
              ? 'default'
              : listing.status === 'deleted'
              ? 'destructive'
              : 'secondary'
          }
        >
          {STATUS_LABELS[listing.status as keyof typeof STATUS_LABELS]}
        </Badge>
      </div>

      {/* Main Content */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Gallery */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="w-5 h-5" />
              Изображения
            </CardTitle>
          </CardHeader>
          <CardContent>
            {listing.images && listing.images.length > 0 ? (
              <div className="space-y-4">
                <div
                  className="relative aspect-video rounded-lg overflow-hidden cursor-pointer group"
                  onClick={() => setIsGalleryOpen(true)}
                >
                  <img
                    src={listing.images[selectedImageIndex]}
                    alt={listing.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                  />
                  <div className="absolute inset-0 bg-black/20 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                    <ZoomIn className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
                {listing.images.length > 1 && (
                  <div className="flex gap-2 overflow-x-auto">
                    {listing.images.map((img, idx) => (
                      <button
                        key={idx}
                        onClick={() => setSelectedImageIndex(idx)}
                        className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                          idx === selectedImageIndex
                            ? 'border-primary scale-105'
                            : 'border-muted hover:border-primary/50'
                        }`}
                      >
                        <img
                          src={img}
                          alt={`${idx + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="aspect-video rounded-lg bg-gradient-to-br from-muted to-muted/50 flex items-center justify-center">
                <ImageIcon className="w-12 h-12 text-muted-foreground" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Home className="w-5 h-5" />
              Информация
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-3xl font-bold text-primary">
              {price.toLocaleString()} {displayCurrency}
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <Building className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Комнат</p>
                  <p className="font-semibold">{listing.rooms ?? '-'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Maximize className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Площадь</p>
                  <p className="font-semibold">{listing.area ? `${listing.area.toFixed(1)} м²` : '-'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Этаж</p>
                  <p className="font-semibold">{listing.floor ?? '-'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Первое обнаружение</p>
                  <p className="font-semibold">
                    {formatDateTime(listing.first_seen_at)}
                  </p>
                </div>
              </div>
              {listing.total_floors && (
                <div className="flex items-center gap-2">
                  <Tag className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Этажность</p>
                    <p className="font-semibold">{listing.total_floors}</p>
                  </div>
                </div>
              )}
              {listing.house_year && (
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-xs text-muted-foreground">Год постройки</p>
                    <p className="font-semibold">{listing.house_year}</p>
                  </div>
                </div>
              )}
            </div>

            <Separator />

            <Button className="w-full" asChild>
              <a href={listing.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="w-4 h-4 mr-2" />
                Открыть на Kufar.by
              </a>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Description */}
      {listing.description && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Описание
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap leading-relaxed">
              {listing.description}
            </p>
          </CardContent>
        </Card>
      )}

      {/* History - показываем только важные события */}
      {history && history.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              История изменений ({history.filter(h => 
                ['created', 'deleted', 'price_changed', 'price_changed_byn'].includes(h.event_type)
              ).length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-4">
                {history
                  .filter(event => ['created', 'deleted', 'price_changed', 'price_changed_byn'].includes(event.event_type))
                  .map((event, idx) => {
                  const eventTypeConfig = {
                    created: { label: 'Создано', color: 'bg-green-500', icon: CheckCircle },
                    deleted: { label: 'Удалено', color: 'bg-red-500', icon: Archive },
                    price_changed: { label: 'Цена USD изменена', color: 'bg-yellow-500', icon: TrendingUp },
                    price_changed_byn: { label: 'Цена BYN изменена', color: 'bg-orange-500', icon: DollarSign },
                  };

                  const config = eventTypeConfig[event.event_type as keyof typeof eventTypeConfig] || {
                    label: event.event_type, 
                    color: 'bg-gray-500',
                    icon: Activity 
                  };
                  const IconComponent = config.icon;

                  return (
                    <div key={event.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
                      <div className={`w-3 h-3 rounded-full mt-1.5 ${config.color}`} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <IconComponent className="w-4 h-4 text-muted-foreground" />
                          <p className="font-medium">{config.label}</p>
                        </div>
                        {event.price_before && event.price_after && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {(currency === 'USD' 
                              ? (event.price_before_usd ?? event.price_before / 100) 
                              : (event.price_before / 100)
                            ).toLocaleString()}{' '}
                            →{' '}
                            {(currency === 'USD' 
                              ? (event.price_after_usd ?? event.price_after / 100) 
                              : (event.price_after / 100)
                            ).toLocaleString()} {displayCurrency}
                          </p>
                        )}
                        {event.changed_fields && Object.keys(event.changed_fields).length > 0 && (
                          <div className="mt-2 text-xs text-muted-foreground">
                            {Object.entries(event.changed_fields)
                              .filter(([field]) => field !== 'raw_data') // Исключаем raw_data из отображения
                              .map(([field, values]) => {
                              // Helper to safely convert value to string
                              const formatValue = (val: any) => {
                                if (val === null || val === undefined) return '—';
                                if (typeof val === 'object') {
                                  try {
                                    return JSON.stringify(val).slice(0, 100) + (JSON.stringify(val).length > 100 ? '...' : '');
                                  } catch {
                                    return '[Object]';
                                  }
                                }
                                return String(val);
                              };

                              return (
                                <div key={field} className="flex items-center gap-1 mb-1">
                                  <Eye className="w-3 h-3" />
                                  <span className="font-medium">{field}:</span>
                                  <span className="line-through opacity-50">{formatValue(values[0])}</span>
                                  <span>→</span>
                                  <span className="font-medium">{formatValue(values[1])}</span>
                                </div>
                              );
                            })}
                          </div>
                        )}
                        <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDateTime(event.created_at)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">История изменений пуста</p>
          </CardContent>
        </Card>
      )}

      {/* Gallery Dialog */}
      <Dialog open={isGalleryOpen} onOpenChange={setIsGalleryOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Изображения</DialogTitle>
          </DialogHeader>
          <div className="relative aspect-video">
            <img
              src={listing.images?.[selectedImageIndex] || ''}
              alt={listing.title}
              className="w-full h-full object-contain"
            />
            {listing.images && listing.images.length > 1 && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute left-2 top-1/2 -translate-y-1/2"
                  onClick={() =>
                    setSelectedImageIndex(
                      (prev) => (prev - 1 + (listing.images?.length || 0)) % (listing.images?.length || 0)
                    )
                  }
                >
                  <ChevronLeft className="w-6 h-6" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-1/2 -translate-y-1/2"
                  onClick={() =>
                    setSelectedImageIndex(
                      (prev) => (prev + 1) % (listing.images?.length || 1)
                    )
                  }
                >
                  <ChevronRight className="w-6 h-6" />
                </Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
