"""Fix favorites user_id type to UUID

Revision ID: 016
Revises: 015
Create Date: 2026-03-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Исправляем тип колонки user_id с character varying на UUID.

    Используем USING clause для конвертации существующих данных.
    """
    # Изменяем тип колонки user_id на UUID
    op.alter_column(
        "favorites",
        "user_id",
        existing_type=sa.String(),
        type_=UUID(as_uuid=True),
        existing_nullable=False,
        postgresql_using="user_id::uuid",
    )


def downgrade() -> None:
    """
    Возвращаем тип колонки user_id к character varying.
    """
    op.alter_column(
        "favorites",
        "user_id",
        existing_type=UUID(as_uuid=True),
        type_=sa.String(),
        existing_nullable=False,
    )
