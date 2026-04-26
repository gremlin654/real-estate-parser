"""
Telegram Web App API - управление подписками через Web App.

Endpoints для CRUD операций с подписками и получения конфигурации.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from uuid import UUID
from loguru import logger
import json

from app.db.database import get_db
from app.services.telegram_subscription_service import TelegramSubscriptionService
from app.models.telegram_user import (
    TelegramUser,
    TelegramSubscription,
    TelegramNotificationLog,
)
from app.config import CITY_NAMES

router = APIRouter(prefix="/telegram", tags=["telegram"])

# Лимиты
MAX_SUBSCRIPTIONS_PER_USER = 5


def get_telegram_user_id(
    x_telegram_user_id: Optional[str] = Header(None, alias="X-Telegram-User-Id"),
    authorization: Optional[str] = Header(None),
) -> int:
    """
    Получает Telegram user ID из заголовков.

    В реальном приложении это должно извлекаться из initData
    и валидироваться через Bot API. Для упрощения принимаем из заголовка.

    Args:
        x_telegram_user_id: Telegram user ID из заголовка
        authorization: Authorization заголовок (для future use)

    Returns:
        Telegram user ID

    Raises:
        HTTPException: Если Telegram user ID не предоставлен
    """
    if x_telegram_user_id:
        try:
            return int(x_telegram_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Telegram-User-Id format",
            )

    # Для разработки - использовать тестовый ID
    # В production это должно быть обязательно
    logger.warning("No X-Telegram-User-Id header provided, using default test ID")
    return 123456789


async def get_or_create_telegram_user(
    telegram_id: int,
    db: AsyncSession,
) -> TelegramUser:
    """
    Получает или создаёт пользователя Telegram.

    Args:
        telegram_id: ID пользователя в Telegram
        db: Сессия базы данных

    Returns:
        Объект TelegramUser
    """
    service = TelegramSubscriptionService(db)
    user = await service.get_user_by_telegram_id(telegram_id)

    if not user:
        # Создаём пользователя с тестовыми данными
        user = await service.create_user(
            telegram_id=telegram_id,
            username=None,
            first_name="User",
            last_name=None,
            language_code="ru",
        )
        logger.info(f"Created new Telegram user: {user.id} (telegram_id={telegram_id})")

    return user


@router.get("/subscriptions")
async def get_subscriptions(
    telegram_id: int = Depends(get_telegram_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Получает список подписок текущего пользователя.

    Args:
        telegram_id: ID пользователя Telegram
        db: Сессия базы данных

    Returns:
        Список подписок
    """
    user = await get_or_create_telegram_user(telegram_id, db)
    service = TelegramSubscriptionService(db)
    subscriptions = await service.get_active_subscriptions(user.id)

    return [
        {
            "id": str(sub.id),
            "user_id": str(sub.user_id),
            "city": sub.city,
            "rooms": sub.rooms,
            "price_min": sub.price_min,
            "price_max": sub.price_max,
            "currency": sub.currency,
            "price_per_m2_max": sub.price_per_m2_max,
            "floor_min": sub.floor_min,
            "floor_max": sub.floor_max,
            "notify_only_price_drop": sub.notify_only_price_drop,
            "exclude_deal_below_percent": sub.exclude_deal_below_percent,
            "is_active": sub.is_active,
            "created_at": sub.created_at.isoformat(),
            "updated_at": sub.updated_at.isoformat(),
        }
        for sub in subscriptions
    ]


