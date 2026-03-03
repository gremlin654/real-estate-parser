# Scan History Tracking

## Обзор

Функционал отслеживания истории запусков сканера позволяет сохранять информацию о каждом запуске сканирования (как ручном, так и по расписанию), включая:

- Время начала и окончания
- Город сканирования
- Тип запуска (ручной/по расписанию)
- Количество обработанных объявлений
- Статус выполнения (успех/ошибка)
- Ошибки если они произошли
- Продолжительность сканирования

## Компоненты

### Модель данных

**Таблица:** `scan_history`

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | UUID | Первичный ключ |
| `started_at` | DateTime | Время начала сканирования |
| `completed_at` | DateTime | Время завершения (NULL если ещё сканирует) |
| `city` | String | Код города (minsk, mogilev, etc.) |
| `city_name` | String | Название города на русском |
| `status` | String | Статус: running, completed, error |
| `trigger_type` | String | Тип запуска: manual, scheduled |
| `listings_fetched` | Integer | Количество найденных объявлений |
| `listings_created` | Integer | Количество созданных записей |
| `listings_updated` | Integer | Количество обновленных записей |
| `listings_deleted` | Integer | Количество помеченных как удаленные |
| `pages_scraped` | Integer | Количество спарсенных страниц |
| `errors` | JSONB | Массив сообщений об ошибках |
| `duration_seconds` | Integer | Продолжительность в секундах |
| `error_message` | Text | Сообщение об ошибке если status=error |

### Сервис

**Файл:** `backend/app/services/scan_history_service.py`

Основные методы:

```python
# Создание записи о начале сканирования
await service.create_scan_record(
    city="minsk",
    city_name="Минск",
    trigger_type="manual"  # или "scheduled"
)

# Обновление статистики во время сканирования
await service.update_scan_record(
    scan_id=uuid,
    listings_fetched=100,
    listings_created=10,
    listings_updated=80,
    listings_deleted=5,
    pages_scraped=4,
    errors=["error message"]
)

# Завершение сканирования
await service.complete_scan_record(
    scan_id=uuid,
    status="completed",  # или "error"
    error_message="Optional error message"
)

# Получение истории
scans = await service.get_scan_history(
    limit=50,
    offset=0,
    city="minsk",      # опционально
    status="completed" # опционально
)

# Получение одной записи
scan = await service.get_scan_record_by_id(uuid)

# Получение сводной статистики
summary = await service.get_summary(city="minsk")
# Returns:
# {
#     "total_scans": 10,
#     "completed_scans": 8,
#     "failed_scans": 1,
#     "running_scans": 1,
#     "total_listings_fetched": 1000,
#     "total_listings_created": 100,
#     "total_listings_updated": 800,
#     "total_listings_deleted": 50,
#     "avg_duration_seconds": 45
# }
```

### API Endpoints

#### GET /api/v1/scan/history

Получить историю сканирований с пагинацией и фильтрацией.

**Параметры:**
- `limit` (int, default: 50, max: 200) - количество записей
- `offset` (int, default: 0) - смещение
- `city` (string, optional) - фильтр по городу
- `status` (string, optional) - фильтр по статусу

**Ответ:**
```json
{
  "items": [
    {
      "id": "uuid-string",
      "started_at": "2026-03-01T19:00:00",
      "completed_at": "2026-03-01T19:01:00",
      "city": "minsk",
      "city_name": "Минск",
      "status": "completed",
      "trigger_type": "manual",
      "listings_fetched": 540,
      "listings_created": 15,
      "listings_updated": 520,
      "listings_deleted": 5,
      "pages_scraped": 18,
      "duration_seconds": 53,
      "error_message": null
    }
  ],
  "total": 150
}
```

#### GET /api/v1/scan/history/{scan_id}

Получить детальную информацию о конкретном сканировании.

**Ответ:** Объект ScanHistory

#### GET /api/v1/scan/history/summary

Получить сводную статистику по всем сканированиям.

**Параметры:**
- `city` (string, optional) - фильтр по городу

**Ответ:**
```json
{
  "total_scans": 150,
  "completed_scans": 145,
  "failed_scans": 3,
  "running_scans": 2,
  "total_listings_fetched": 75000,
  "total_listings_created": 1500,
  "total_listings_updated": 72000,
  "total_listings_deleted": 1500,
  "avg_duration_seconds": 52
}
```

