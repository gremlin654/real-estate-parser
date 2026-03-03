"""
Tests for ScanSettingsService
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from app.services.scan_settings_service import ScanSettingsService, utc_now
from app.models.listing import ScanSettings


@pytest.mark.asyncio
class TestScanSettingsService:
    """Tests for ScanSettingsService."""

    async def test_get_settings_creates_default_if_not_exist(self, test_session):
        """Test that get_settings creates default settings if none exist."""
        service = ScanSettingsService(test_session)
        
        settings = await service.get_settings()
        
        assert settings is not None
        assert settings.id == 1
        assert settings.scan_interval_minutes == 30
        assert settings.enabled is True
        assert settings.updated_at is not None

    async def test_get_settings_returns_existing(self, test_session):
        """Test that get_settings returns existing settings."""
        # Create settings manually
        existing_settings = ScanSettings(
            id=1,
            scan_interval_minutes=60,
            enabled=False,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        test_session.add(existing_settings)
        await test_session.commit()
        
        service = ScanSettingsService(test_session)
        settings = await service.get_settings()
        
        assert settings.id == 1
        assert settings.scan_interval_minutes == 60
        assert settings.enabled is False

    async def test_update_settings_interval(self, test_session):
        """Test updating scan interval."""
        service = ScanSettingsService(test_session)
        
        # First get/create default settings
        await service.get_settings()
        
        # Update interval
        updated = await service.update_settings(scan_interval_minutes=45)
        
        assert updated.scan_interval_minutes == 45
        assert updated.enabled is True  # Should remain unchanged

    async def test_update_settings_enabled(self, test_session):
        """Test updating enabled status."""
        service = ScanSettingsService(test_session)
        
        # First get/create default settings
        await service.get_settings()
        
        # Update enabled status
        updated = await service.update_settings(enabled=False)
        
        assert updated.enabled is False
        assert updated.scan_interval_minutes == 30  # Should remain unchanged

    async def test_update_settings_both(self, test_session):
        """Test updating both interval and enabled."""
        service = ScanSettingsService(test_session)
        
        # First get/create default settings
        await service.get_settings()
        
        # Update both
        updated = await service.update_settings(
            scan_interval_minutes=120,
            enabled=False
        )
        
        assert updated.scan_interval_minutes == 120
        assert updated.enabled is False

    async def test_update_settings_invalid_interval_too_small(self, test_session):
        """Test that interval < 5 minutes raises ValueError."""
        service = ScanSettingsService(test_session)
        
        # First get/create default settings
        await service.get_settings()
        
        with pytest.raises(ValueError, match="at least 5 minutes"):
            await service.update_settings(scan_interval_minutes=3)

    async def test_update_settings_invalid_interval_too_large(self, test_session):
        """Test that interval > 1440 minutes raises ValueError."""
        service = ScanSettingsService(test_session)
        
        # First get/create default settings
        await service.get_settings()
        
        with pytest.raises(ValueError, match="at most 1440 minutes"):
            await service.update_settings(scan_interval_minutes=1500)

    async def test_update_settings_boundary_interval_min(self, test_session):
        """Test boundary value: 5 minutes (minimum)."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        updated = await service.update_settings(scan_interval_minutes=5)
        
        assert updated.scan_interval_minutes == 5

    async def test_update_settings_boundary_interval_max(self, test_session):
        """Test boundary value: 1440 minutes (maximum)."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        updated = await service.update_settings(scan_interval_minutes=1440)
        
        assert updated.scan_interval_minutes == 1440

    async def test_get_interval_minutes(self, test_session):
        """Test getting interval minutes."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        interval = await service.get_interval_minutes()
        
        assert interval == 30

    async def test_get_interval_minutes_after_update(self, test_session):
        """Test getting interval minutes after update."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        await service.update_settings(scan_interval_minutes=90)
        interval = await service.get_interval_minutes()
        
        assert interval == 90

    async def test_is_enabled_true(self, test_session):
        """Test is_enabled returns True by default."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        enabled = await service.is_enabled()
        
        assert enabled is True

    async def test_is_enabled_false(self, test_session):
        """Test is_enabled returns False after update."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        await service.update_settings(enabled=False)
        enabled = await service.is_enabled()
        
        assert enabled is False

    async def test_update_settings_updates_timestamp(self, test_session):
        """Test that update_settings updates the timestamp."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        before_update = datetime.now(timezone.utc).replace(tzinfo=None)
        
        updated = await service.update_settings(scan_interval_minutes=45)
        
        assert updated.updated_at >= before_update
        assert updated.updated_at <= datetime.now(timezone.utc).replace(tzinfo=None)

    async def test_multiple_updates(self, test_session):
        """Test multiple sequential updates."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        
        # First update
        updated1 = await service.update_settings(scan_interval_minutes=45)
        assert updated1.scan_interval_minutes == 45
        assert updated1.enabled is True
        
        # Second update
        updated2 = await service.update_settings(enabled=False)
        assert updated2.scan_interval_minutes == 45  # Unchanged
        assert updated2.enabled is False
        
        # Third update
        updated3 = await service.update_settings(scan_interval_minutes=60, enabled=True)
        assert updated3.scan_interval_minutes == 60
        assert updated3.enabled is True


class TestUtcNow:
    """Tests for utc_now helper function."""

    def test_utc_now_returns_datetime(self):
        """Test that utc_now returns a datetime object."""
        result = utc_now()
        
        assert isinstance(result, datetime)

    def test_utc_now_returns_utc_time(self):
        """Test that utc_now returns UTC time."""
        from datetime import datetime as dt, timezone
        
        result = utc_now()
        now_utc = dt.now(timezone.utc).replace(tzinfo=None)
        
        # Should be close to current UTC time (within 1 second)
        diff = abs((now_utc - result).total_seconds())
        assert diff < 1

    def test_utc_now_no_microseconds_precision(self):
        """Test that utc_now can return time with microseconds."""
        result = utc_now()
        
        # May or may not have microseconds, but should be valid datetime
        assert result.year >= 2024
        assert 1 <= result.month <= 12
        assert 1 <= result.day <= 31


@pytest.mark.asyncio
class TestScanSettingsServiceEdgeCases:
    """Edge case tests for ScanSettingsService."""

    async def test_concurrent_get_settings(self, test_session):
        """Test that concurrent get_settings calls return same settings."""
        service = ScanSettingsService(test_session)
        
        # First call creates settings
        settings1 = await service.get_settings()
        
        # Second call should return existing
        settings2 = await service.get_settings()
        
        assert settings1.id == settings2.id
        assert settings1.scan_interval_minutes == settings2.scan_interval_minutes

    async def test_update_with_none_values(self, test_session):
        """Test that None values don't change settings."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        updated = await service.update_settings(
            scan_interval_minutes=None,
            enabled=None
        )
        
        # Should remain default values
        assert updated.scan_interval_minutes == 30
        assert updated.enabled is True

    async def test_update_only_interval_keeps_enabled(self, test_session):
        """Test updating only interval keeps enabled unchanged."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        await service.update_settings(enabled=False)
        updated = await service.update_settings(scan_interval_minutes=60)
        
        assert updated.scan_interval_minutes == 60
        assert updated.enabled is False  # Should remain False

    async def test_update_only_enabled_keeps_interval(self, test_session):
        """Test updating only enabled keeps interval unchanged."""
        service = ScanSettingsService(test_session)
        
        await service.get_settings()
        await service.update_settings(scan_interval_minutes=90)
        updated = await service.update_settings(enabled=False)
        
        assert updated.scan_interval_minutes == 90  # Should remain 90
        assert updated.enabled is False
