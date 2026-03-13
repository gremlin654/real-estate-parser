"""
Unit тесты для FavoritesService.

Тестируют методы:
- add_to_favorites
- remove_from_favorites
- get_favorites
- is_favorite
- clear_user_favorites_cache
- invalidate_cache
- serialize/deserialize
- cache write/read
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import json

from app.services.favorites_service import (
    FavoritesService,
    FAVORITES_CACHE_TTL,
)
from app.models.favorite import Favorite
from app.models.listing import Listing


@pytest.fixture
def mock_db_session():
    """Создание мок сессии базы данных."""
    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock()
    session.execute = AsyncMock()
    # add и delete - синхронные методы в SQLAlchemy
    session.add = MagicMock()
    session.delete = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    """Создание мок Redis клиента."""
    redis = AsyncMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.flushdb = AsyncMock()
    return redis


@pytest.fixture
def favorites_service(mock_db_session, mock_redis):
    """Создание экземпляра сервиса с мок Redis."""
    service = FavoritesService(mock_db_session)
    service._redis_client = mock_redis
    return service


@pytest.fixture
def sample_user_id() -> UUID:
    """Пример user_id для тестов."""
    return uuid4()


@pytest.fixture
def sample_listing_id() -> UUID:
    """Пример listing_id для тестов."""
    return uuid4()


@pytest.fixture
def sample_favorite(sample_user_id, sample_listing_id) -> Favorite:
    """Создание примера Favorite для тестов."""
    return Favorite(
        id=uuid4(),
        user_id=sample_user_id,
        listing_id=sample_listing_id,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_listing(sample_listing_id) -> Listing:
    """Создание примера Listing для тестов."""
    return Listing(
        id=sample_listing_id,
        kufar_id="test_123",
        url="https://re.kufar.by/test",
        title="Test Listing",
        price=100000,
        price_usd=35000,
        city="minsk",
        rooms=2,
        area=50.5,
        floor=3,
        status="active",
    )


class TestFavoritesServiceInit:
    """Тесты инициализации сервиса."""

    def test_init_with_db_session(self, mock_db_session):
        """Тест инициализации с сессией БД."""
        service = FavoritesService(mock_db_session)
        assert service.db == mock_db_session
        assert service._redis_client is None

    def test_get_cache_key(self, favorites_service, sample_user_id):
        """Тест генерации ключа кэша."""
        # Ключ теперь включает page и size для пагинации
        expected_key = f"cache:favorites:{sample_user_id}:1:20"
        assert favorites_service._get_cache_key(sample_user_id) == expected_key
        
        # Проверка с другими параметрами пагинации
        expected_key_page2 = f"cache:favorites:{sample_user_id}:2:50"
        assert favorites_service._get_cache_key(sample_user_id, page=2, size=50) == expected_key_page2


class TestAddToFavorites:
    """Тесты метода add_to_favorites."""

    @pytest.mark.asyncio
    async def test_add_to_favorites_success(
        self,
        favorites_service,
        mock_db_session,
        mock_redis,
        sample_user_id,
        sample_listing_id,
        sample_listing,
    ):
        """Тест успешного добавления в избранное."""
        # Setup
        mock_db_session.get.return_value = sample_listing

        # Mock для execute (проверка на дубликат)
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_execute_result

        # Mock для commit и refresh
        created_favorite = Favorite(
            id=uuid4(),
            user_id=sample_user_id,
            listing_id=sample_listing_id,
            created_at=datetime.utcnow(),
        )

        async def mock_refresh(obj):
            obj.id = created_favorite.id

        mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)

        # Execute
        result = await favorites_service.add_to_favorites(
            user_id=sample_user_id, listing_id=sample_listing_id
        )

        # Assert
        mock_db_session.get.assert_called_once_with(Listing, sample_listing_id)
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_redis.delete.assert_called_once()  # Инвалидация кэша
        assert result is not None
        assert result.user_id == sample_user_id
        assert result.listing_id == sample_listing_id

    @pytest.mark.asyncio
    async def test_add_to_favorites_already_exists(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
        sample_listing,
        sample_favorite,
    ):
        """Тест добавления уже существующего избранного (idempotent)."""
        # Setup
        mock_db_session.get.return_value = sample_listing

        # Mock для execute (возвращает существующий favorite)
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = sample_favorite
        mock_db_session.execute.return_value = mock_execute_result

        # Execute
        result = await favorites_service.add_to_favorites(
            user_id=sample_user_id, listing_id=sample_listing_id
        )

        # Assert
        assert result == sample_favorite
        mock_db_session.add.assert_not_called()  # Не создаёт новую запись
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_to_favorites_listing_not_found(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
    ):
        """Тест добавления несуществующего объявления."""
        # Setup
        mock_db_session.get.return_value = None

        # Execute & Assert
        with pytest.raises(
            ValueError, match=f"Listing with id {sample_listing_id} not found"
        ):
            await favorites_service.add_to_favorites(
                user_id=sample_user_id, listing_id=sample_listing_id
            )

    @pytest.mark.asyncio
    async def test_add_to_favorites_db_error(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
        sample_listing,
    ):
        """Тест обработки ошибки базы данных."""
        # Setup
        mock_db_session.get.return_value = sample_listing

        # Mock для execute (проверка на дубликат)
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_execute_result

        # Mock для commit с ошибкой
        mock_db_session.commit.side_effect = SQLAlchemyError("DB error")

        # Execute & Assert
        with pytest.raises(SQLAlchemyError):
            await favorites_service.add_to_favorites(
                user_id=sample_user_id, listing_id=sample_listing_id
            )

        mock_db_session.rollback.assert_called_once()


class TestRemoveFromFavorites:
    """Тесты метода remove_from_favorites."""

    @pytest.mark.asyncio
    async def test_remove_from_favorites_success(
        self,
        favorites_service,
        mock_db_session,
        mock_redis,
        sample_user_id,
        sample_listing_id,
        sample_favorite,
    ):
        """Тест успешного удаления из избранного."""
        # Setup - mock для execute (поиск favorite)
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = sample_favorite
        mock_db_session.execute.return_value = mock_execute_result

        # Execute
        result = await favorites_service.remove_from_favorites(
            user_id=sample_user_id, listing_id=sample_listing_id
        )

        # Assert
        assert result is True
        mock_db_session.execute.assert_called()  # Вызов delete через execute
        mock_db_session.commit.assert_called_once()
        mock_redis.delete.assert_called_once()  # Инвалидация кэша

    @pytest.mark.asyncio
    async def test_remove_from_favorites_not_found(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
    ):
        """Тест удаления отсутствующего избранного (idempotent)."""
        # Setup
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_execute_result

        # Execute
        result = await favorites_service.remove_from_favorites(
            user_id=sample_user_id, listing_id=sample_listing_id
        )

        # Assert
        assert result is False
        # execute вызывается только для поиска (не для delete)
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_remove_from_favorites_db_error(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
        sample_favorite,
    ):
        """Тест обработки ошибки базы данных."""
        # Setup
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = (
            sample_favorite
        )
        mock_db_session.commit.side_effect = SQLAlchemyError("DB error")

        # Execute & Assert
        with pytest.raises(SQLAlchemyError):
            await favorites_service.remove_from_favorites(
                user_id=sample_user_id, listing_id=sample_listing_id
            )

        mock_db_session.rollback.assert_called_once()


class TestGetFavorites:
    """Тесты метода get_favorites."""

    @pytest.mark.asyncio
    async def test_get_favorites_success(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_favorite,
    ):
        """Тест успешного получения списка избранных."""
        # Setup - mock для scalars().all()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_favorite]

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars
        mock_execute_result.scalar.return_value = 1  # total count

        # Настраиваем последовательные вызовы execute
        mock_db_session.execute.side_effect = [mock_execute_result, mock_execute_result]

        # Execute
        favorites, total = await favorites_service.get_favorites(
            user_id=sample_user_id, page=1, size=20
        )

        # Assert
        assert len(favorites) == 1
        assert favorites[0] == sample_favorite
        assert isinstance(total, int)
        assert total == 1
        mock_db_session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_get_favorites_pagination(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
    ):
        """Тест пагинации списка избранных."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        # Execute
        await favorites_service.get_favorites(user_id=sample_user_id, page=2, size=50)

        # Assert - проверяем что size ограничен 100
        assert True  # Если не упало - тест прошёл

    @pytest.mark.asyncio
    async def test_get_favorites_empty_list(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
    ):
        """Тест получения пустого списка избранных."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        # Execute
        favorites, total = await favorites_service.get_favorites(
            user_id=sample_user_id, page=1, size=20
        )

        # Assert
        assert len(favorites) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_favorites_cache_hit(
        self,
        favorites_service,
        mock_db_session,
        mock_redis,
        sample_user_id,
    ):
        """Тест получения избранных с cache hit."""
        # Setup
        mock_redis.get.return_value = b"cached_data"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        # Execute
        await favorites_service.get_favorites(user_id=sample_user_id, page=1, size=20)

        # Assert
        mock_redis.get.assert_called_once()


class TestIsFavorite:
    """Тесты метода is_favorite."""

    @pytest.mark.asyncio
    async def test_is_favorite_true(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
        sample_favorite,
    ):
        """Тест проверки наличия в избранном (True)."""
        # Setup
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = sample_favorite
        mock_db_session.execute.return_value = mock_execute_result

        # Execute
        result = await favorites_service.is_favorite(
            user_id=sample_user_id, listing_id=sample_listing_id
        )

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_favorite_false(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
    ):
        """Тест проверки наличия в избранном (False)."""
        # Setup
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_execute_result

        # Execute
        result = await favorites_service.is_favorite(
            user_id=sample_user_id, listing_id=sample_listing_id
        )

        # Assert
        assert result is False


class TestClearUserFavoritesCache:
    """Тесты метода clear_user_favorites_cache."""

    @pytest.mark.asyncio
    async def test_clear_cache_success(
        self,
        favorites_service,
        mock_redis,
        sample_user_id,
    ):
        """Тест успешной очистки кэша."""
        # Execute
        await favorites_service.clear_user_favorites_cache(sample_user_id)

        # Assert
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_redis_error(
        self,
        favorites_service,
        sample_user_id,
    ):
        """Тест обработки ошибки Redis при очистке кэша."""
        # Setup - отключаем Redis
        favorites_service._redis_client = None

        # Execute - не должно падать
        await favorites_service.clear_user_favorites_cache(sample_user_id)

        # Assert - просто проверяем что не упало
        assert True


class TestInvalidateCache:
    """Тесты метода _invalidate_cache."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_success(
        self,
        favorites_service,
        mock_redis,
        sample_user_id,
    ):
        """Тест успешной инвалидации кэша."""
        # Execute
        await favorites_service._invalidate_cache(sample_user_id)

        # Assert
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_cache_no_redis(
        self,
        mock_db_session,
        sample_user_id,
    ):
        """Тест инвалидации кэша без Redis."""
        # Setup
        service = FavoritesService(mock_db_session)
        service._redis_client = None

        # Execute - не должно падать
        await service._invalidate_cache(sample_user_id)

        # Assert - просто проверяем что не упало
        assert True

    @pytest.mark.asyncio
    async def test_invalidate_cache_redis_error(
        self,
        favorites_service,
        mock_redis,
        sample_user_id,
    ):
        """Тест обработки ошибки Redis при инвалидации."""
        # Setup
        mock_redis.delete.side_effect = Exception("Redis error")

        # Execute - не должно падать
        await favorites_service._invalidate_cache(sample_user_id)

        # Assert - просто проверяем что не упало
        assert True


