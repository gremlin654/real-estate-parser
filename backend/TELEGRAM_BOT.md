# Telegram Bot для Kufar Monitor

Система Telegram уведомлений для оповещения о новых квартирах, соответствующих вашим фильтрам.

## Быстрый старт

### 1. Создать бота через BotFather

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям (введите имя и username бота)
4. Скопируйте полученный токен (вида `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Настроить .env

```bash
cd backend
cp .env.example .env
```

Отредактируйте `.env`:

```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_BOT_ENABLED=true
```

### 3. Запустить

```bash
docker-compose up -d backend
```

Проверьте что бот запущен:

```bash
docker-compose logs backend | grep -i telegram
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация пользователя и приветственное сообщение |
| `/help` | Справка по доступным командам |
| `/subscribe` | Создать подписку на уведомления о новых квартирах |
| `/settings` | Просмотр моих активных подписок |
| `/stop` | Отписаться от всех уведомлений |

## Как работает подписка

### Создание подписки

1. Отправьте `/subscribe`
2. Выберите город из inline keyboard (Минск, Могилёв, Гродно, Брест, Гомель, Витебск)
3. Выберите количество комнат (1, 2, 3, 4, 5+)
4. Введите минимальную цену (BYN)
5. Введите максимальную цену (BYN)
6. Подтвердите подписку

### Получение уведомлений

После каждого сканирования бот проверяет новые объявления и отправляет уведомления пользователям с активными подписками.

### Формат уведомления

```
🏠 Новая квартира в Минск!

📍 Адрес: пр. Независимости, 100
🚪 Комнат: 2
📐 Площадь: 54 м²
🏢 Этаж: 5/9
💰 Цена: $42,500 (123,750 BYN)
📊 Цена за м²: $833

🔗 https://re.kufar.by/vi/minsk/kupit/kvartiru/123456
```

## Настройки переменных окружения

### TELEGRAM_BOT_ENABLED
- **По умолчанию:** `false`
- **Описание:** Включить/выключить Telegram бота
- **Значения:** `true` / `false`

### TELEGRAM_BOT_TOKEN
- **По умолчанию:** `""` (пусто)
- **Описание:** Токен бота от BotFather (обязательно для работы)
- **Формат:** `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### TELEGRAM_MAX_RETRIES
- **По умолчанию:** `3`
- **Описание:** Максимальное количество попыток отправки сообщения при ошибке
- **Рекомендация:** 3-5

### TELEGRAM_RETRY_DELAY_SECONDS
- **По умолчанию:** `5`
- **Описание:** Задержка перед первой попыткой отправки (используется exponential backoff)
- **Рекомендация:** 5-10 секунд

### TELEGRAM_RATE_LIMIT_PER_MINUTE
- **По умолчанию:** `20`
- **Описание:** Максимальное количество уведомлений в минуту для предотвращения спама
- **Рекомендация:** 20-30

## Troubleshooting

### Бот не запускается

```bash
# Проверить логи
docker-compose logs backend | grep -i telegram

# Проверить .env
cat backend/.env | grep TELEGRAM

# Убедиться что TELEGRAM_BOT_ENABLED=true
```

### Пользователь не получает уведомления

```bash
# Проверить подписки (нужен доступ к БД)
docker-compose exec db psql -U postgres -d kufar_monitor \
  -c "SELECT * FROM telegram_subscriptions WHERE user_id = 'ваш-uuid';"

# Проверить notification_log
docker-compose exec db psql -U postgres -d kufar_monitor \
  -c "SELECT * FROM telegram_notification_log WHERE user_id = 'ваш-uuid' ORDER BY sent_at DESC LIMIT 10;"
```

### Бот заблокирован пользователем

Автоматически устанавливается `blocked_by_user = True` при получении `TelegramForbiddenError`.
Уведомления больше не отправляются этому пользователю.

Проверить заблокированных:

```bash
docker-compose exec db psql -U postgres -d kufar_monitor \
  -c "SELECT user_id, telegram_id, blocked_at FROM telegram_users WHERE blocked_by_user = true;"
```

### Слишком много уведомлений

Уменьшите `TELEGRAM_RATE_LIMIT_PER_MINUTE` или скорректируйте подписки с помощью `/settings` и `/stop`.

## Архитектура

```
Пользователь → Telegram Bot API → aiogram → Handlers → Services → PostgreSQL
                                                              ↓
Scraper → Новые объявления → TelegramNotificationService → Пользователи
```

### Компоненты

| Компонент | Описание | Файл |
|-----------|----------|------|
| **Bot** | Инициализация aiogram бота | `app/telegram/bot.py` |
| **Handlers** | Обработка команд (/start, /subscribe, etc) | `app/telegram/handlers/` |
| **Services** | Бизнес-логика уведомлений | `app/services/telegram_*.py` |
| **Database** | Хранение подписок и пользователей | `app/models/telegram_*.py` |
| **Scheduler** | Интеграция с планировщиком сканирования | `app/telegram/scheduler.py` |

### База данных

```sql
-- Пользователи Telegram
telegram_users (id, telegram_id, username, first_name, blocked_by_user, created_at)

-- Подписки на уведомления
telegram_subscriptions (id, user_id, city, rooms, price_from, price_to, active, created_at)

-- Лог отправленных уведомлений
telegram_notification_log (id, user_id, listing_id, sent_at, status)
```

## Тесты

```bash
# Все Telegram тесты
docker-compose exec backend python -m pytest tests/test_telegram*.py -v

# Coverage
docker-compose exec backend python -m pytest tests/test_telegram*.py \
  --cov=app/telegram --cov=app/services/telegram_*
```

## Безопасность

- **Токен бота** хранится только в `.env` файле и НЕ коммитится в репозиторий
- **Telegram ID** пользователей хешируется при логировании
- **Rate limiting** предотвращает спам уведомлениями
- **Автоматическая блокировка** при `TelegramForbiddenError`

## API Integration

Telegram бот интегрируется с существующими API endpoints:

```bash
GET /api/v1/listings?city=minsk&rooms=2&price_from=50000&price_to=150000
```

Используется для получения новых объявлений после каждого сканирования.

## Масштабирование

При большом количестве пользователей:

1. Увеличьте `TELEGRAM_RATE_LIMIT_PER_MINUTE`
2. Настройте batch отправку уведомлений
3. Используйте Redis для кэширования результатов сканирования
4. Рассмотрите очередь сообщений (Celery + Redis) для асинхронной отправки
