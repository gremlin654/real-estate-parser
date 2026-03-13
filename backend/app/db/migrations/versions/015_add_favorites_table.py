"""Add favorites table

Revision ID: 015
Revises: 014
Create Date: 2026-03-13 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Создаём таблицу favorites для хранения избранных объявлений.

    Таблица позволяет пользователям сохранять избранные объявления
    для быстрого доступа к ним в будущем.

    Структура:
    - id: UUID первичный ключ
    - user_id: UUID пользователя (session-based, пока заглушка)
    - listing_id: UUID объявления (foreign key → listings.id)
    - created_at: DateTime создания записи

    Индексы:
    - idx_favorites_user_id: для быстрого поиска по пользователю
    - idx_favorites_listing_id: для быстрого поиска по объявлению
    - uq_favorites_user_listing: уникальный индекс на пару (user_id, listing_id)
    """
    # Создаём таблицу favorites
    op.create_table(
        "favorites",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            nullable=False,
            index=True,  # idx_favorites_user_id
        ),
        sa.Column(
            "listing_id",
            UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,  # idx_favorites_listing_id
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            default=sa.func.now(),
            nullable=False,
        ),
        # Уникальное ограничение на пару (user_id, listing_id)
        sa.UniqueConstraint(
            "user_id", "listing_id", name="uq_favorites_user_listing"
        ),
    )

    # Создаём композитный индекс для быстрого поиска всех избранных пользователя
    # с сортировкой по дате добавления
    op.create_index(
        "idx_favorites_user_created",
        "favorites",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """
    Удаляем таблицу favorites.

    Внимание: Все данные об избранных объявлениях будут потеряны.
    """
    # Сначала удаляем индекс если существует
    op.drop_index("idx_favorites_user_created", table_name="favorites")
    op.drop_table("favorites")
