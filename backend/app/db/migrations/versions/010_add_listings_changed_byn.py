"""Add listings_changed_byn column to scan_history

Revision ID: 010
Revises: 009
Create Date: 2026-03-02 02:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add listings_changed_byn column to scan_history table
    op.add_column(
        "scan_history",
        sa.Column("listings_changed_byn", sa.Integer(), nullable=True, default=0),
    )
    # Set default value for existing records
    op.execute(
        "UPDATE scan_history SET listings_changed_byn = 0 WHERE listings_changed_byn IS NULL"
    )


def downgrade() -> None:
    op.drop_column("scan_history", "listings_changed_byn")
