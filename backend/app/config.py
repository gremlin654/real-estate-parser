from pydantic_settings import BaseSettings
from typing import Literal

CITY_CHOICES = Literal["mogilev", "minsk", "grodno", "brest", "gomel", "vitebsk"]


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:secret@db/kufar_monitor"
    TEST_DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@db_test/kufar_monitor_test"
    )

    # Redis настройки
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_TEST_URL: str = "redis://redis:6379/1"

    # Настройки кэширования (TTL в секундах)
    CACHE_TTL_STATS_SUMMARY: int = 60  # Кэш для сводной статистики
    CACHE_TTL_STATS_OTHER: int = 300  # Кэш для остальных статистических данных
    CACHE_TTL_LISTINGS: int = 30  # Кэш для списка объявлений
    CACHE_TTL_KUFAR_RESPONSE: int = 300  # Кэш для ответов Kufar API

    # Rate limiting - Token Bucket алгоритм
    # Уменьшено для предотвращения блокировок Kufar при одновременном сканировании
    # Каждый город имеет свой bucket
    RATE_LIMIT_CAPACITY: int = 5  # Максимум токенов на город (burst)
    RATE_LIMIT_REFILL_RATE: float = (
        2.0  # Токенов в секунду на город (медленнее чтобы не блокировали)
    )
    RATE_LIMIT_TTL: int = 3600  # TTL ключей (1 час)
    RATE_LIMIT_REQUESTS_PER_SECOND: int = (
        2  # На каждый город (осторожно при 6 городах = 12/sec total)
    )

    # Lock timeout для сканирования
    SCAN_LOCK_TIMEOUT_SECONDS: int = 3600  # 1 час

    SCAN_INTERVAL_MINUTES: int = 30
    API_PREFIX: str = "/api/v1"
    KUFAR_CITY: CITY_CHOICES = "mogilev"

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_RETENTION_DAYS: int = 7
    LOG_ROTATION_SIZE: str = "10 MB"
    LOG_COMPRESSION: str = "zip"

    # Telegram Bot настройки
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_ENABLED: bool = False
    TELEGRAM_MAX_RETRIES: int = 3
    TELEGRAM_RETRY_DELAY_SECONDS: int = 5
    TELEGRAM_RATE_LIMIT_PER_MINUTE: int = 20

    class Config:
        env_file = ".env"


settings = Settings()


CITY_NAMES = {
    "mogilev": "Могилёв",
    "minsk": "Минск",
    "grodno": "Гродно",
    "brest": "Брест",
    "gomel": "Гомель",
    "vitebsk": "Витебск",
}
