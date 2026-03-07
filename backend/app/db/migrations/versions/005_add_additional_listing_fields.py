"""Add additional listing fields

Revision ID: 005
Revises: 004
Create Date: 2026-02-26

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add additional columns to listings table."""
    op.add_column("listings", sa.Column("total_floors", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("listings", sa.Column("district", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("metro", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("house_year", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("house_type", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("renovation", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("furniture", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("heating", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("windows", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("bathroom", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("balcony", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("pets", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("agent_type", sa.String(), nullable=True))


def downgrade() -> None:
    """Remove additional columns from listings table."""
    op.drop_column("listings", "agent_type")
    op.drop_column("listings", "pets")
    op.drop_column("listings", "balcony")
    op.drop_column("listings", "bathroom")
    op.drop_column("listings", "windows")
    op.drop_column("listings", "heating")
    op.drop_column("listings", "furniture")
    op.drop_column("listings", "renovation")
    op.drop_column("listings", "house_type")
    op.drop_column("listings", "house_year")
    op.drop_column("listings", "metro")
    op.drop_column("listings", "district")
    op.drop_column("listings", "description")
    op.drop_column("listings", "total_floors")
