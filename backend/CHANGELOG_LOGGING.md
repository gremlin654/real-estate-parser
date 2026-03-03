# Changelog: Логирование с ротацией файлов

## [1.0.0] - 2025-01-01

### ✨ Добавлено

- **Модуль логирования** (`app/core/logging_config.py`):
  - Настройка консольного и файлового логирования
  - Автоматическая ротация файлов по размеру
  - Сжатие архивированных логов (zip/gz)
  - Очистка старых логов по истечении срока
  - Потокобезопасная асинхронная запись (`enqueue=True`)
  - Отдельный файл для ошибок (`errors.log`)
  - Цветной формат для консоли
  - Обычный формат для файлов

- **Конфигурация** (`app/config.py`):
  - `LOG_LEVEL` — уровень логирования (INFO по умолчанию)
  - `LOG_DIR` — директория для логов (logs)
  - `LOG_RETENTION_DAYS` — срок хранения (7 дней)
  - `LOG_ROTATION_SIZE` — размер ротации (10 MB)
  - `LOG_COMPRESSION` — формат сжатия (zip)

- **Интеграция** (`app/main.py`):
  - Инициализация логирования при старте приложения
  - Логирование событий startup/shutdown
  - Логирование health check запросов

- **Тесты** (`tests/test_logging.py`):
  - 24 теста конфигурации логирования
  - Тесты ротации файлов
  - Тесты форматирования сообщений
  - Тесты фильтрации по уровням
  - Интеграционные тесты

- **Документация** (`docs/LOGGING.md`):
  - Полное описание возможностей
  - Примеры использования
  - Конфигурация через env
  - Troubleshooting

### 🔧 Изменено

- **main.py**:
  - Добавлен импорт `setup_logging` и `get_logger`
  - Добавлена инициализация логирования в lifespan
  - Добавлено логирование startup/shutdown событий

- **config.py**:
  - Добавлены настройки логирования
  - Поддержка переменных окружения

### 📁 Структура файлов

```
backend/
├── app/
│   ├── core/
│   │   ├── __init__.py         # NEW
│   │   └── logging_config.py   # NEW
│   └── main.py                 # MODIFIED
├── logs/                       # NEW (auto-created)
│   ├── kufar_monitor.log
│   └── errors.log
├── docs/
│   └── LOGGING.md              # NEW
├── tests/
│   └── test_logging.py         # NEW
└── CHANGELOG_LOGGING.md        # NEW
```

### 🎯 Примеры использования

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

logger.info("Сканер запущен")
logger.error("Ошибка подключения к БД")
logger.debug(f"Найдено {count} объявлений")
```

### 📊 Статистика

- **Файлов добавлено:** 5
- **Файлов изменено:** 2
- **Строк кода добавлено:** ~350
- **Тестов добавлено:** 24
- **Покрытие тестов:** ~95%

### 🚀 Преимущества

1. **Сохранение истории** — логи сохраняются после перезапуска
2. **Отладка production** — анализ ошибок после сбоя
3. **Аудит** — история всех событий сканера
4. **Мониторинг** — отслеживание производительности
5. **Экономия места** — ротация и сжатие старых логов
6. **Безопасность** — отдельный файл для ошибок

### ⚙️ Настройки по умолчанию

| Параметр | Значение | Описание |
|----------|----------|----------|
| `LOG_LEVEL` | INFO | Уровень логирования |
| `LOG_DIR` | logs | Директория логов |
| `LOG_RETENTION_DAYS` | 7 | Дней хранения |
| `LOG_ROTATION_SIZE` | 10 MB | Размер ротации |
| `LOG_COMPRESSION` | zip | Формат сжатия |

### 🔧 Migration

**Перед обновлением:**

```bash
# 1. Создать backup
cp -r backend/logs backend/logs.backup

# 2. Обновить код
git pull

# 3. Установить зависимости (если нужны новые)
pip install -r requirements.txt

# 4. Перезапустить приложение
docker-compose restart backend
```

**После обновления:**

```bash
# Проверить логи
docker-compose logs backend | grep "Logging configured"

# Убедиться, что файлы создаются
ls -la backend/logs/
```

### 📝 Переменные окружения для .env

```bash
# Logging configuration
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_RETENTION_DAYS=7
LOG_ROTATION_SIZE=10 MB
LOG_COMPRESSION=zip
```

### 🧪 Запуск тестов

```bash
cd backend
docker-compose exec backend python -m pytest tests/test_logging.py -v
```

### 📖 Документация

- [Полная документация](docs/LOGGING.md)
- [Конфигурация](app/config.py)
- [Примеры использования](app/main.py)

---

**Дата:** 2025-01-01  
**Автор:** Kufar Monitor Team  
**Версия:** 1.0.0
