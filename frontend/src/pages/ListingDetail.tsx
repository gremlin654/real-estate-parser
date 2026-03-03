import { useParams, useNavigate } from 'react-router-dom';
import { useListing, useListingHistory } from '../api/listings';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, ExternalLink } from 'lucide-react';

export function ListingDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: listing, isLoading } = useListing(id || '');
  const { data: history } = useListingHistory(id || '');

  if (isLoading) return <div className="p-8">Загрузка...</div>;
  if (!listing) return <div className="p-8">Объявление не найдено</div>;

  return (
    <div className="space-y-6">
      <Button variant="ghost" onClick={() => navigate(-1)}>
        <ArrowLeft className="w-4 h-4 mr-2" />
        Назад
      </Button>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-4">
          <h2 className="text-xl font-bold mb-4">Изображения</h2>
          {listing.images?.length ? (
            <img src={listing.images[0]} alt={listing.title} className="w-full rounded-lg" />
          ) : (
            <div className="text-center text-muted-foreground py-8">Нет изображений</div>
          )}
        </Card>

        <Card className="p-4">
          <h1 className="text-2xl font-bold mb-2">{listing.title}</h1>
          <p className="text-3xl font-bold text-primary mb-4">
            {listing.price_usd ? `${listing.price_usd} USD` : `${listing.price} BYN`}
          </p>
          <Badge className="mb-4">{listing.status}</Badge>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-muted-foreground">Комнат</p>
              <p className="font-medium">{listing.rooms}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Площадь</p>
              <p className="font-medium">{listing.area} м²</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Этаж</p>
              <p className="font-medium">{listing.floor}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Год постройки</p>
              <p className="font-medium">{listing.house_year || 'Н/Д'}</p>
            </div>
          </div>

          <Button className="w-full bg-green-600 hover:bg-green-700">
            <ExternalLink className="w-4 h-4 mr-2" />
            Открыть на Kufar
          </Button>
        </Card>
      </div>

      <Card className="p-4">
        <h3 className="text-lg font-semibold mb-2">Описание</h3>
        <p className="text-muted-foreground">{listing.description || 'Нет описания'}</p>
      </Card>

      {history && history.length > 0 && (
        <Card className="p-4">
          <h3 className="text-lg font-semibold mb-4">История изменений</h3>
          <div className="space-y-2">
            {history.map((event) => (
              <div key={event.id} className="flex items-center gap-3 p-2 border rounded">
                <span className="text-sm font-medium">{event.event_type}</span>
                {event.price_before && event.price_after && (
                  <span className="text-sm text-muted-foreground">
                    {event.price_before} → {event.price_after} USD
                  </span>
                )}
                <span className="text-xs text-muted-foreground ml-auto">
                  {new Date(event.created_at).toLocaleString('ru-RU')}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
