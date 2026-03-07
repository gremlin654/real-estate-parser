"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-23

"""

from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём ENUM типы только если они не существуют
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'listingstatus') THEN CREATE TYPE listingstatus AS ENUM ('active', 'deleted', 'archived'); END IF; END $$;"
    )
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'eventtype') THEN CREATE TYPE eventtype AS ENUM ('created', 'price_changed', 'edited', 'deleted', 'restored'); END IF; END $$;"
    )

    # Создаём таблицы
    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kufar_id", sa.String(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("rooms", sa.Integer(), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "active", "deleted", "archived", name="listingstatus", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("first_seen_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_listings_kufar_id"), "listings", ["kufar_id"], unique=True)

    op.create_table(
        "listing_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "created",
                "price_changed",
                "edited",
                "deleted",
                "restored",
                name="eventtype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("price_before", sa.Integer(), nullable=True),
        sa.Column("price_after", sa.Integer(), nullable=True),
        sa.Column(
            "changed_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["listing_id"],
            ["listings.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("listing_history")
    op.drop_index(op.f("ix_listings_kufar_id"), table_name="listings")
    op.drop_table("listings")
    op.execute("DROP TYPE IF EXISTS listingstatus")
    op.execute("DROP TYPE IF EXISTS eventtype")
