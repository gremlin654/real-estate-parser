"""Remove unreliable fields from Kufar API

Revision ID: 006_remove_unreliable_fields
Revises: 005_add_additional_listing_fields
Create Date: 2026-02-26

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "006_remove_unreliable_fields"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    # Drop unreliable columns that return incorrect data from Kufar API
    op.drop_column("listings", "agent_type")
    op.drop_column("listings", "pets")
    op.drop_column("listings", "balcony")
    op.drop_column("listings", "bathroom")
    op.drop_column("listings", "windows")
    op.drop_column("listings", "heating")
    op.drop_column("listings", "furniture")
    op.drop_column("listings", "renovation")
    op.drop_column("listings", "house_type")


def downgrade():
    # Add columns back (without data)
    op.add_column("listings", sa.Column("house_type", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("renovation", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("furniture", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("heating", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("windows", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("bathroom", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("balcony", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("pets", sa.String(), nullable=True))
    op.add_column("listings", sa.Column("agent_type", sa.String(), nullable=True))
