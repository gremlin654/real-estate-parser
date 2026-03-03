import { Calendar, TrendingUp, Edit, Trash2, RotateCcw, FileText } from "lucide-react";
import type { HistoryEvent } from "@/api/listings";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface TimelineProps {
  events: HistoryEvent[];
  isLoading?: boolean;
}

export function HistoryTimeline({ events, isLoading }: TimelineProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div
          data-testid="loading-spinner"
          className="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"
        />
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
        <p className="font-medium">История пуста</p>
        <p className="text-sm mt-1">Изменений пока не было</p>
      </div>
    );
  }

  // Filter out 'restored' events - they look strange in the UI
  const filteredEvents = events.filter(event => event.event_type !== 'restored');

  if (filteredEvents.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
        <p className="font-medium">История пуста</p>
        <p className="text-sm mt-1">Изменений пока не было</p>
      </div>
    );
  }

  return (
    <div className="space-y-0 pt-5">
      {filteredEvents.map((event, index) => (
        <TimelineItem key={event.id} event={event} isLast={index === filteredEvents.length - 1} />
      ))}
    </div>
  );
}

interface TimelineItemProps {
  event: HistoryEvent;
  isLast: boolean;
}

function TimelineItem({ event, isLast }: TimelineItemProps) {
  const config = getEventConfig(event.event_type);

  return (
    <div className="flex gap-4">
      {/* Icon */}
      <div className="flex flex-col items-center pt-4">
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center shadow-md flex-shrink-0 ${config.bgColor} border-2 ${config.borderColor}`}
        >
          <config.icon className={`h-5 w-5 ${config.iconColor}`} />
        </div>
        {!isLast && <div className="w-0.5 flex-1 min-h-[60px] bg-border mt-2" />}
      </div>

      {/* Content */}
      <div className="flex-1 pb-6 pt-4">
        <Card className="border shadow-sm hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Badge variant={config.badgeVariant} className={`${config.badgeColor} text-white font-semibold text-xs`}>
                {config.label}
              </Badge>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(event.created_at)}
              </span>
            </div>

            {/* Price change */}
            {event.event_type === 'price_changed' && (
              <div className="flex items-center gap-4 mt-3 p-3 rounded-lg bg-muted/50">
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground mb-1">Было</p>
                  <p className="text-lg font-bold text-red-500 line-through">
                    {formatPrice(event.price_before)}
                  </p>
                </div>
                <div className="text-muted-foreground">→</div>
                <div className="flex-1 text-right">
                  <p className="text-xs text-muted-foreground mb-1">Стало</p>
                  <p className="text-lg font-bold text-green-500">
                    {formatPrice(event.price_after)}
                  </p>
                </div>
              </div>
            )}

            {/* Changed fields */}
            {event.changed_fields && Object.keys(event.changed_fields).length > 0 && (
              <div className="mt-3 space-y-2">
                <p className="text-xs font-semibold text-muted-foreground">Изменённые поля:</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(event.changed_fields).map(([field, values]) => {
                    if (Array.isArray(values) && values.length === 2) {
                      return (
                        <div
                          key={field}
                          className="text-xs px-2 py-1 rounded bg-primary/10 border border-primary/20"
                        >
                          <span className="font-medium">{translateField(field)}:</span>{" "}
                          <span className="text-red-500 line-through">{String(values[0])}</span>
                          {" → "}
                          <span className="text-green-500 font-medium">{String(values[1])}</span>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function getEventConfig(eventType: string) {
  switch (eventType) {
    case 'created':
      return {
        icon: FileText,
        label: 'Создано',
        bgColor: 'bg-blue-500',
        borderColor: 'border-blue-600',
        iconColor: 'text-white',
        badgeVariant: 'default' as const,
        badgeColor: 'bg-blue-500',
      };
    case 'price_changed':
      return {
        icon: TrendingUp,
        label: 'Изменение цены',
        bgColor: 'bg-yellow-500',
        borderColor: 'border-yellow-600',
        iconColor: 'text-white',
        badgeVariant: 'default' as const,
        badgeColor: 'bg-yellow-500',
      };
    case 'edited':
      return {
        icon: Edit,
        label: 'Редактировано',
        bgColor: 'bg-purple-500',
        borderColor: 'border-purple-600',
        iconColor: 'text-white',
        badgeVariant: 'default' as const,
        badgeColor: 'bg-purple-500',
      };
    case 'deleted':
      return {
        icon: Trash2,
        label: 'Удалено',
        bgColor: 'bg-red-500',
        borderColor: 'border-red-600',
        iconColor: 'text-white',
        badgeVariant: 'destructive' as const,
        badgeColor: 'bg-red-500',
      };
    case 'restored':
      return {
        icon: RotateCcw,
        label: 'Восстановлено',
        bgColor: 'bg-green-500',
        borderColor: 'border-green-600',
        iconColor: 'text-white',
        badgeVariant: 'secondary' as const,
        badgeColor: 'bg-green-500',
      };
    default:
      return {
        icon: FileText,
        label: eventType,
        bgColor: 'bg-gray-500',
        borderColor: 'border-gray-600',
        iconColor: 'text-white',
        badgeVariant: 'outline' as const,
        badgeColor: 'bg-gray-500',
      };
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatPrice(price?: number | null): string {
  if (!price) return '—';
  return `${price.toLocaleString()} BYN`;
}

function translateField(field: string): string {
  const translations: Record<string, string> = {
    title: 'Заголовок',
    price: 'Цена',
    address: 'Адрес',
    rooms: 'Комнаты',
    area: 'Площадь',
    floor: 'Этаж',
    total_floors: 'Этажность',
    description: 'Описание',
    district: 'Район',
    metro: 'Метро',
    house_year: 'Год постройки',
    category: 'Категория',
  };
  return translations[field] || field;
}
