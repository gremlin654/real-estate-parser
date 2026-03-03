# Логирование с ротацией файлов

## Обзор

Система логирования для Kufar Monitor с автоматической ротацией файлов, сжатием и очисткой старых логов.

## Возможности

✅ **Консольное логирование** — цветной вывод для разработки  
✅ **Файловое логирование** — сохранение в файлы с ротацией  
✅ **Разделение по уровням** — отдельный файл для ошибок  
✅ **Автоматическая ротация** — при достижении размера  
✅ **Сжатие архивов** — экономия места на диске  
✅ **Очистка старых логов** — удаление по истечении срока  
✅ **Потокобезопасность** — асинхронная запись с `enqueue=True`  
✅ **Настройка через env** — переменные окружения  

## Конфигурация

### Переменные окружения

```bash
# Backend
LOG_LEVEL=INFO              # Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs                # Директория для логов
LOG_RETENTION_DAYS=7        # Сколько дней хранить логи
LOG_ROTATION_SIZE=10 MB     # Максимальный размер файла до ротации
LOG_COMPRESSION=zip         # Формат сжатия: zip, gz, или None
```

### Программная настройка

```python
from app.core.logging_config import setup_logging

# Настройка с параметрами по умолчанию (из config)
setup_logging()

# Кастомная настройка
setup_logging(
    log_level="DEBUG",
    log_dir="logs",
    retention_days=14,
    rotation_size="50 MB",
    compression="gz"
)
```

## Использование

### Базовое логирование

```python
from loguru import logger
from app.core.logging_config import get_logger

# Получить logger с именем модуля
logger = get_logger(__name__)

# Логирование на разных уровнях
logger.debug("Отладочная информация")
logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.critical("Критическая ошибка")

# Логирование с исключением
try:
    raise ValueError("Тестовая ошибка")
except Exception:
    logger.exception("Произошла ошибка при обработке")

# Логирование с контекстом
bound_logger = logger.bind(user_id="123", action="scan")
bound_logger.info("Действие выполнено")
```

### Формат логов

**Консоль (цветной):**
```
2025-01-01 12:00:00.000 | INFO     | app.main:lifespan:10 | Application startup initiated
```

**Файл (без цветов):**
```
2025-01-01 12:00:00.000 | INFO     | app.main:lifespan:10 | Application startup initiated
```

## Структура файлов

```
backend/
├── logs/
│   ├── kufar_monitor.log    # Основной лог (все уровни)
│   ├── errors.log           # Только ошибки (ERROR и выше)
│   ├── kufar_monitor.log.1.zip  # Архивированный ротированный лог
│   └── errors.log.1.zip     # Архивированный лог ошибок
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   └── logging_config.py  # Конфигурация логирования
│   └── main.py              # Инициализация logging при старте
└── tests/
    └── test_logging.py      # Тесты логирования
```

## Ротация файлов

### Как работает

1. **Достигнут размер** — когда файл достигает `LOG_ROTATION_SIZE` (10 MB по умолчанию)
2. **Создаётся новый файл** — основной лог очищается
3. **Старый файл архивируется** — сжимается в `.zip` или `.gz`
4. **Удаляются старые архивы** — старше `LOG_RETENTION_DAYS` дней

### Пример ротации

```
kufar_monitor.log        # Текущий активный лог
kufar_monitor.log.1.zip  # Вчерашний лог
kufar_monitor.log.2.zip  # Позавчерашний лог
...
kufar_monitor.log.7.zip  # Лог недельной давности (удалится через 24ч)
```

## Интеграция с приложением

### main.py

```python
from app.core.logging_config import setup_logging, get_logger

# Настройка логирования ПЕРЕД другими импортами
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup initiated")
    # ... startup code ...
    logger.info("Application startup completed successfully")
    
    yield
    
    logger.info("Application shutdown initiated")
    # ... shutdown code ...
    logger.info("Application shutdown completed")
```

### Другие модули

```python
from loguru import logger
from app.core.logging_config import get_logger

logger = get_logger(__name__)

def scrape_page():
    logger.info(f"Scraping page {page}")
    # ... scraping logic ...
    logger.info(f"Extracted {len(listings)} listings")
```

## Тестирование

### Запустить тесты

```bash
cd backend
docker-compose exec backend python -m pytest tests/test_logging.py -v
```

### Покрытие тестов

- ✅ Создание директории логов
- ✅ Настройка уровня логирования
- ✅ Ротация файлов
- ✅ Сжатие архивов
- ✅ Разделение ошибок
- ✅ Форматирование сообщений
- ✅ Логирование исключений
- ✅ Потокобезопасность
- ✅ Переменные окружения

## Troubleshooting

### Логи не записываются в файл

**Проверьте права доступа:**
```bash
ls -la backend/logs/
chmod 755 backend/logs/
```

**Проверьте переменные окружения:**
```bash
echo $LOG_LEVEL
echo $LOG_DIR
```

### Слишком много логов

**Уменьшите уровень логирования:**
```bash
LOG_LEVEL=WARNING
```

**Уменьшите срок хранения:**
```bash
LOG_RETENTION_DAYS=3
```

### Логи занимают много места

**Включите сжатие:**
```bash
LOG_COMPRESSION=zip
```

**Уменьшите размер ротации:**
```bash
LOG_ROTATION_SIZE=5 MB
```

### Fallback режим

Если файловое логирование не работает (нет прав, диск заполнен), система автоматически переключается на консольное логирование:

```
ERROR    | Failed to setup file logging: [Errno 28] No space left on device. Using console-only logging.
```

## Производительность

- **Асинхронная запись** — `enqueue=True` для потокобезопасности
- **Минимальные накладные расходы** — ~0.1ms на лог сообщение
- **Эффективное сжатие** — zip уменьшает размер в 5-10 раз

## Безопасность

⚠️ **Не логируйте чувствительные данные:**
- Пароли
- API ключи
- Персональные данные пользователей
- Токены аутентификации

## Мониторинг

### Проверка логов

```bash
# Последние 100 строк
tail -100 backend/logs/kufar_monitor.log

# Только ошибки
tail -100 backend/logs/errors.log

# Поиск по логам
grep "ERROR" backend/logs/kufar_monitor.log

# Просмотр архива
unzip -p backend/logs/kufar_monitor.log.1.zip | less
```

### Статистика

```bash
# Размер логов
du -sh backend/logs/

# Количество строк
wc -l backend/logs/kufar_monitor.log

# Количество ошибок
grep -c "ERROR" backend/logs/kufar_monitor.log
```

## Changelog

См. [CHANGELOG_LOGGING.md](../CHANGELOG_LOGGING.md)

## См. также

- [Retry Logic](docs/RETRY_LOGIC.md) — Повторные попытки с экспоненциальной задержкой
- [Config](app/config.py) — Конфигурация приложения
