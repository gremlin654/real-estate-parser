import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ListingStatus(str, Enum):
    active = "active"
    new = "new"
    updated = "updated"
    price_changed_byn = "price_changed_byn"
    deleted = "deleted"
    archived = "archived"


class EventType(str, Enum):
    created = "created"
    price_changed = "price_changed"  # Изменение цены USD
    price_changed_byn = "price_changed_byn"  # Изменение цены BYN
    edited = "edited"
    deleted = "deleted"
    restored = "restored"


class Listing(Base):
    __tablename__ = "listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kufar_id = Column(String, unique=True, nullable=False, index=True)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    price_usd = Column(Integer, nullable=True)
    currency = Column(String, default="BYN")
    city = Column(String, nullable=True, index=True)
    address = Column(Text)
    rooms = Column(Integer)
    area = Column(Float)
    floor = Column(Integer)
    total_floors = Column(Integer)
    category = Column(String)
    description = Column(Text)
    district = Column(String)
    metro = Column(String)
    house_year = Column(Integer)
    images = Column(JSONB, default=list)
    raw_data = Column(JSONB)
    status = Column(
        SQLEnum(ListingStatus, create_type=False), default=ListingStatus.active
    )
    first_seen_at = Column(DateTime, default=utc_now)
    last_seen_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    deleted_at = Column(DateTime)

    history = relationship(
        "ListingHistory", back_populates="listing", cascade="all, delete-orphan"
    )


class ListingHistory(Base):
    __tablename__ = "listing_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    event_type = Column(SQLEnum(EventType, create_type=False), nullable=False)
    price_before = Column(Integer)
    price_after = Column(Integer)
    price_before_usd = Column(Integer)  # Цена до изменения в USD (копейках)
    price_after_usd = Column(Integer)  # Цена после изменения в USD (копейках)
    changed_fields = Column(JSONB)
    snapshot = Column(JSONB)
    created_at = Column(DateTime, default=utc_now)

    listing = relationship("Listing", back_populates="history")


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    city = Column(String, nullable=False, index=True)
    city_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="running")
    trigger_type = Column(String, nullable=False, default="manual")
    listings_fetched = Column(Integer, default=0)
    listings_created = Column(Integer, default=0)
    listings_updated = Column(Integer, default=0)
    listings_changed_byn = Column(Integer, default=0)
    listings_deleted = Column(Integer, default=0)
    listings_restored = Column(Integer, default=0)
    listings_unchanged = Column(Integer, default=0)
    pages_scraped = Column(Integer, default=0)
    errors = Column(JSONB, default=list)
    duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)


class ScanSettings(Base):
    __tablename__ = "scan_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city = Column(String, unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=False, nullable=False)
    scan_interval_minutes = Column(Integer, default=30, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ScanStats(Base):
    """Статистика сканирований по городам для валидации аномалий."""

    __tablename__ = "scan_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city = Column(String, unique=True, nullable=False, index=True)
    avg_listings_count = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=utc_now, onupdate=utc_now)
    # Хранит последние 10 значений для расчёта среднего
    recent_counts = Column(JSONB, default=list, nullable=False)