@router.post("/subscriptions")
async def create_subscription(
    subscription_data: dict,
    telegram_id: int = Depends(get_telegram_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Создаёт новую подписку.

    Args:
        subscription_data: Данные подписки
        telegram_id: ID пользователя Telegram
        db: Сессия базы данных

    Returns:
        Созданная подписка

    Raises:
        HTTPException: При ошибках валидации
    """
    user = await get_or_create_telegram_user(telegram_id, db)
    service = TelegramSubscriptionService(db)

    # Проверяем лимит подписок
    existing = await service.get_active_subscriptions(user.id)
    if len(existing) >= MAX_SUBSCRIPTIONS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum subscriptions limit ({MAX_SUBSCRIPTIONS_PER_USER}) reached",
        )

    # Создаём подписку
    subscription = await service.create_subscription(
        user_id=user.id,
        city=subscription_data.get("city", "minsk"),
        rooms=subscription_data.get("rooms"),
        price_min=subscription_data.get("price_min"),
        price_max=subscription_data.get("price_max"),
        currency=subscription_data.get("currency", "usd"),
        price_per_m2_max=subscription_data.get("price_per_m2_max"),
        floor_min=subscription_data.get("floor_min"),
        floor_max=subscription_data.get("floor_max"),
        notify_only_price_drop=subscription_data.get("notify_only_price_drop", False),
        exclude_deal_below_percent=subscription_data.get("exclude_deal_below_percent"),
    )

    logger.info(f"Created subscription {subscription.id} for user {user.id}")

    return {
        "id": str(subscription.id),
        "user_id": str(subscription.user_id),
        "city": subscription.city,
        "rooms": subscription.rooms,
        "price_min": subscription.price_min,
        "price_max": subscription.price_max,
        "currency": subscription.currency,
        "price_per_m2_max": subscription.price_per_m2_max,
        "floor_min": subscription.floor_min,
        "floor_max": subscription.floor_max,
        "notify_only_price_drop": subscription.notify_only_price_drop,
        "exclude_deal_below_percent": subscription.exclude_deal_below_percent,
        "is_active": subscription.is_active,
        "created_at": subscription.created_at.isoformat(),
        "updated_at": subscription.updated_at.isoformat(),
    }


@router.put("/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: UUID,
    subscription_data: dict,
    telegram_id: int = Depends(get_telegram_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Обновляет подписку.

    Args:
        subscription_id: ID подписки
        subscription_data: Новые данные подписки
        telegram_id: ID пользователя Telegram
        db: Сессия базы данных

    Returns:
        Обновлённая подписка

    Raises:
        HTTPException: При ошибках
    """
    user = await get_or_create_telegram_user(telegram_id, db)
    service = TelegramSubscriptionService(db)

    # Проверяем, что подписка принадлежит пользователю
    subscription = await service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription belongs to another user",
        )

    # Обновляем подписку
    update_fields = {k: v for k, v in subscription_data.items() if v is not None}
    updated = await service.update_subscription(subscription_id, **update_fields)

    logger.info(f"Updated subscription {subscription_id}")

    return {
        "id": str(updated.id),
        "user_id": str(updated.user_id),
        "city": updated.city,
        "rooms": updated.rooms,
        "price_min": updated.price_min,
        "price_max": updated.price_max,
        "currency": updated.currency,
        "price_per_m2_max": updated.price_per_m2_max,
        "floor_min": updated.floor_min,
        "floor_max": updated.floor_max,
        "notify_only_price_drop": updated.notify_only_price_drop,
        "exclude_deal_below_percent": updated.exclude_deal_below_percent,
        "is_active": updated.is_active,
        "created_at": updated.created_at.isoformat(),
        "updated_at": updated.updated_at.isoformat(),
    }


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: UUID,
    telegram_id: int = Depends(get_telegram_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Удаляет подписку.

    Args:
        subscription_id: ID подписки
        telegram_id: ID пользователя Telegram
        db: Сессия базы данных

    Returns:
        Результат удаления

    Raises:
        HTTPException: При ошибках
    """
    user = await get_or_create_telegram_user(telegram_id, db)
    service = TelegramSubscriptionService(db)

    # Проверяем, что подписка принадлежит пользователю
    subscription = await service.get_subscription_by_id(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription belongs to another user",
        )

    # Удаляем подписку
    await service.delete_subscription(subscription_id)

    logger.info(f"Deleted subscription {subscription_id}")

    return {"success": True, "message": "Subscription deleted"}


@router.get("/webapp/config")
async def get_webapp_config(
    telegram_id: int = Depends(get_telegram_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Получает конфигурацию для Web App.

    Args:
        telegram_id: ID пользователя Telegram
        db: Сессия базы данных

    Returns:
        Конфигурация Web App
    """
    user = await get_or_create_telegram_user(telegram_id, db)
    service = TelegramSubscriptionService(db)
    subscriptions = await service.get_active_subscriptions(user.id)

    return {
        "cities": [{"code": code, "name": name} for code, name in CITY_NAMES.items()],
        "currencies": [
            {"code": "usd", "name": "USD", "symbol": "$"},
            {"code": "byn", "name": "BYN", "symbol": "Br"},
        ],
        "room_options": [
            {"value": "any", "label": "Любые"},
            {"value": "1", "label": "1 комната"},
            {"value": "2", "label": "2 комнаты"},
            {"value": "3", "label": "3 комнаты"},
            {"value": "4", "label": "4 комнаты"},
            {"value": "5", "label": "5+ комнат"},
        ],
        "max_subscriptions": MAX_SUBSCRIPTIONS_PER_USER,
        "current_subscription_count": len(subscriptions),
    }


@router.get("/stats")
async def get_stats(
    telegram_id: int = Depends(get_telegram_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Получает статистику уведомлений для пользователя.

    Args:
        telegram_id: ID пользователя Telegram
        db: Сессия базы данных

    Returns:
        Статистика уведомлений
    """
    user = await get_or_create_telegram_user(telegram_id, db)

    # Получаем статистику из логов уведомлений
    from datetime import datetime, timedelta

    # Все уведомления
    total_query = select(func.count(TelegramNotificationLog.id)).where(
        TelegramNotificationLog.user_id == user.id
    )
    total_result = await db.execute(total_query)
    total_notifications = total_result.scalar() or 0

    # Успешные
    success_query = select(func.count(TelegramNotificationLog.id)).where(
        TelegramNotificationLog.user_id == user.id,
        TelegramNotificationLog.status == "sent",
    )
    success_result = await db.execute(success_query)
    successful = success_result.scalar() or 0

    # Ошибки
    failed_query = select(func.count(TelegramNotificationLog.id)).where(
        TelegramNotificationLog.user_id == user.id,
        TelegramNotificationLog.status == "failed",
    )
    failed_result = await db.execute(failed_query)
    failed = failed_result.scalar() or 0

    return {
        "total_notifications": total_notifications,
        "successful": successful,
        "failed": failed,
        "duplicated": 0,  # TODO: добавить в логику
        "rate_limited": 0,  # TODO: добавить в логику
    }
