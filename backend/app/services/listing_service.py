from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.listing import Listing, ListingStatus, EventType, ListingHistory
from datetime import datetime, timedelta
from loguru import logger
from typing import Optional
import json


class ListingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_kufar_id(self, kufar_id: str) -> Listing | None:
        result = await self.db.execute(select(Listing).where(Listing.kufar_id == kufar_id))
        return result.scalar_one_or_none()

    async def _create_history_event(
        self,
        listing_id,
        event_type: EventType,
        price_before: Optional[int] = None,
        price_after: Optional[int] = None,
        changed_fields: Optional[dict] = None,
        snapshot: Optional[dict] = None,
    ):
        """Создать запись истории изменений"""
        history = ListingHistory(
            listing_id=listing_id,
            event_type=event_type,
            price_before=price_before,
            price_after=price_after,
            changed_fields=changed_fields,
            snapshot=snapshot,
        )
        self.db.add(history)

    async def upsert(self, listing_data: dict) -> tuple[Listing, str]:
        kufar_id = listing_data['kufar_id']
        existing = await self.get_by_kufar_id(kufar_id)

        if existing:
            # Сохраняем старые значения для истории
            old_price_usd = existing.price_usd
            old_price_byn = existing.price
            was_deleted = existing.status == ListingStatus.deleted

            # Собираем изменённые поля
            changed_fields = {}
            for key, value in listing_data.items():
                if key != 'kufar_id':
                    old_value = getattr(existing, key, None)
                    if old_value != value:
                        changed_fields[key] = [old_value, value]
                        setattr(existing, key, value)

            existing.last_seen_at = datetime.utcnow()

            # Восстанавливаем если было удалённым
            if was_deleted:
                existing.status = ListingStatus.active
                existing.deleted_at = None
                # Создаём событие восстановления
                await self._create_history_event(
                    listing_id=existing.id,
                    event_type=EventType.restored,
                    snapshot=json.loads(json.dumps(existing.__dict__, default=str, skipkeys=True)),
                )
                logger.info(f"Listing {kufar_id} restored after deletion")
            # Устанавливаем статус updated только если изменилась цена USD
            elif old_price_usd is not None and existing.price_usd is not None and old_price_usd != existing.price_usd:
                existing.status = ListingStatus.updated
                # Создаём событие изменения цены USD
                await self._create_history_event(
                    listing_id=existing.id,
                    event_type=EventType.price_changed,
                    price_before=old_price_usd,
                    price_after=existing.price_usd,
                    changed_fields=changed_fields if changed_fields else None,
                    snapshot=json.loads(json.dumps(existing.__dict__, default=str, skipkeys=True)),
                )
                logger.info(f"Price USD changed for {kufar_id}: {old_price_usd} -> {existing.price_usd}")
            # Изменилась цена BYN но не USD
            elif old_price_byn is not None and existing.price is not None and old_price_byn != existing.price:
                existing.status = ListingStatus.price_changed_byn
                # Создаём событие изменения цены BYN
                await self._create_history_event(
                    listing_id=existing.id,
                    event_type=EventType.price_changed_byn,
                    price_before=old_price_byn,
                    price_after=existing.price,
                    changed_fields=changed_fields if changed_fields else None,
                    snapshot=json.loads(json.dumps(existing.__dict__, default=str, skipkeys=True)),
                )
                logger.info(f"Price BYN changed for {kufar_id}: {old_price_byn} -> {existing.price} (USD unchanged)")
            else:
                # Оставляем статус active - никаких значимых изменений
                existing.status = ListingStatus.active
                # НЕ создаём событие истории для обычных изменений

            await self.db.commit()
            await self.db.refresh(existing)
            return existing, 'updated'
        else:
            # Create new
            new_listing = Listing(**listing_data)
            self.db.add(new_listing)
            await self.db.commit()
            await self.db.refresh(new_listing)
            
            # Создаём событие создания
            await self._create_history_event(
                listing_id=new_listing.id,
                event_type=EventType.created,
                snapshot=json.loads(json.dumps(new_listing.__dict__, default=str, skipkeys=True)),
            )
            logger.info(f"New listing created: {kufar_id}")
            
            return new_listing, 'created'

    async def upsert_listings(self, listings_data: list[dict], city: str) -> dict:
        """Массовое обновление/создание объявлений"""
        stats = {
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "restored": 0,
            "processed": 0,
        }

        kufar_ids = set()

        for listing_data in listings_data:
            try:
                listing, action = await self.upsert(listing_data)
                kufar_ids.add(listing.kufar_id)

                if action == 'created':
                    stats["created"] += 1
                elif action == 'updated':
                    stats["updated"] += 1
                    # Проверяем не было ли объявление удалённым
                    if hasattr(listing, '_was_deleted') and listing._was_deleted:
                        stats["restored"] += 1

                stats["processed"] += 1
            except Exception as e:
                logger.error(f"Error upserting listing: {e}")

        # Помечаем удалённые объявления
        if kufar_ids:
            deleted_count = await self.mark_deleted(kufar_ids, city)
            stats["deleted"] = deleted_count

        return stats

    async def mark_deleted(self, kufar_ids: set[str], city: str) -> int:
        result = await self.db.execute(
            select(Listing).where(
                and_(
                    Listing.kufar_id.not_in(kufar_ids),
                    Listing.city == city,
                    Listing.status.in_([ListingStatus.active, ListingStatus.new, ListingStatus.updated])
                )
            )
        )
        listings = result.scalars().all()

        for listing in listings:
            listing.status = ListingStatus.deleted
            listing.deleted_at = datetime.utcnow()
            # Создаём событие удаления
            await self._create_history_event(
                listing_id=listing.id,
                event_type=EventType.deleted,
                snapshot=json.loads(json.dumps(listing.__dict__, default=str, skipkeys=True)),
            )

        await self.db.commit()
        return len(listings)
