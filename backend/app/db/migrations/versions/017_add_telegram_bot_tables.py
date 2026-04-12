"""add telegram bot tables

Revision ID: 017
Revises: 016
Create Date: 2026-04-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID, ARRAY

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Создаём таблицы для Telegram Bot интеграции:
    1. telegram_users - пользователи бота
    2. telegram_subscriptions - подписки на уведомления
    3. telegram_notification_log - лог отправленных уведомлений
    """
    # Создаём enum type для статуса уведомлений через raw SQL (идемпотентно)
    op.execute(
        "CREATE TYPE IF NOT EXISTS telegram_notification_status AS ENUM "
        "('sent', 'failed', 'retry', 'blocked')"
    )

    # Таблица telegram_users
    op.create_table(
        "telegram_users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("language_code", sa.String(10), server_default="ru"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("blocked_by_user", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Индексы для telegram_users
    op.create_index(
        "idx_telegram_users_telegram_id",
        "telegram_users",
        ["telegram_id"],
        unique=False,
    )

    # Таблица telegram_subscriptions
    op.create_table(
        "telegram_subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("telegram_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("city", sa.String(50), nullable=False),
        sa.Column("rooms", ARRAY(sa.Integer), nullable=True),
        sa.Column("price_min", sa.Integer, nullable=True),
        sa.Column("price_max", sa.Integer, nullable=True),
        sa.Column("price_per_m2_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("floor_min", sa.Integer, nullable=True),
        sa.Column("floor_max", sa.Integer, nullable=True),
        sa.Column("currency", sa.String(10), server_default="usd"),
        sa.Column("notify_only_price_drop", sa.Boolean, server_default="false"),
        sa.Column("exclude_deal_below_percent", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Индексы для telegram_subscriptions
    op.create_index(
        "idx_telegram_subscriptions_user_id",
        "telegram_subscriptions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_telegram_subscriptions_city",
        "telegram_subscriptions",
        ["city"],
        unique=False,
    )
    op.create_index(
        "idx_telegram_subscriptions_is_active",
        "telegram_subscriptions",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "idx_telegram_subscriptions_user_city",
        "telegram_subscriptions",
        ["user_id", "city"],
        unique=False,
    )

    # Таблица telegram_notification_log
    op.create_table(
        "telegram_notification_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("telegram_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "listing_id",
            UUID(as_uuid=True),
            sa.ForeignKey("listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "subscription_id",
            UUID(as_uuid=True),
            sa.ForeignKey("telegram_subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sent_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "status",
            postgresql.ENUM(
                "sent",
                "failed",
                "retry",
                "blocked",
                name="telegram_notification_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("response_message_id", sa.BigInteger, nullable=True),
    )

    # Индексы для telegram_notification_log
    op.create_index(
        "idx_telegram_notification_log_user_id",
        "telegram_notification_log",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_telegram_notification_log_listing_id",
        "telegram_notification_log",
        ["listing_id"],
        unique=False,
    )
    op.create_index(
        "idx_telegram_notification_log_sent_at",
        "telegram_notification_log",
        ["sent_at"],
        unique=False,
    )
    op.create_index(
        "idx_telegram_notification_log_user_sent",
        "telegram_notification_log",
        ["user_id", "sent_at"],
        unique=False,
    )


def downgrade() -> None:
    """
    Откатываем миграцию: удаляем таблицы и enum type.
    """
    # Удаляем таблицы в обратном порядке создания
    op.drop_table("telegram_notification_log")
    op.drop_table("telegram_subscriptions")
    op.drop_table("telegram_users")

    # Удаляем enum type
    op.execute("DROP TYPE IF EXISTS telegram_notification_status")
