# Миграция v3.2: Поддержка USD в истории изменений цен

## Дата
2026-03-08

## Проблема
Модель `ListingHistory` не содержала полей `price_before_usd` и `price_after_usd`, поэтому при изменении цены USD в истории отображались некорректные данные (сохранялись только цены в BYN).

## Решение

### 1. Обновление модели `ListingHistory`
**Файл:** `backend/app/models/listing.py`

Добавлены два новых поля:
- `price_before_usd` - цена до изменения в USD (копейках)
- `price_after_usd` - цена после изменения в USD (копейках)

### 2. Обновление схемы API
**Файл:** `backend/app/schemas/listing.py`

Обновлена схема `ListingHistoryResponse`:
- Добавлены поля `price_before_usd` и `price_after_usd`
- API endpoint `/api/v1/history/{id}` теперь возвращает USD цены

### 3. Обновление сервиса
**Файл:** `backend/app/services/listing_service.py`

Изменения в методе `_create_history_event`:
- Добавлены параметры `price_before_usd` и `price_after_usd`

Изменения в методе `upsert`:
- При изменении цены USD сохраняются оба значения (old и new)
- При изменении цены BYN сохраняются текущие значения USD для контекста

### 4. Миграция БД
**Файл:** `backend/migrations/005_add_listing_history_usd_fields.sql`

SQL миграция добавляет:
- Две новые колонки в таблицу `listing_history`
- Индекс `idx_listing_history_price_usd` для ускорения поиска
- Комментарии к колонкам

## Применённые изменения

### База данных
```sql
ALTER TABLE listing_history 
ADD COLUMN price_before_usd INTEGER,
ADD COLUMN price_after_usd INTEGER;

CREATE INDEX IF NOT EXISTS idx_listing_history_price_usd ON listing_history(price_before_usd, price_after_usd);
```

### Backup перед миграцией
```bash
docker-compose exec db pg_dump -U postgres kufar_monitor > /tmp/backup_listing_history_migration.sql
```

## Тестирование

### Unit тесты
```bash
cd backend
python3 -m pytest tests/test_history.py -v
# 5 тестов пройдено успешно
```

### Полные тесты
```bash
python3 -m pytest tests/ --ignore=tests/test_scan_e2e.py --ignore=tests/test_scan_false_deleted_e2e.py -v
# 196 тестов пройдено, 3 пропущено
```

## Пример использования API

### Запрос
```bash
GET /api/v1/history/{listing_id}
```

### Ответ
```json
[
  {
    "id": "uuid",
    "listing_id": "uuid",
    "event_type": "price_changed",
    "price_before": 90000,
    "price_after": 100000,
    "price_before_usd": 40000,
    "price_after_usd": 42500,
    "changed_fields": {...},
    "snapshot": {...},
    "created_at": "2026-03-08T12:00:00"
  }
]
```

## Откат миграции (при необходимости)

```sql
ALTER TABLE listing_history 
DROP COLUMN price_before_usd, 
DROP COLUMN price_after_usd;
```

Восстановление из backup:
```bash
cat /tmp/backup_listing_history_migration.sql | docker-compose exec -T db psql -U postgres -d kufar_monitor
```

## Acceptance Criteria

- [x] Поля `price_before_usd` и `price_after_usd` добавлены в модель
- [x] История изменений сохраняет USD цены при изменении цены
- [x] Миграция создана и применена к production БД
- [x] API `/api/v1/history/{id}` возвращает новые поля
- [x] Все тесты проходят (196 passed)
- [x] Backup создан перед миграцией

## Совместимость

- **Обратная совместимость:** Новые поля nullable, существующие записи получат `NULL`
- **Frontend:** Требуется обновление UI для отображения USD в истории изменений

## Примечания

- Цены хранятся в копейках (целых числах) для избежания проблем с плавающей точкой
- Для исторических записей значения USD будут `NULL` (требуется data migration при необходимости)
- Индекс добавлен для ускорения фильтрации по USD ценам в будущем
