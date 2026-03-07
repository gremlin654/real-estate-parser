"""scan settings per city

Revision ID: 011
Revises: 010
Create Date: 2026-03-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Добавить колонку city (nullable временно)
    op.add_column("scan_settings", sa.Column("city", sa.String(), nullable=True))

    # 2. Заполнить существующие записи city="mogilev" (default город)
    op.execute("UPDATE scan_settings SET city = 'mogilev' WHERE city IS NULL")

    # 3. Изменить тип id с Integer на UUID
    # Сначала добавить временную колонку
    op.add_column(
        "scan_settings",
        sa.Column("id_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Заполнить UUID для существующих записей
    op.execute(
        "UPDATE scan_settings SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL"
    )

    # Сделать id_uuid NOT NULL
    op.alter_column("scan_settings", "id_uuid", nullable=False)

    # Удалить старый primary key constraint
    op.drop_constraint("scan_settings_pkey", "scan_settings", type_="primary")

    # Удалить старую колонку id
    op.drop_column("scan_settings", "id")

    # Переименовать id_uuid в id
    op.alter_column("scan_settings", "id_uuid", new_column_name="id")

    # Добавить primary key constraint на новую колонку
    op.create_primary_key("scan_settings_pkey", "scan_settings", ["id"])

    # 4. Сделать city NOT NULL
    op.alter_column("scan_settings", "city", nullable=False)

    # 5. Создать unique constraint на city
    op.create_unique_constraint("uq_scan_settings_city", "scan_settings", ["city"])

    # 6. Создать index на city для ускорения поиска
    op.create_index("ix_scan_settings_city", "scan_settings", ["city"])

    # 7. Удалить default значение для city (теперь нет единственной записи)
    # 8. Удалить default значение для scan_interval_minutes (теперь требуется явно указывать)


def downgrade() -> None:
    # 1. Удалить index
    op.drop_index("ix_scan_settings_city", "scan_settings")

    # 2. Удалить unique constraint
    op.drop_constraint("uq_scan_settings_city", "scan_settings", type_="unique")

    # 3. Вернуть колонку id (Integer)
    op.add_column("scan_settings", sa.Column("id_old", sa.Integer(), nullable=True))

    # Заполнить id=1 для всех записей (в downgraded версии только одна запись)
    op.execute("UPDATE scan_settings SET id_old = 1 WHERE id_old IS NULL")

    # Удалить UUID primary key
    op.drop_constraint("scan_settings_pkey", "scan_settings", type_="primary")

    # Удалить UUID колонку
    op.drop_column("scan_settings", "id")

    # Переименовать id_old в id
    op.alter_column("scan_settings", "id_old", new_column_name="id")

    # Добавить primary key constraint
    op.create_primary_key("scan_settings_pkey", "scan_settings", ["id"])

    # 4. Удалить колонку city
    op.drop_column("scan_settings", "city")
