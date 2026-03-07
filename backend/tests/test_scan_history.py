"""
Tests for Scan History Service

Tests cover:
- Scan history creation and retrieval
- Filtering by city and status
- Summary statistics
- Error handling
"""
import pytest
from sqlalchemy import select
from uuid import uuid4

from app.models.listing import ScanHistory
from app.services.scan_history_service import ScanHistoryService


class TestScanHistoryService:
    """Tests for ScanHistoryService."""

    @pytest.mark.asyncio
    async def test_create_scan_record(self, test_session):
        """Test creating a scan history record."""
        service = ScanHistoryService(test_session)

        scan = await service.create_scan_record(
            city="minsk",
            city_name="Минск",
            trigger_type="manual",
        )

        assert scan.city == "minsk"
        assert scan.city_name == "Минск"
        assert scan.status == "running"
        assert scan.trigger_type == "manual"
        assert scan.listings_fetched == 0
        assert scan.errors == []

    @pytest.mark.asyncio
    async def test_update_scan_record(self, test_session, create_test_scan_history):
        """Test updating a scan history record."""
        service = ScanHistoryService(test_session)

        await service.update_scan_record(
            scan_id=create_test_scan_history.id,
            listings_fetched=200,
            listings_created=20,
            pages_scraped=7,
        )

        # Refresh from DB
        result = await test_session.execute(
            select(ScanHistory).where(ScanHistory.id == create_test_scan_history.id)
        )
        updated_scan = result.scalar_one()

        assert updated_scan.listings_fetched == 200
        assert updated_scan.listings_created == 20
        assert updated_scan.pages_scraped == 7

    @pytest.mark.asyncio
    async def test_complete_scan_record_success(self, test_session, create_test_scan_history):
        """Test completing a scan record with success status."""
        service = ScanHistoryService(test_session)

        await service.complete_scan_record(
            scan_id=create_test_scan_history.id,
            status="completed",
        )

        result = await test_session.execute(
            select(ScanHistory).where(ScanHistory.id == create_test_scan_history.id)
        )
        completed_scan = result.scalar_one()

        assert completed_scan.status == "completed"
        assert completed_scan.completed_at is not None
        assert completed_scan.duration_seconds is not None

    @pytest.mark.asyncio
    async def test_complete_scan_record_error(self, test_session, create_test_scan_history):
        """Test completing a scan record with error status."""
        service = ScanHistoryService(test_session)

        error_msg = "Test error message"
        await service.complete_scan_record(
            scan_id=create_test_scan_history.id,
            status="error",
            error_message=error_msg,
        )

        result = await test_session.execute(
            select(ScanHistory).where(ScanHistory.id == create_test_scan_history.id)
        )
        failed_scan = result.scalar_one()

        assert failed_scan.status == "error"
        assert failed_scan.error_message == error_msg

    @pytest.mark.asyncio
    async def test_get_scan_history(self, test_session, create_multiple_scan_histories):
        """Test getting scan history list."""
        service = ScanHistoryService(test_session)

        scans = await service.get_scan_history(limit=10, offset=0)

        assert len(scans) == 5
        # Should be ordered by started_at DESC
        assert scans[0].started_at >= scans[-1].started_at

    @pytest.mark.asyncio
    async def test_get_scan_history_filtered_by_city(self, test_session, create_multiple_scan_histories):
        """Test filtering scan history by city."""
        service = ScanHistoryService(test_session)

        scans = await service.get_scan_history(city="minsk")

        assert len(scans) == 3  # 3 minsk scans
        assert all(s.city == "minsk" for s in scans)

    @pytest.mark.asyncio
    async def test_get_scan_history_filtered_by_status(self, test_session, create_multiple_scan_histories):
        """Test filtering scan history by status."""
        service = ScanHistoryService(test_session)

        scans = await service.get_scan_history(status="completed")

        assert len(scans) == 3  # 3 completed scans (indices 1, 2, 4)
        assert all(s.status == "completed" for s in scans)

    @pytest.mark.asyncio
    async def test_get_scan_record_by_id(self, test_session, create_test_scan_history):
        """Test getting single scan record by ID."""
        service = ScanHistoryService(test_session)

        scan = await service.get_scan_record_by_id(create_test_scan_history.id)

        assert scan is not None
        assert scan.id == create_test_scan_history.id

    @pytest.mark.asyncio
    async def test_get_scan_record_by_id_not_found(self, test_session):
        """Test getting non-existent scan record."""
        service = ScanHistoryService(test_session)

        scan = await service.get_scan_record_by_id(uuid4())

        assert scan is None

    @pytest.mark.asyncio
    async def test_get_summary(self, test_session, create_multiple_scan_histories):
        """Test getting summary statistics."""
        service = ScanHistoryService(test_session)

        summary = await service.get_summary()

        assert summary["total_scans"] == 5
        # completed_scans: indices 1, 2, 4 (i % 3 != 0) = 3 scans
        assert summary["completed_scans"] == 3
        # failed_scans: indices 0, 3 (i % 3 == 0) = 2 scans
        assert summary["failed_scans"] == 2
        assert summary["running_scans"] == 0
        assert summary["total_listings_fetched"] > 0

    @pytest.mark.asyncio
    async def test_get_summary_filtered_by_city(self, test_session, create_multiple_scan_histories):
        """Test getting summary filtered by city."""
        service = ScanHistoryService(test_session)

        summary = await service.get_summary(city="minsk")

        assert summary["total_scans"] == 3  # 3 minsk scans


# API validation tests removed - API tested via E2E and manual integration tests
# Service tests provide sufficient coverage for business logic