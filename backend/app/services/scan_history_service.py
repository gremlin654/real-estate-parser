from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.listing import ScanHistory
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
from loguru import logger


class ScanHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_scan_record(
        self,
        city: str,
        city_name: str,
        trigger_type: str = 'manual'
    ) -> ScanHistory:
        """Создание записи истории сканирования."""
        logger.info(f"Creating scan record for {city}, trigger: {trigger_type}")
        scan = ScanHistory(
            city=city,
            city_name=city_name,
            trigger_type=trigger_type,
            status='running'
        )
        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)
        logger.info(f"Scan record created with ID: {scan.id}")
        return scan

    async def update_scan_record(
        self,
        scan_id: str,
        listings_fetched: int = None,
        listings_created: int = None,
        listings_updated: int = None,
        listings_deleted: int = None,
        pages_scraped: int = None,
        errors: list = None
    ):
        """Обновление записи истории сканирования."""
        logger.info(f"Updating scan record {scan_id}")
        scan = await self.get_scan_record_by_id(scan_id)
        if not scan:
            logger.warning(f"Scan record {scan_id} not found for update")
            return

        if listings_fetched is not None:
            scan.listings_fetched = listings_fetched
        if listings_created is not None:
            scan.listings_created = listings_created
        if listings_updated is not None:
            scan.listings_updated = listings_updated
        if listings_deleted is not None:
            scan.listings_deleted = listings_deleted
        if pages_scraped is not None:
            scan.pages_scraped = pages_scraped
        if errors is not None:
            scan.errors = errors

        await self.db.commit()
        logger.info(f"Scan record {scan_id} updated successfully")

    async def complete_scan_record(
        self,
        scan_id: str,
        status: str = 'completed',
        error_message: str = None,
        listings_created: int = None,
        listings_updated: int = None,
        listings_changed_byn: int = None,
        listings_deleted: int = None,
        listings_restored: int = None,
        listings_unchanged: int = None,
        pages_scraped: int = None,
        duration_seconds: int = None
    ):
        """Завершение записи истории сканирования."""
        logger.info(f"Completing scan record {scan_id} with status: {status}")
        scan = await self.get_scan_record_by_id(scan_id)
        if not scan:
            logger.warning(f"Scan record {scan_id} not found for completion")
            return

        scan.status = status
        scan.completed_at = datetime.utcnow()
        scan.error_message = error_message

        # Сохранение статистики если предоставлена
        if listings_created is not None:
            scan.listings_created = listings_created
        if listings_updated is not None:
            scan.listings_updated = listings_updated
        if listings_changed_byn is not None:
            scan.listings_changed_byn = listings_changed_byn
        if listings_deleted is not None:
            scan.listings_deleted = listings_deleted
        if listings_restored is not None:
            scan.listings_restored = listings_restored
        if listings_unchanged is not None:
            scan.listings_unchanged = listings_unchanged
        if pages_scraped is not None:
            scan.pages_scraped = pages_scraped
        if duration_seconds is not None:
            scan.duration_seconds = duration_seconds
        elif scan.started_at:
            # Вычислить длительность если не предоставлена
            scan.duration_seconds = int((scan.completed_at - scan.started_at).total_seconds())

        await self.db.commit()
        logger.info(f"Scan record {scan_id} completed with status: {status}, duration: {scan.duration_seconds}s")

    async def get_scan_record_by_id(self, scan_id) -> Optional[ScanHistory]:
        """Получение записи истории по ID."""
        from uuid import UUID
        
        # Преобразуем в UUID если это строка
        if isinstance(scan_id, str):
            try:
                uuid_id = UUID(scan_id)
            except ValueError:
                return None
        else:
            # Уже UUID (например, от asyncpg)
            uuid_id = scan_id

        result = await self.db.execute(select(ScanHistory).where(ScanHistory.id == uuid_id))
        return result.scalar_one_or_none()

    async def get_scan_history(
        self,
        limit: int = 50,
        offset: int = 0,
        city: str = None,
        status: str = None
    ) -> List[ScanHistory]:
        """Получение истории сканирований с пагинацией и фильтрами."""
        query = select(ScanHistory).order_by(ScanHistory.started_at.desc())
        
        if city:
            query = query.where(ScanHistory.city == city)
        if status:
            query = query.where(ScanHistory.status == status)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_scan_history_paginated(
        self,
        page: int = 1,
        size: int = 20,
        city: str = None,
        status: str = None,
        trigger_type: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> Tuple[List[ScanHistory], int]:
        """
        Получение пагинированной истории сканирований.
        
        Возвращает кортеж: (список записей, общее количество)
        """
        # Базовый запрос для подсчета
        count_query = select(func.count(ScanHistory.id))
        
        # Базовый запрос для данных
        data_query = select(ScanHistory).order_by(ScanHistory.started_at.desc())
        
        # Применяем фильтры
        if city:
            count_query = count_query.where(ScanHistory.city == city)
            data_query = data_query.where(ScanHistory.city == city)
        
        if status:
            count_query = count_query.where(ScanHistory.status == status)
            data_query = data_query.where(ScanHistory.status == status)
        
        if trigger_type:
            count_query = count_query.where(ScanHistory.trigger_type == trigger_type)
            data_query = data_query.where(ScanHistory.trigger_type == trigger_type)
        
        if date_from:
            count_query = count_query.where(ScanHistory.started_at >= date_from)
            data_query = data_query.where(ScanHistory.started_at >= date_from)
        
        if date_to:
            count_query = count_query.where(ScanHistory.started_at <= date_to)
            data_query = data_query.where(ScanHistory.started_at <= date_to)
        
        # Получаем общее количество
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Применяем пагинацию
        offset = (page - 1) * size
        data_query = data_query.limit(size).offset(offset)
        
        # Получаем данные
        data_result = await self.db.execute(data_query)
        items = data_result.scalars().all()
        
        return items, total

    async def get_scan_history_count(
        self,
        city: str = None,
        status: str = None,
        trigger_type: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> int:
        """Получение общего количества записей с фильтрами."""
        query = select(func.count(ScanHistory.id))
        
        if city:
            query = query.where(ScanHistory.city == city)
        if status:
            query = query.where(ScanHistory.status == status)
        if trigger_type:
            query = query.where(ScanHistory.trigger_type == trigger_type)
        if date_from:
            query = query.where(ScanHistory.started_at >= date_from)
        if date_to:
            query = query.where(ScanHistory.started_at <= date_to)
        
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_summary(self, city: str = None) -> dict:
        """Получение сводной статистики."""
        base_query = select(func.count(ScanHistory.id))
        
        if city:
            base_query = base_query.where(ScanHistory.city == city)
        
        # Общее количество
        total_query = base_query
        result = await self.db.execute(total_query)
        total = result.scalar() or 0
        
        # Завершенные
        completed_query = base_query.where(ScanHistory.status == 'completed')
        result = await self.db.execute(completed_query)
        completed = result.scalar() or 0
        
        # Ошибки
        failed_query = base_query.where(ScanHistory.status == 'error')
        result = await self.db.execute(failed_query)
        failed = result.scalar() or 0
        
        # Активные
        running_query = base_query.where(ScanHistory.status == 'running')
        result = await self.db.execute(running_query)
        running = result.scalar() or 0
        
        # Всего объявлений
        listings_query = select(func.sum(ScanHistory.listings_fetched))
        if city:
            listings_query = listings_query.where(ScanHistory.city == city)
        result = await self.db.execute(listings_query)
        total_listings = result.scalar() or 0
        
        return {
            'total_scans': total,
            'completed_scans': completed,
            'failed_scans': failed,
            'running_scans': running,
            'total_listings_fetched': total_listings,
        }
