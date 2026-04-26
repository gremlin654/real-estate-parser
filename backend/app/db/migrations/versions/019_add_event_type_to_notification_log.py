"""Add event_type to telegram_notification_log for deduplication

Revision ID: 019
Revises: 018
Create Date: 2026-04-25 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Добавляем event_type колонку для дедупликации уведомлений.

    Позволяет разделять уведомления типа new_listing и price_drop
    для одного и того же listing+subscription — чтобы можно было
    отправить оба типа события одному пользователю.

    Также добавляется partial unique index для предотвращения дублей:
    один user не может получить два уведомления с одинаковым
    (listing_id, subscription_id, event_type).
    """
    op.add_column(
        "telegram_notification_log",
        sa.Column(
            "event_type",
            sa.Enum("new_listing", "price_drop", name="telegramnotificationeventtype"),
            nullable=True,
        ),
    )

    op.create_index(
        "idx_telegram_notification_log_dedup",
        "telegram_notification_log",
        ["user_id", "listing_id", "subscription_id", "event_type"],
        unique=True,
        postgresql_where=sa.text(
            "user_id IS NOT NULL "
            "AND listing_id IS NOT NULL "
            "AND subscription_id IS NOT NULL "
            "AND event_type IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "idx_telegram_notification_log_dedup",
        table_name="telegram_notification_log",
    )
    op.drop_column("telegram_notification_log", "event_type")
