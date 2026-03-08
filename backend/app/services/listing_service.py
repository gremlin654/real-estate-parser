from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from app.models.listing import Listing, ListingStatus, EventType, ListingHistory
from datetime import datetime, timedelta
from loguru import logger
from typing import Optional, Set
import json


class ListingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_kufar_id(self, kufar_id: str) -> Optional[Listing]:
        result = await self.db.execute(
            select(Listing).where(Listing.kufar_id == kufar_id)
        )
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
        kufar_id = listing_data["kufar_id"]
        existing = await self.get_by_kufar_id(kufar_id)

        if existing:
            # Сохраняем старые значения для истории
            old_price_usd = existing.price_usd
            old_price_byn = existing.price
            was_deleted = existing.status == ListingStatus.deleted

            # Собираем изменённые поля
            changed_fields = {}
            for key, value in listing_data.items():
                if key != "kufar_id":
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
                    snapshot=json.loads(
                        json.dumps(existing.__dict__, default=str, skipkeys=True)
                    ),
                )
                logger.info(f"Listing {kufar_id} restored after deletion")
                await self.db.commit()
                await self.db.refresh(existing)
                return existing, "restored"
            # Устанавливаем статус updated только если изменилась цена USD
            elif (
                old_price_usd is not None
                and existing.price_usd is not None
                and old_price_usd != existing.price_usd
            ):
                existing.status = ListingStatus.updated
                # Создаём событие изменения цены USD
                await self._create_history_event(
                    listing_id=existing.id,
                    event_type=EventType.price_changed,
                    price_before=old_price_usd,
                    price_after=existing.price_usd,
                    changed_fields=changed_fields if changed_fields else None,
                    snapshot=json.loads(
                        json.dumps(existing.__dict__, default=str, skipkeys=True)
                    ),
                )
                logger.info(
                    f"Price USD changed for {kufar_id}: {old_price_usd} -> {existing.price_usd}"
                )
                await self.db.commit()
                await self.db.refresh(existing)
                return existing, "updated"
            # Изменилась цена BYN но не USD
            elif (
                old_price_byn is not None
                and existing.price is not None
                and old_price_byn != existing.price
            ):
                existing.status = ListingStatus.price_changed_byn
                # Создаём событие изменения цены BYN
                await self._create_history_event(
                    listing_id=existing.id,
                    event_type=EventType.price_changed_byn,
                    price_before=old_price_byn,
                    price_after=existing.price,
                    changed_fields=changed_fields if changed_fields else None,
                    snapshot=json.loads(
                        json.dumps(existing.__dict__, default=str, skipkeys=True)
                    ),
                )
                logger.info(
                    f"Price BYN changed for {kufar_id}: {old_price_byn} -> {existing.price} (USD unchanged)"
                )
                await self.db.commit()
                await self.db.refresh(existing)
                return existing, "changed_byn"
            else:
                # Оставляем статус active - никаких значимых изменений
                existing.status = ListingStatus.active
                # НЕ создаём событие истории для обычных изменений
                await self.db.commit()
                await self.db.refresh(existing)
                return existing, "unchanged"
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
                snapshot=json.loads(
                    json.dumps(new_listing.__dict__, default=str, skipkeys=True)
                ),
            )
            logger.info(f"New listing created: {kufar_id}")

            return new_listing, "created"

    async def upsert_listings_no_mark_deleted(
        self, listings_data: list[dict], city: str
    ) -> dict:
        """
        Массовое обновление/создание объявлений БЕЗ маркировки удалённых.
        
        Mark deleted вызывается отдельно в scheduler после валидации количества.
        Возвращает статистику по операциям.
        """
        stats = {
            "created": 0,
            "updated": 0,
            "changed_byn": 0,
            "deleted": 0,
            "restored": 0,
            "unchanged": 0,
            "processed": 0,
        }

        kufar_ids = set()

        for listing_data in listings_data:
            try:
                listing, action = await self.upsert(listing_data)
                kufar_ids.add(listing.kufar_id)

                if action == "created":
                    stats["created"] += 1
                elif action == "updated":
                    stats["updated"] += 1
                elif action == "changed_byn":
                    stats["changed_byn"] += 1
                elif action == "restored":
                    stats["restored"] += 1
                elif action == "unchanged":
                    stats["unchanged"] += 1

                stats["processed"] += 1
            except Exception as e:
                logger.error(f"Error upserting listing: {e}")
                raise  # Пробрасываем ошибку вверх для отката транзакции

        return stats

    async def upsert_listings(
        self, listings_data: list[dict], city: str, mark_deleted_externally: bool = False
    ) -> dict:
        """
        Массовое обновление/создание объявлений.
        
        Args:
            listings_data: Список данных объявлений
            city: Город сканирования
            mark_deleted_externally: Если True, mark_deleted вызывается отдельно в scheduler.
                                     Если False, mark_deleted вызывается здесь (старое поведение).
        
        Returns:
            Статистика по операциям
        """
        stats = await self.upsert_listings_no_mark_deleted(listings_data, city)
        
        # Помечаем удалённые объявления только если не вызывается externall
        if not mark_deleted_externally and stats["processed"] > 0:
            kufar_ids = set(item["kufar_id"] for item in listings_data)
            deleted_count = await self.mark_deleted(kufar_ids, city)
            stats["deleted"] = deleted_count

        return stats

    async def upsert_listings_transaction(
        self, listings_data: list[dict], city: str
    ) -> dict:
        """
        Массовое обновление/создание объявлений в транзакции.

        При любой ошибке происходит откат всех изменений.
        Mark deleted НЕ вызывается - только валидация и upsert.

        Args:
            listings_data: Список данных объявлений
            city: Город сканирования

        Returns:
            Статистика по операциям

        Raises:
            SQLAlchemyError: При ошибке базы данных
            Exception: При других ошибках
        """
        stats = {
            "created": 0,
            "updated": 0,
            "changed_byn": 0,
            "restored": 0,
            "unchanged": 0,
            "processed": 0,
        }

        kufar_ids = set()

        try:
            for listing_data in listings_data:
                try:
                    listing, action = await self.upsert(listing_data)
                    kufar_ids.add(listing.kufar_id)

                    if action == "created":
                        stats["created"] += 1
                    elif action == "updated":
                        stats["updated"] += 1
                    elif action == "changed_byn":
                        stats["changed_byn"] += 1
                    elif action == "restored":
                        stats["restored"] += 1
                    elif action == "unchanged":
                        stats["unchanged"] += 1

                    stats["processed"] += 1
                except Exception as e:
                    logger.error(f"Error upserting listing {listing_data.get('kufar_id')}: {e}")
                    raise  # Пробрасываем для отката транзакции

            # Флаг успешного завершения для внешнего использования
            stats["success"] = True
            stats["kufar_ids"] = kufar_ids

            return stats

        except SQLAlchemyError as e:
            logger.error(f"Database error during upsert: {e}")
            await self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error during transaction upsert: {e}")
            await self.db.rollback()
            raise

    async def upsert_listings_no_commit(
        self, listings_data: list[dict], city: str, db_session: AsyncSession
    ) -> dict:
        """
        Массовое обновление/создание объявлений без commit() - для использования в единой транзакции.

        Все изменения будут закоммичены внешним вызовом db_session.commit().
        Mark deleted НЕ вызывается - вызывается отдельно через mark_deleted_no_commit().

        Args:
            listings_data: Список данных объявлений
            city: Город сканирования
            db_session: Сессия БД для использования (внешняя транзакция)

        Returns:
            Статистика по операциям (created, updated, changed_byn, restored, unchanged, processed, kufar_ids)

        Raises:
            SQLAlchemyError: При ошибке базы данных
            Exception: При других ошибках
        """
        stats = {
            "created": 0,
            "updated": 0,
            "changed_byn": 0,
            "restored": 0,
            "unchanged": 0,
            "processed": 0,
        }

        kufar_ids = set()

        # Временный сервис для использования переданной сессии
        temp_service = ListingService(db_session)

        for listing_data in listings_data:
            try:
                listing, action = await temp_service.upsert_no_commit_inner(listing_data)
                kufar_ids.add(listing.kufar_id)

                if action == "created":
                    stats["created"] += 1
                elif action == "updated":
                    stats["updated"] += 1
                elif action == "changed_byn":
                    stats["changed_byn"] += 1
                elif action == "restored":
                    stats["restored"] += 1
                elif action == "unchanged":
                    stats["unchanged"] += 1

                stats["processed"] += 1
            except Exception as e:
                logger.error(f"Error upserting listing {listing_data.get('kufar_id')}: {e}")
                raise  # Пробрасываем ошибку для отката транзакции

        stats["kufar_ids"] = kufar_ids
        return stats

    async def upsert_no_commit_inner(self, listing_data: dict) -> tuple[Listing, str]:
        """
        Внутренний метод upsert без commit() - для использования в upsert_listings_no_commit().
        
        Использует self.db сессию которая должна быть передана извне.
        """
        kufar_id = listing_data["kufar_id"]
        existing = await self.get_by_kufar_id(kufar_id)

        if existing:
            # Сохраняем старые значения для истории
            old_price_usd = existing.price_usd
            old_price_byn = existing.price
            was_deleted = existing.status == ListingStatus.deleted

            # Собираем изменённые поля
            changed_fields = {}
            for key, value in listing_data.items():
                if key != "kufar_id":
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
                    snapshot=json.loads(
                        json.dumps(existing.__dict__, default=str, skipkeys=True)
                    ),
                )
                logger.info(f"Listing {kufar_id} restored after deletion")
                # БЕЗ commit()
                return existing, "restored"
            # Устанавливаем статус updated только если изменилась цена USD
            elif (
                old_price_usd is not None
                and existing.price_usd is not None
                and old_price_usd != existing.price_usd
            ):
                existing.status = ListingStatus.updated
                # Создаём событие изменения цены USD
                await self._create_history_event(
                    listing_id=existing.id,
                    event_type=EventType.price_changed,
                    price_before=old_price_usd,
                    price_after=existing.price_usd,
                    changed_fields=changed_fields if changed_fields else None,
                    snapshot=json.loads(
                        json.dumps(existing.__dict__, default=str, skipkeys=True)
                    ),
                )
                logger.info(
                    f"Price USD changed for {kufar_id}: {old_price_usd} -> {existing.price_usd}"
                )
                # БЕЗ commit()
                return existing, "updated"
            # Изменилась цена BYN но не USD
            elif (
                old_price_byn is not None
                and existing.price is not None
                and old_price_byn != existing.price
            ):
                existing.status = ListingStatus.price_changed_byn
                # Создаём событие изменения цены BYN
                await self._create_history_event(
                    listing_id=existing.id,
                    event_type=EventType.price_changed_byn,
                    price_before=old_price_byn,
                    price_after=existing.price,
                    changed_fields=changed_fields if changed_fields else None,
                    snapshot=json.loads(
                        json.dumps(existing.__dict__, default=str, skipkeys=True)
                    ),
                )
                logger.info(
                    f"Price BYN changed for {kufar_id}: {old_price_byn} -> {existing.price} (USD unchanged)"
                )
                # БЕЗ commit()
                return existing, "changed_byn"
            else:
                # Оставляем статус active - никаких значимых изменений
                existing.status = ListingStatus.active
                # НЕ создаём событие истории для обычных изменений
                # БЕЗ commit()
                return existing, "unchanged"
        else:
            # Create new
            new_listing = Listing(**listing_data)
            self.db.add(new_listing)
            # БЕЗ commit() но делаем flush для получения id
            await self.db.flush()

            # Создаём событие создания (теперь new_listing.id не None)
            await self._create_history_event(
                listing_id=new_listing.id,
                event_type=EventType.created,
                snapshot=json.loads(
                    json.dumps(new_listing.__dict__, default=str, skipkeys=True)
                ),
            )
            logger.info(f"New listing created: {kufar_id}")

            return new_listing, "created"

    async def mark_deleted_no_commit(
        self, kufar_ids: Set[str], city: str, db_session: AsyncSession
    ) -> int:
        """
        Пометить отсутствующие объявления как удалённые без commit() - для использования в единой транзакции.

        Все изменения будут закоммичены внешним вызовом db_session.commit().

        Args:
            kufar_ids: Множество kufar_id объявлений которые существуют в API
            city: Город сканирования
            db_session: Сессия БД для использования (внешняя транзакция)

        Returns:
            Количество помеченных как удалённые
        """
        # Временный сервис для использования переданной сессии
        temp_service = ListingService(db_session)
        
        result = await db_session.execute(
            select(Listing).where(
                and_(
                    Listing.kufar_id.not_in(kufar_ids),
                    Listing.city == city,
                    Listing.status.in_(
                        [ListingStatus.active, ListingStatus.new, ListingStatus.updated]
                    ),
                )
            )
        )
        listings = result.scalars().all()

        for listing in listings:
            listing.status = ListingStatus.deleted
            listing.deleted_at = datetime.utcnow()
            # Создаём событие удаления
            await temp_service._create_history_event(
                listing_id=listing.id,
                event_type=EventType.deleted,
                snapshot=json.loads(
                    json.dumps(listing.__dict__, default=str, skipkeys=True)
                ),
            )

        # БЕЗ commit()
        return len(listings)

    async def mark_deleted(self, kufar_ids: Set[str], city: str) -> int:
        result = await self.db.execute(
            select(Listing).where(
                and_(
                    Listing.kufar_id.not_in(kufar_ids),
                    Listing.city == city,
                    Listing.status.in_(
                        [ListingStatus.active, ListingStatus.new, ListingStatus.updated]
                    ),
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
                snapshot=json.loads(
                    json.dumps(listing.__dict__, default=str, skipkeys=True)
                ),
            )

        await self.db.commit()
        return len(listings)
