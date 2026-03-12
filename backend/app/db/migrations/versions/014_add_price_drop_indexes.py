"""Add price drop tracker indexes

Revision ID: 014
Revises: 013
Create Date: 2026-03-12 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Добавляем индексы для оптимизации Price Drop Tracker запросов.

    Индексы ускоряют:
    - Поиск объявлений с падением цены по city и event_type
    - Сортировку по created_at для истории цен
    - Агрегацию MAX/MIN для расчёта drop_percent
    """
    # Композитный индекс для фильтрации по listing_id и event_type
    # Используется в get_price_drop_listings для GROUP BY и фильтрации
    op.create_index(
        "idx_listing_history_listing_event",
        "listing_history",
        ["listing_id", "event_type"],
        unique=False,
    )

    # Индекс для сортировки по времени создания
    # Используется для получения истории в хронологическом порядке
    op.create_index(
        "idx_listing_history_created_at",
        "listing_history",
        ["created_at"],
        unique=False,
    )

    # Композитный индекс для city фильтрации в listing_history
    # Через JOIN с listings таблицей для фильтрации по городу
    op.create_index(
        "idx_listing_history_listing_id_created",
        "listing_history",
        ["listing_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Удаляем индексы Price Drop Tracker."""
    op.drop_index("idx_listing_history_listing_id_created", table_name="listing_history")
    op.drop_index("idx_listing_history_created_at", table_name="listing_history")
    op.drop_index("idx_listing_history_listing_event", table_name="listing_history")