## Интеграция со сканером

### Scheduler

**Файл:** `backend/app/scraper/scheduler.py`

Scheduler автоматически создает и обновляет записи истории сканирований:

1. **Перед началом сканирования:**
   ```python
   scan_record = await history_service.create_scan_record(
       city=scan_city,
       city_name=city_name,
       trigger_type=trigger_type,  # "manual" или "scheduled"
   )
   self._current_scan_id = scan_record.id
   ```

2. **После успешного завершения:**
   ```python
   await history_service.update_scan_record(
       scan_id=self._current_scan_id,
       listings_fetched=stats["listings_fetched"],
       listings_created=stats["listings_created"],
       listings_updated=stats["listings_updated"],
       listings_deleted=stats["listings_deleted"],
       pages_scraped=self.scan_progress["pages_scraped"],
       errors=stats["errors"],
   )
   await history_service.complete_scan_record(
       scan_id=self._current_scan_id,
       status="completed",
   )
   ```

3. **При ошибке:**
   ```python
   await history_service.update_scan_record(
       scan_id=self._current_scan_id,
       listings_fetched=stats["listings_fetched"],
       errors=stats["errors"],
   )
   await history_service.complete_scan_record(
       scan_id=self._current_scan_id,
       status="error",
       error_message=str(e),
   )
   ```

## Примеры использования

### Получить последние 10 сканирований

```bash
curl http://localhost:8000/api/v1/scan/history?limit=10
```

### Получить сканирования для Минска

```bash
curl http://localhost:8000/api/v1/scan/history?city=minsk
```

### Получить только успешные сканирования

```bash
curl http://localhost:8000/api/v1/scan/history?status=completed
```

### Получить сводку по всем сканированиям

```bash
curl http://localhost:8000/api/v1/scan/history/summary
```

### Получить сводку только по Могилёву

```bash
curl http://localhost:8000/api/v1/scan/history/summary?city=mogilev
```

## Тесты

**Файл:** `backend/tests/test_scan_history.py`

13 тестов покрывают функционал Scan History:

- ✅ Создание записи сканирования
- ✅ Обновление статистики
- ✅ Завершение сканирования (успех/ошибка)
- ✅ Получение списка истории
- ✅ Фильтрация по городу и статусу
- ✅ Получение одной записи
- ✅ Сводная статистика
- ✅ Валидация API параметров

Запуск тестов:
```bash
docker-compose exec backend python -m pytest tests/test_scan_history.py -v
```

## Миграция БД

**Файл:** `backend/app/db/migrations/versions/007_add_scan_history_table.py`

Миграция создает таблицу `scan_history` и индекс на колонке `city`.

Применение миграции:
```bash
# Автоматически через alembic
docker-compose exec backend alembic upgrade head

# Или вручную (если таблицы уже существуют)
docker-compose exec db psql -U postgres -d kufar_monitor -c "
CREATE TABLE IF NOT EXISTS scan_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    city VARCHAR NOT NULL,
    city_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'running',
    trigger_type VARCHAR NOT NULL DEFAULT 'manual',
    listings_fetched INTEGER DEFAULT 0,
    listings_created INTEGER DEFAULT 0,
    listings_updated INTEGER DEFAULT 0,
    listings_deleted INTEGER DEFAULT 0,
    pages_scraped INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    duration_seconds INTEGER,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS ix_scan_history_city ON scan_history(city);
"
```

## Преимущества

1. **Аудит** - полная история всех запусков сканера
2. **Мониторинг** - можно отследить проблемы и ошибки
3. **Аналитика** - статистика по эффективности сканирования
4. **Отладка** - понимание что происходило во время сканирования
5. **Прозрачность** - видно разницу между ручными и запланированными сканированиями

## Будущие улучшения

- [ ] Автоматические алерты при ошибках сканирования (email/telegram)
- [ ] Дашборд с графиками и статистикой
- [ ] Экспорт истории в CSV/Excel
- [ ] Сравнение эффективности сканирований по городам
- [ ] Прогнозирование времени следующего сканирования
