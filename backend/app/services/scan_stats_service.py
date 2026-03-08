"""
Сервис для управления статистикой сканирований по городам.
Используется для валидации аномалий при сканировании.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.listing import ScanStats
from datetime import datetime
from typing import Optional, List
from loguru import logger

# Минимальный порог объявлений для первого сканирования
# Если первое сканирование возвращает меньше этого значения - аномалия
MIN_FIRST_SCAN_LISTINGS = 10


class ScanStatsService:
    """Сервис для управления статистикой сканирований."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_city_stats(self, city: str) -> Optional[ScanStats]:
        """Получить статистику по городу."""
        result = await self.db.execute(select(ScanStats).where(ScanStats.city == city))
        return result.scalar_one_or_none()

    async def get_or_create_stats(self, city: str) -> ScanStats:
        """Получить или создать статистику по городу."""
        stats = await self.get_city_stats(city)
        if not stats:
            stats = ScanStats(city=city, recent_counts=[])
            self.db.add(stats)
            await self.db.commit()
            await self.db.refresh(stats)
        return stats

    async def _get_or_create_stats_no_commit(
        self, city: str, db_session: AsyncSession
    ) -> ScanStats:
        """
        Получить или создать статистику по городу без commit() - для использования в транзакции.

        Все изменения будут закоммичены внешним вызовом db_session.commit().

        Args:
            city: Код города
            db_session: Сессия БД для использования (внешняя транзакция)

        Returns:
            Объект ScanStats (новый или существующий)
        """
        query = select(ScanStats).where(ScanStats.city == city)
        result = await db_session.execute(query)
        stats = result.scalar_one_or_none()

        if not stats:
            stats = ScanStats(city=city, recent_counts=[])
            db_session.add(stats)
            # БЕЗ commit() - вызывающий код сам решит когда коммитить

        return stats

    async def update_stats(self, city: str, listings_count: int) -> ScanStats:
        """
        Обновить статистику по городу после успешного сканирования.

        Сохраняет последние 10 значений и вычисляет среднее.

        Args:
            city: Код города
            listings_count: Количество объявлений
        """
        stats = await self.get_or_create_stats(city)

        # Добавляем новое значение в историю
        recent_counts = stats.recent_counts or []
        recent_counts.append(listings_count)

        # Храним только последние 10 значений
        if len(recent_counts) > 10:
            recent_counts = recent_counts[-10:]

        stats.recent_counts = recent_counts

        # Вычисляем среднее
        if recent_counts:
            stats.avg_listings_count = sum(recent_counts) // len(recent_counts)
        else:
            stats.avg_listings_count = 0

        stats.last_updated = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(stats)

        logger.info(
            f"Scan stats updated for {city}: {listings_count} listings, "
            f"avg: {stats.avg_listings_count}, history: {recent_counts}"
        )

        return stats

    async def update_stats_no_commit(
        self, city: str, listings_count: int, db_session: AsyncSession
    ) -> ScanStats:
        """
        Обновить статистику по городу без commit() - для использования в единой транзакции.

        Все изменения будут закоммичены внешним вызовом db_session.commit().

        Args:
            city: Код города
            listings_count: Количество объявлений
            db_session: Сессия БД для использования (внешняя транзакция)

        Returns:
            Обновлённый объект ScanStats
        """
        # Получаем или создаём статистику используя переданную сессию
        query = select(ScanStats).where(ScanStats.city == city)
        result = await db_session.execute(query)
        stats = result.scalar_one_or_none()

        if not stats:
            stats = ScanStats(city=city, recent_counts=[])
            db_session.add(stats)

        # Добавляем новое значение в историю
        recent_counts = stats.recent_counts or []
        recent_counts.append(listings_count)

        # Храним только последние 10 значений
        if len(recent_counts) > 10:
            recent_counts = recent_counts[-10:]

        stats.recent_counts = recent_counts

        # Вычисляем среднее
        if recent_counts:
            stats.avg_listings_count = sum(recent_counts) // len(recent_counts)
        else:
            stats.avg_listings_count = 0

        stats.last_updated = datetime.utcnow()

        logger.info(
            f"Scan stats updated for {city}: {listings_count} listings, "
            f"avg: {stats.avg_listings_count}, history: {recent_counts}"
        )

        return stats

    async def validate_listings_count(
        self,
        city: str,
        current_count: int,
        use_lock: bool = True,
    ) -> tuple[bool, str, int]:
        """
        Проверить количество объявлений на аномалии с блокировкой строки.

        Использует SELECT FOR UPDATE для предотвращения гонок данных между
        параллельными сканированиями одного города.

        Args:
            city: Код города
            current_count: Текущее количество объявлений
            use_lock: Использовать блокировку SELECT FOR UPDATE (по умолчанию True)

        Returns:
            Кортеж: (is_valid, message, expected_count)

        Если получено < 90% от среднего → аномалия.
        Если статистики ещё нет → проверяем на 0 объявлений.
        """
        session = self.db

        # Блокируем строку для предотвращения гонок между сканированиями
        # with_for_update() устанавливает блокировку уровня строки в PostgreSQL
        # skip_locked=True предотвращает deadlock при параллельных сканированиях
        # Используется только когда use_lock=True
        if use_lock:
            # Сначала пробуем получить или создать статистику без commit()
            # Это гарантирует что запись существует перед блокировкой
            await self._get_or_create_stats_no_commit(city, session)

            # Применяем блокировку для валидации
            query = select(ScanStats).where(ScanStats.city == city)
            query = query.with_for_update(
                skip_locked=True
            )  # PostgreSQL FOR UPDATE с skip_locked
            result = await session.execute(query)
            stats = result.scalar_one_or_none()
        else:
            query = select(ScanStats).where(ScanStats.city == city)
            result = await session.execute(query)
            stats = result.scalar_one_or_none()

        if not stats or not stats.recent_counts or len(stats.recent_counts) < 3:
            # Первое сканирование или недостаточно данных
            if current_count == 0:
                logger.warning(
                    f"[{city}] First scan returned 0 listings — possible API error"
                )
                return (
                    False,
                    "⚠️ Первое сканирование: 0 объявлений — возможна ошибка API",
                    0,
                )

            # Проверка минимального порога для первого сканирования
            if current_count < MIN_FIRST_SCAN_LISTINGS:
                logger.warning(
                    f"[{city}] First scan returned {current_count} listings (< {MIN_FIRST_SCAN_LISTINGS})"
                )
                return (
                    False,
                    f"⚠️ Первое сканирование: {current_count} < {MIN_FIRST_SCAN_LISTINGS} (минимальный порог)",
                    0,
                )

            logger.info(
                f"[{city}] First scan or insufficient history: {current_count} listings"
            )
            return True, "Первое сканирование — валидация отключена", 0

        expected_count = stats.avg_listings_count
        threshold = expected_count * 0.9  # 90% порог

        if current_count < threshold:
            message = (
                f"⚠️ Аномалия: получено {current_count} объявлений, "
                f"ожидалось ~{expected_count} (менее 90% от среднего, порог {threshold:.0f})"
            )
            logger.warning(message)
            return False, message, expected_count

        logger.info(
            f"Validation passed for {city}: {current_count} listings, "
            f"expected ~{expected_count}"
        )
        return True, "OK", expected_count

    async def reset_stats(self, city: str):
        """Сбросить статистику по городу."""
        stats = await self.get_city_stats(city)
        if stats:
            stats.recent_counts = []
            stats.avg_listings_count = 0
            stats.last_updated = datetime.utcnow()
            await self.db.commit()
            logger.info(f"Scan stats reset for {city}")