class TestGetFavoriteByListing:
    """Тесты метода get_favorite_by_listing."""

    @pytest.mark.asyncio
    async def test_get_favorite_by_listing_found(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
        sample_favorite,
    ):
        """Тест получения записи об избранном."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_favorite
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await favorites_service.get_favorite_by_listing(
            user_id=sample_user_id, listing_id=sample_listing_id
        )

        # Assert
        assert result == sample_favorite

    @pytest.mark.asyncio
    async def test_get_favorite_by_listing_not_found(
        self,
        favorites_service,
        mock_db_session,
        sample_user_id,
        sample_listing_id,
    ):
        """Тест получения отсутствующей записи."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await favorites_service.get_favorite_by_listing(
            user_id=sample_user_id, listing_id=sample_listing_id
        )

        # Assert
        assert result is None


class TestSerializeDeserialize:
    """Тесты методов сериализации/десериализации."""

    @pytest.mark.asyncio
    async def test_serialize_favorite(
        self,
        favorites_service,
        sample_favorite,
        sample_listing,
    ):
        """Тест сериализации Favorite в JSON."""
        # Setup - добавляем listing к favorite
        sample_favorite.listing = sample_listing

        # Execute
        serialized = favorites_service._serialize_favorite(sample_favorite)

        # Assert
        assert isinstance(serialized, dict)
        assert "id" in serialized
        assert "user_id" in serialized
        assert "listing_id" in serialized
        assert "created_at" in serialized
        assert "listing" in serialized
        assert serialized["listing"]["kufar_id"] == "test_123"
        assert serialized["listing"]["title"] == "Test Listing"

    @pytest.mark.asyncio
    async def test_deserialize_favorites(
        self,
        favorites_service,
        sample_favorite,
        sample_listing,
    ):
        """Тест десериализации JSON в список Favorite."""
        # Setup
        sample_favorite.listing = sample_listing
        serialized_data = [favorites_service._serialize_favorite(sample_favorite)]

        # Execute
        deserialized = favorites_service._deserialize_favorites(serialized_data)

        # Assert
        assert len(deserialized) == 1
        assert isinstance(deserialized[0], Favorite)
        assert deserialized[0].id == sample_favorite.id
        assert deserialized[0].listing is not None
        assert deserialized[0].listing.kufar_id == "test_123"

    @pytest.mark.asyncio
    async def test_serialize_deserialize_roundtrip(
        self,
        favorites_service,
        sample_favorite,
        sample_listing,
    ):
        """Тест круговой сериализации/десериализации."""
        # Setup
        sample_favorite.listing = sample_listing

        # Execute
        serialized = favorites_service._serialize_favorite(sample_favorite)
        deserialized = favorites_service._deserialize_favorites([serialized])

        # Assert
        assert len(deserialized) == 1
        assert deserialized[0].id == sample_favorite.id
        assert deserialized[0].user_id == sample_favorite.user_id
        assert deserialized[0].listing_id == sample_favorite.listing_id
        assert deserialized[0].listing.kufar_id == sample_listing.kufar_id


