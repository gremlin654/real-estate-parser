"""Add price_changed_byn status

Revision ID: 009
Revises: 008
Create Date: 2026-03-02 01:24:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new status 'price_changed_byn' to listing_status enum
    op.execute("ALTER TYPE listingstatus ADD VALUE IF NOT EXISTS 'price_changed_byn'")


def downgrade() -> None:
    # Can't remove enum values in PostgreSQL, so we just log a warning
    pass
