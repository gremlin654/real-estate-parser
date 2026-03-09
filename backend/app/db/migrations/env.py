from logging.config import fileConfig
from sqlalchemy import engine_from_config, create_engine, MetaData
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context
import sys
from os.path import abspath, dirname

sys.path.insert(0, abspath(dirname(dirname(dirname(__file__)))))

# Не импортируем Base с моделями - они используют ENUM с create_type=False
# что вызывает ошибки при миграциях. Используем пустую метадату.
# from app.db.database import Base

from app.config import settings

config = context.config
DB_URL = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", DB_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Пустая метадата чтобы избежать автоматического создания ENUM типов
target_metadata = MetaData()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
