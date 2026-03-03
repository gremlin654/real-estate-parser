import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';

export function Settings() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Настройки</h1>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Город по умолчанию</h3>
        <p className="text-muted-foreground">Выберите город для сканирования</p>
        <div className="mt-4 flex gap-2">
          <Button variant="outline">Могилёв</Button>
          <Button variant="outline">Минск</Button>
          <Button variant="outline">Гродно</Button>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Интервал сканирования</h3>
        <p className="text-muted-foreground">Настройте частоту автоматического сканирования</p>
        <div className="mt-4">
          <input
            type="number"
            defaultValue={30}
            min={5}
            max={1440}
            className="px-3 py-2 border rounded-md bg-background w-32"
          />
          <span className="ml-2">минут</span>
        </div>
      </Card>
    </div>
  );
}
