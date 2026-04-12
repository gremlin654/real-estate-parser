"""
Модели для Telegram Bot интеграции.

Модуль содержит SQLAlchemy модели для хранения пользователей Telegram,
их подписок на уведомления и лога отправленных уведомлений.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    Numeric,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.db.database import Base


def utc_now() -> datetime:
    """Возвращает текущее UTC время без timezone info."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TelegramUser(Base):
    """
    Модель пользователя Telegram.

    Хранит информацию о пользователях которые подключили бота
    и настроили уведомления о новых объявлениях.

    Attributes:
        id: UUID первичный ключ записи
        telegram_id: Идентификатор пользователя в Telegram (unique)
        username: Username пользователя в Telegram
        first_name: Имя пользователя
        last_name: Фамилия пользователя
        language_code: Код языка (ru, en, etc.)
        is_active: Флаг активности пользователя
        blocked_by_user: True если пользователь заблокировал бота
        created_at: Дата и время регистрации
        updated_at: Дата и время последнего обновления
    """

    __tablename__ = "telegram_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default="ru")
    is_active = Column(Boolean, default=True)
    blocked_by_user = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    subscriptions = relationship(
        "TelegramSubscription",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notification_logs = relationship(
        "TelegramNotificationLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<TelegramUser(id={self.id}, telegram_id={self.telegram_id}, "
            f"username='{self.username}')>"
        )


class TelegramSubscription(Base):
    """
    Модель подписки на уведомления.

    Хранит параметры фильтрации для уведомлений о новых объявлениях.
    Пользователь может иметь несколько подписок с разными фильтрами.

    Attributes:
        id: UUID первичный ключ записи
        user_id: UUID пользователя (FK → telegram_users.id)
        city: Город для мониторинга (minsk, mogilev, grodno, brest, gomel, vitebsk)
        rooms: Список комнат (NULL = любые, [1,2,3] = конкретные, [5] = 5+)
        price_min: Минимальная цена
        price_max: Максимальная цена
        price_per_m2_max: Максимальная цена за м²
        floor_min: Минимальный этаж
        floor_max: Максимальный этаж
        currency: Валюта расчётов (byn/usd)
        notify_only_price_drop: Уведомлять только о падении цены
        exclude_deal_below_percent: Исключить deal ниже X%
        is_active: Флаг активности подписки
        created_at: Дата и время создания
        updated_at: Дата и время последнего обновления
    """

    __tablename__ = "telegram_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("telegram_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    city = Column(String(50), nullable=False, index=True)
    rooms = Column(ARRAY(Integer), nullable=True)
    price_min = Column(Integer, nullable=True)
    price_max = Column(Integer, nullable=True)
    price_per_m2_max = Column(Numeric(10, 2), nullable=True)
    floor_min = Column(Integer, nullable=True)
    floor_max = Column(Integer, nullable=True)
    currency = Column(String(10), default="usd")
    notify_only_price_drop = Column(Boolean, default=False)
    exclude_deal_below_percent = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("TelegramUser", back_populates="subscriptions")
    notification_logs = relationship(
        "TelegramNotificationLog",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )

    # Индексы
    __table_args__ = (
        # Композитный индекс для быстрого поиска подписок по городу
        Index(
            "idx_telegram_subscriptions_user_city",
            "user_id",
            "city",
            unique=False,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TelegramSubscription(id={self.id}, user_id={self.user_id}, "
            f"city='{self.city}', rooms={self.rooms})>"
        )


class TelegramNotificationStatus(str, Enum):
    """Статус отправки уведомления."""

    sent = "sent"
    failed = "failed"
    retry = "retry"
    blocked = "blocked"


class TelegramNotificationLog(Base):
    """
    Лог отправленных уведомлений.

    Хранит историю всех попыток отправки уведомлений пользователям.
    Используется для отслеживания статусов, повторных попыток и аналитики.

    Attributes:
        id: UUID первичный ключ записи
        user_id: UUID пользователя (FK → telegram_users.id)
        listing_id: UUID объявления (FK → listings.id, может быть NULL)
        subscription_id: UUID подписки (FK → telegram_subscriptions.id)
        sent_at: Дата и время отправки
        status: Статус отправки (sent/failed/retry/blocked)
        error_message: Текст ошибки при неудачной отправке
        retry_count: Количество повторных попыток
        response_message_id: ID отправленного сообщения в Telegram
    """

    __tablename__ = "telegram_notification_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("telegram_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    listing_id = Column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("telegram_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    sent_at = Column(DateTime, default=utc_now, index=True)
    status = Column(
        SQLEnum(TelegramNotificationStatus, create_type=False),
        nullable=False,
    )
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    response_message_id = Column(BigInteger, nullable=True)

    # Relationships
    user = relationship("TelegramUser", back_populates="notification_logs")
    listing = relationship("Listing", backref="telegram_notification_logs")
    subscription = relationship(
        "TelegramSubscription", back_populates="notification_logs"
    )

    # Индексы
    __table_args__ = (
        # Композитный индекс для поиска уведомлений пользователя по времени
        Index(
            "idx_telegram_notification_log_user_sent",
            "user_id",
            "sent_at",
            unique=False,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TelegramNotificationLog(id={self.id}, user_id={self.user_id}, "
            f"status='{self.status.value}', sent_at={self.sent_at})>"
        )
