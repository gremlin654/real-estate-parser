"""Add city column to listings

Revision ID: 003
Revises: 002
Create Date: 2026-02-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add city column to listings table."""
    op.add_column('listings', sa.Column('city', sa.String(), nullable=True))
    op.create_index(op.f('ix_listings_city'), 'listings', ['city'], unique=False)


def downgrade() -> None:
    """Remove city column from listings table."""
    op.drop_index(op.f('ix_listings_city'), table_name='listings')
    op.drop_column('listings', 'city')
