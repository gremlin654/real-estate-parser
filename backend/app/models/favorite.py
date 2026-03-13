"""
Модель избранных объявлений (Favorites).

Модуль содержит SQLAlchemy модели для хранения избранных объявлений пользователей.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.listing import Listing


class Favorite(Base):
    """
    Модель избранного объявления.

    Представляет связь между пользователем и объявлением которое он добавил в избранное.
    Использует session-based идентификацию пользователей (пока заглушка).

    Attributes:
        id: UUID первичный ключ записи
        user_id: UUID пользователя (session-based)
        listing_id: UUID объявления (foreign key → listings.id)
        created_at: Дата и время добавления в избранное
        listing: Relationship к объекту Listing
    """

    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    listing_id = Column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship к Listing с eager loading
    listing = relationship("Listing", back_populates="favorites", lazy="selectin")

    # Индексы для оптимизации запросов
    __table_args__ = (
        # Уникальное ограничение на пару (user_id, listing_id)
        Index(
            "uq_favorites_user_listing",
            "user_id",
            "listing_id",
            unique=True,
        ),
        # Композитный индекс для быстрого поиска с сортировкой по дате
        Index(
            "idx_favorites_user_created",
            "user_id",
            "created_at",
            unique=False,
        ),
    )

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return f"<Favorite(id={self.id}, user_id={self.user_id}, listing_id={self.listing_id})>"