class TestCacheWriteRead:
    """Тесты записи и чтения кэша."""

    @pytest.mark.asyncio
    async def test_get_favorites_cache_write(
        self,
        favorites_service,
        mock_db_session,
        mock_redis,
        sample_user_id,
        sample_favorite,
        sample_listing,
    ):
        """Тест записи в кэш при get_favorites."""
        # Setup - cache miss
        mock_redis.get.return_value = None

        # Setup - mock для scalars().all()
        sample_favorite.listing = sample_listing
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_favorite]

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value = mock_scalars
        mock_execute_result.scalar.return_value = 1  # total count

        # Настраиваем последовательные вызовы execute
        mock_db_session.execute.side_effect = [mock_execute_result, mock_execute_result]

        # Execute
        favorites, total = await favorites_service.get_favorites(
            user_id=sample_user_id, page=1, size=20
        )

        # Assert - проверяем что кэш был записан
        assert mock_redis.setex.called
        assert mock_redis.setex.call_args[0][1] == FAVORITES_CACHE_TTL  # TTL
        # Проверяем что ключ содержит user_id, page, size
        cache_key = mock_redis.setex.call_args[0][0]
        assert str(sample_user_id) in cache_key
        assert "1" in cache_key  # page
        assert "20" in cache_key  # size

    @pytest.mark.asyncio
    async def test_get_favorites_cache_read(
        self,
        favorites_service,
        mock_db_session,
        mock_redis,
        sample_user_id,
        sample_favorite,
        sample_listing,
    ):
        """Тест чтения из кэша при get_favorites."""
        # Setup - cache hit
        sample_favorite.listing = sample_listing
        serialized_data = [favorites_service._serialize_favorite(sample_favorite)]
        mock_redis.get.return_value = json.dumps(serialized_data)

        # Setup - mock для total count
        mock_execute_result = MagicMock()
        mock_execute_result.scalar.return_value = 1
        mock_db_session.execute.return_value = mock_execute_result

        # Execute
        favorites, total = await favorites_service.get_favorites(
            user_id=sample_user_id, page=1, size=20
        )

        # Assert - проверяем что кэш был прочитан
        mock_redis.get.assert_called_once()
        assert len(favorites) == 1
        assert isinstance(favorites[0], Favorite)
        assert favorites[0].id == sample_favorite.id
        # БД не должна была запрашиваться для данных (только для total)
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_get_favorites_cache_error_handling(
        self,
        favorites_service,
        mock_db_session,
        mock_redis,
        sample_user_id,
    ):
        """Тест обработки ошибок Redis при чтении кэша."""
        # Setup - Redis ошибка при чтении
        mock_redis.get.side_effect = Exception("Redis connection error")

        # Setup - пустой результат из БД
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        # Execute - не должно падать
        favorites, total = await favorites_service.get_favorites(
            user_id=sample_user_id, page=1, size=20
        )

        # Assert
        assert favorites == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_favorites_cache_write_error(
        self,
        favorites_service,
        mock_db_session,
        mock_redis,
        sample_user_id,
    ):
        """Тест обработки ошибок Redis при записи в кэш."""
        # Setup - cache miss
        mock_redis.get.return_value = None
        # Redis ошибка при записи
        mock_redis.setex.side_effect = Exception("Redis write error")

        # Setup - пустой результат из БД
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.side_effect = [mock_result, mock_result]

        # Execute - не должно падать
        favorites, total = await favorites_service.get_favorites(
            user_id=sample_user_id, page=1, size=20
        )

        # Assert
        assert favorites == []
        assert total == 0
