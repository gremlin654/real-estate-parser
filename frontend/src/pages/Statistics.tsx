import { Card } from '../components/ui/card';

export default function Statistics() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Статистика</h1>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Динамика цен</h3>
        <p className="text-muted-foreground">График изменения цен по месяцам</p>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Распределение по комнатам</h3>
        <p className="text-muted-foreground">Количество объявлений по количеству комнат</p>
      </Card>
    </div>
  );
}
