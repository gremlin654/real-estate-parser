"""Add price_usd column to listings

Revision ID: 004
Revises: 003
Create Date: 2026-02-26

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add price_usd column to listings table."""
    op.add_column("listings", sa.Column("price_usd", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove price_usd column from listings table."""
    op.drop_column("listings", "price_usd")
