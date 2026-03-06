# WebSocket API — Прогресс сканирования

## Обзор

Начиная с версии 2.1, Kufar Monitor использует WebSocket для real-time обновления прогресса сканирования вместо polling. Это уменьшает нагрузку на сервер и обеспечивает мгновенные обновления.

## Endpoint

```
ws://localhost:8000/ws/scan/progress
```

Для HTTPS:
```
wss://your-domain.com/ws/scan/progress
```

## Подключение

### JavaScript (Frontend)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scan/progress');

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  console.log('Progress update:', progress);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
  // Автоматическое переподключение через 3 секунды
  setTimeout(() => {
    // Reconnect logic
  }, 3000);
};
```

### React Hook

Используйте готовый хук `useScanProgressWebSocket`:

```typescript
import { useScanProgressWebSocket } from '@/api/listings';

function MyComponent() {
  const { progress, isConnected } = useScanProgressWebSocket();
  
  return (
    <div>
      {progress.is_scanning && (
        <div>
          <p>Стадия: {progress.stage}</p>
          <p>Страниц: {progress.pages_scraped}</p>
          <p>Объявлений: {progress.listings_fetched}</p>
        </div>
      )}
    </div>
  );
}
```

### Python (Тестирование)

```python
import asyncio
import websockets

async def test():
    async with websockets.connect("ws://localhost:8000/ws/scan/progress") as ws:
        message = await ws.recv()
        progress = json.loads(message)
        print(progress)

asyncio.run(test())
```

## Формат данных

### Progress Object

```json
{
  "is_scanning": true,
  "city": "minsk",
  "city_name": "Минск",
  "stage": "fetching",
  "pages_scraped": 15,
  "listings_fetched": 450,
  "listings_processed": 0,
  "elapsed_seconds": 25,
  "is_stable": false
}
```

### Поля

| Поле | Тип | Описание |
|------|-----|----------|
| `is_scanning` | boolean | true если сканирование активно |
| `city` | string\|null | Код города (minsk, mogilev, etc.) |
| `city_name` | string\|null | Название города на русском |
| `stage` | string | Текущая стадия сканирования |
| `pages_scraped` | number | Количество спарсенных страниц |
| `listings_fetched` | number | Количество найденных объявлений |
| `listings_processed` | number | Количество обработанных объявлений |
| `elapsed_seconds` | number | Время выполнения в секундах |
| `is_stable` | boolean | true если данные стабильны (не меняются) |

### Стадии сканирования

| Стадия | Описание |
|--------|----------|
| `starting` | Запуск сканирования |
| `marking_deleted` | Подготовка базы данных |
| `fetching` | Загрузка данных с Kufar |
| `parsing` | Обработка данных |
| `upserting` | Сохранение в базу данных |
| `marking_deleted_final` | Финализация (обновление статусов) |
| `done` | Сканирование завершено успешно |
| `error` | Произошла ошибка |

## Автоматическое обновление

WebSocket автоматически отправляет обновления при:

- Изменении стадии сканирования
- Загрузке каждой новой страницы
- Обновлении количества обработанных объявлений
- Завершении сканирования
- Возникновении ошибки

## Переподключение

При разрыве соединения клиент автоматически пытается переподключиться через 3 секунды.

## Совместимость

- **Frontend**: React 19+, браузеры с поддержкой WebSocket
- **Backend**: FastAPI 0.109.2+
- **Тестирование**: Python 3.10+, библиотека `websockets`

## Отличия от polling

| Характеристика | Polling | WebSocket |
|----------------|---------|-----------|
| Запросы к серверу | Каждые 2 секунды | Одно подключение |
| Задержка обновления | До 2 секунд | Мгновенно |
| Нагрузка на сервер | Высокая | Низкая |
| Трафик | Избыточный | Минимальный |
| Сложность | Простая | Средняя |

## Migration Guide

### Обновление frontend

**До:**
```typescript
import { useScanProgress } from '@/api/listings';

function Component() {
  const { data: progress } = useScanProgress();
}
```

**После:**
```typescript
import { useScanProgressWebSocket } from '@/api/listings';

function Component() {
  const { progress, isConnected } = useScanProgressWebSocket();
}
```

### Обновление backend

Backend автоматически отправляет обновления через WebSocket при сканировании. Никаких изменений в API endpoints не требуется.

## Тестирование

### Проверка подключения

```bash
# Запустить тестовый скрипт
python test_ws.py
```

### Через браузер

Откройте консоль разработчика и выполните:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scan/progress');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## Troubleshooting

### WebSocket не подключается

1. Убедитесь, что backend запущен
2. Проверьте логи backend на наличие ошибок
3. Проверьте firewall и сетевые настройки

### Нет обновлений прогресса

1. Убедитесь, что сканирование запущено
2. Проверьте `_broadcast_progress()` вызовы в scheduler
3. Проверьте консоль браузера на ошибки

### Частые переподключения

1. Проверьте стабильность сетевого соединения
2. Увеличьте timeout в настройках WebSocket
3. Проверьте load balancer настройки (если используется)
