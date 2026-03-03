import { useState } from 'react';
import { useListings, useManualScan } from '../api/listings';
import { useFilterStore } from '../store/filterStore';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';

export function Listings() {
  const { city, currency, page, setPage } = useFilterStore();
  const { data, isLoading } = useListings({ city, page: page, size: 20 });
  const { mutate: triggerScan, isPending } = useManualScan();

  const handleScan = () => {
    triggerScan({ city });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Объявления</h1>
        <Button onClick={handleScan} disabled={isPending}>
          <RefreshCw className={`w-4 h-4 mr-2 ${isPending ? 'animate-spin' : ''}`} />
          {isPending ? 'Сканирование...' : '🔄 Сканировать'}
        </Button>
      </div>

      <Card className="p-4">
        <div className="flex gap-4">
          <select
            value={city}
            onChange={(e) => useFilterStore.getState().setCity(e.target.value)}
            className="px-3 py-2 border rounded-md bg-background"
          >
            <option value="mogilev">Могилёв</option>
            <option value="minsk">Минск</option>
            <option value="grodno">Гродно</option>
            <option value="brest">Брест</option>
            <option value="gomel">Гомель</option>
            <option value="vitebsk">Витебск</option>
          </select>

          <select
            value={currency}
            onChange={(e) => useFilterStore.getState().setCurrency(e.target.value as 'BYN' | 'USD')}
            className="px-3 py-2 border rounded-md bg-background"
          >
            <option value="BYN">BYN</option>
            <option value="USD">USD</option>
          </select>
        </div>
      </Card>

      <Card>
        {isLoading ? (
          <div className="p-8 text-center">Загрузка...</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="p-3 text-left">Заголовок</th>
                <th className="p-3 text-left">Цена</th>
                <th className="p-3 text-left">Комн.</th>
                <th className="p-3 text-left">Площадь</th>
                <th className="p-3 text-left">Статус</th>
              </tr>
            </thead>
            <tbody>
              {data?.items?.map((listing) => (
                <tr key={listing.id} className="border-b hover:bg-accent/50">
                  <td className="p-3">
                    <Link to={`/listings/${listing.id}`} className="text-primary hover:underline">
                      {listing.title}
                    </Link>
                  </td>
                  <td className="p-3 font-medium">
                    {currency === 'USD' ? listing.price_usd : listing.price} {currency}
                  </td>
                  <td className="p-3">{listing.rooms}</td>
                  <td className="p-3">{listing.area} м²</td>
                  <td className="p-3">
                    <Badge variant="outline">{listing.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <div className="flex justify-center gap-2">
        <Button
          variant="outline"
          onClick={() => setPage(page - 1)}
          disabled={page <= 1}
        >
          ← Назад
        </Button>
        <span className="px-4 py-2">Страница {page}</span>
        <Button
          variant="outline"
          onClick={() => setPage(page + 1)}
          disabled={!data?.items?.length}
        >
          Вперёд →
        </Button>
      </div>
    </div>
  );
}
