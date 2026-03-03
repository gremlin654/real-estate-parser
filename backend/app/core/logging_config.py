from loguru import logger
from app.config import settings


def setup_logging():
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=settings.LOG_LEVEL,
    )


def get_logger(name: str):
    return logger
