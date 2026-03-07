from pydantic_settings import BaseSettings
from typing import Literal

CITY_CHOICES = Literal["mogilev", "minsk", "grodno", "brest", "gomel", "vitebsk"]


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:secret@db/kufar_monitor"
    TEST_DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@db_test/kufar_monitor_test"
    )
    SCAN_INTERVAL_MINUTES: int = 30
    API_PREFIX: str = "/api/v1"
    KUFAR_CITY: CITY_CHOICES = "mogilev"

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_RETENTION_DAYS: int = 7
    LOG_ROTATION_SIZE: str = "10 MB"
    LOG_COMPRESSION: str = "zip"

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
