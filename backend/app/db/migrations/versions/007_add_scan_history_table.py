"""Add scan_history table

Revision ID: 007_add_scan_history_table
Revises: 006_remove_unreliable_fields
Create Date: 2026-03-01

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006_remove_unreliable_fields"
branch_labels = None
depends_on = None


def upgrade():
    # Create scan_history table
    op.create_table(
        "scan_history",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("city_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, default="running"),
        sa.Column("trigger_type", sa.String(), nullable=False, default="manual"),
        sa.Column("listings_fetched", sa.Integer(), default=0),
        sa.Column("listings_created", sa.Integer(), default=0),
        sa.Column("listings_updated", sa.Integer(), default=0),
        sa.Column("listings_deleted", sa.Integer(), default=0),
        sa.Column("pages_scraped", sa.Integer(), default=0),
        sa.Column("errors", JSONB(), default=list),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    # Create index on city column for faster filtering
    op.create_index("ix_scan_history_city", "scan_history", ["city"])


def downgrade():
    # Drop index
    op.drop_index("ix_scan_history_city", "scan_history")

    # Drop table
    op.drop_table("scan_history")
