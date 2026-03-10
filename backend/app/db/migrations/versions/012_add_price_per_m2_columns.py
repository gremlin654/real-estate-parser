"""Add price_per_m2_byn and price_per_m2_usd columns

Revision ID: 012
Revises: 83ad2bab3eb7
Create Date: 2026-03-09 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: Union[str, None] = "83ad2bab3eb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем новые колонки для цены за м²
    op.add_column(
        "listings",
        sa.Column("price_per_m2_byn", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "listings",
        sa.Column("price_per_m2_usd", sa.Numeric(precision=12, scale=2), nullable=True),
    )

    # Создаём индексы для ускорения фильтрации и сортировки
    op.create_index(
        "idx_listings_price_per_m2_byn",
        "listings",
        ["price_per_m2_byn"],
        unique=False,
    )
    op.create_index(
        "idx_listings_price_per_m2_usd",
        "listings",
        ["price_per_m2_usd"],
        unique=False,
    )

    # Backfill: рассчитываем цену за м² для существующих записей
    # Делим цену на площадь только если area > 0
    op.execute("""
        UPDATE listings 
        SET 
            price_per_m2_byn = CAST(CAST(price AS NUMERIC) / CAST(area AS NUMERIC) AS NUMERIC(12,2)),
            price_per_m2_usd = CAST(CAST(price_usd AS NUMERIC) / CAST(area AS NUMERIC) AS NUMERIC(12,2))
        WHERE area > 0 AND price IS NOT NULL AND price_usd IS NOT NULL
        """)


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index("idx_listings_price_per_m2_usd", table_name="listings")
    op.drop_index("idx_listings_price_per_m2_byn", table_name="listings")

    # Удаляем колонки
    op.drop_column("listings", "price_per_m2_usd")
    op.drop_column("listings", "price_per_m2_byn")
