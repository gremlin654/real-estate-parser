"""Add new statuses: new, updated

Revision ID: 002
Revises: 001
Create Date: 2026-02-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new values to listing_status enum."""
    # Add new enum values to existing enum type
    op.execute("ALTER TYPE listingstatus ADD VALUE IF NOT EXISTS 'new'")
    op.execute("ALTER TYPE listingstatus ADD VALUE IF NOT EXISTS 'updated'")


def downgrade() -> None:
    """Remove new values from listing_status enum."""
    # Convert new statuses to active
    op.execute("UPDATE listings SET status = 'active' WHERE status IN ('new', 'updated')")
    # Note: PostgreSQL doesn't support removing enum values, so we can't fully downgrade
