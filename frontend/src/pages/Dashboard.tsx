import { Link } from 'react-router-dom';
import { useFilterStore } from '../store/filterStore';
import { useSummary } from '../api/listings';
import { Card } from '../components/ui/card';
import { TrendingUp, TrendingDown, DollarSign, CheckCircle } from 'lucide-react';

export function Dashboard() {
  const { city } = useFilterStore();
  const { data: summary, isLoading } = useSummary(city);

  const stats = [
    {
      title: 'Новых сегодня',
      value: summary?.new_today ?? 0,
      icon: TrendingUp,
      color: 'text-green-500',
    },
    {
      title: 'Удалено сегодня',
      value: summary?.deleted_today ?? 0,
      icon: TrendingDown,
      color: 'text-red-500',
    },
    {
      title: 'Изменилась цена',
      value: summary?.price_changed_usd_today ?? 0,
      icon: DollarSign,
      color: 'text-yellow-500',
    },
    {
      title: 'Активных всего',
      value: summary?.active_total ?? 0,
      icon: CheckCircle,
      color: 'text-blue-500',
    },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Панель управления</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.title}</p>
                  <p className="text-2xl font-bold">{isLoading ? '...' : stat.value}</p>
                </div>
                <Icon className={`w-8 h-8 ${stat.color}`} />
              </div>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-2">Быстрые ссылки</h3>
          <div className="space-y-2">
            <Link to="/listings" className="text-primary hover:underline">
              → Просмотреть объявления
            </Link>
            <Link to="/statistics" className="text-primary hover:underline">
              → Статистика по городам
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
