"""add scan settings table

Revision ID: 008
Revises: 007
Create Date: 2026-03-01

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade():
    # Create scan_settings table
    op.create_table(
        "scan_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_interval_minutes", sa.Integer(), nullable=False, default=30),
        sa.Column("enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("scan_interval_minutes >= 5", name="check_min_interval"),
        sa.CheckConstraint("scan_interval_minutes <= 1440", name="check_max_interval"),
    )

    # Insert default settings (single row)
    op.execute(
        """
        INSERT INTO scan_settings (id, scan_interval_minutes, enabled, updated_at)
        VALUES (1, 30, TRUE, NOW())
        ON CONFLICT (id) DO NOTHING
    """
    )


def downgrade():
    op.drop_table("scan_settings")
