"""Add deal_score and deal_label columns

Revision ID: 018
Revises: 017
Create Date: 2026-04-13 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Добавляем поля для Deal Score:
    1. deal_score - скоринг выгодности объявления (0-100)
    2. deal_label - текстовая метка ("🔥 HOT", "👍 GOOD", "😐 NORMAL")
    
    Индексы:
    - idx_listings_deal_score - для сортировки по deal_score DESC NULLS LAST
    - idx_listings_deal_label - partial index для фильтрации по метке
    """
    # Добавляем колонки
    op.add_column("listings", sa.Column("deal_score", sa.Float(), nullable=True))
    op.add_column("listings", sa.Column("deal_label", sa.String(20), nullable=True))

    # Создаём индексы
    op.create_index(
        "idx_listings_deal_score",
        "listings",
        ["deal_score"],
        unique=False,
        postgresql_ops={"deal_score": "DESC NULLS LAST"},
    )
    op.create_index(
        "idx_listings_deal_label",
        "listings",
        ["deal_label"],
        unique=False,
        postgresql_where=sa.text("deal_label IS NOT NULL"),
    )


def downgrade() -> None:
    """
    Откатываем изменения: удаляем индексы и колонки.
    """
    # Удаляем индексы
    op.drop_index("idx_listings_deal_label", table_name="listings")
    op.drop_index("idx_listings_deal_score", table_name="listings")

    # Удаляем колонки
    op.drop_column("listings", "deal_label")
    op.drop_column("listings", "deal_score")
