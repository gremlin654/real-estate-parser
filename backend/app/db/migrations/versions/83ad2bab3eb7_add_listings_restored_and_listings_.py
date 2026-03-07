"""Add listings_restored and listings_unchanged to scan_history

Revision ID: 83ad2bab3eb7
Revises: 011
Create Date: 2026-03-07 21:52:53.392490

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83ad2bab3eb7'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to scan_history table
    op.add_column('scan_history', sa.Column('listings_restored', sa.Integer(), nullable=True, default=0))
    op.add_column('scan_history', sa.Column('listings_unchanged', sa.Integer(), nullable=True, default=0))


def downgrade() -> None:
    # Remove columns from scan_history table
    op.drop_column('scan_history', 'listings_unchanged')
    op.drop_column('scan_history', 'listings_restored')
