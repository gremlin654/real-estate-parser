"""Add deal finder composite indexes

Revision ID: 013
Revises: 012
Create Date: 2026-03-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Добавляем составные индексы для оптимизации Deal Finder запросов.

    Индексы ускоряют:
    - Поиск выгодных предложений по городу и комнатам
    - Фильтрацию по статусу и цене за м²
    - Агрегацию средней цены за м²
    """
    # Индекс для фильтрации по городу, статусу и цене за м² (USD)
    # Используется в get_avg_price_per_m2 и get_deal_listings
    op.create_index(
        "idx_listings_city_status_price_m2",
        "listings",
        ["city", "status", "price_per_m2_usd"],
        unique=False,
    )

    # ✅ Индекс для фильтрации по городу, статусу и цене за м² (BYN)
    # Используется при переключении валюты на BYN
    op.create_index(
        "idx_listings_city_status_price_m2_byn",
        "listings",
        ["city", "status", "price_per_m2_byn"],
        unique=False,
    )

    # Индекс для фильтрации по комнатам и цене за м² (USD)
    # Используется для расчёта средней цены по комнатам
    op.create_index(
        "idx_listings_rooms_price_m2",
        "listings",
        ["rooms", "price_per_m2_usd"],
        unique=False,
    )


def downgrade() -> None:
    """Удаляем составные индексы."""
    op.drop_index("idx_listings_rooms_price_m2", table_name="listings")
    op.drop_index("idx_listings_city_status_price_m2_byn", table_name="listings")
    op.drop_index("idx_listings_city_status_price_m2", table_name="listings")
