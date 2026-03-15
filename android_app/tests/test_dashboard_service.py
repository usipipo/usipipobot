"""
Tests for Android dashboard service.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.services.dashboard_service import DashboardService
from src.storage.cache_storage import CacheStorage


class TestDashboardService:
    """Test dashboard service functionality."""

    @pytest.fixture
    def mock_api_client(self):
        """Mock API client."""
        with patch("src.services.dashboard_service.ApiClient") as mock:
            yield mock

    @pytest.fixture
    def mock_cache_storage(self):
        """Mock cache storage."""
        with patch("src.services.dashboard_service.CacheStorage") as mock:
            yield mock

    @pytest.fixture
    def dashboard_service(self, mock_api_client, mock_cache_storage):
        """Create dashboard service instance."""
        return DashboardService(telegram_id="123456789")

    def test_init(self, dashboard_service):
        """Test service initialization."""
        assert dashboard_service.telegram_id == "123456789"
        assert dashboard_service.api_client is not None
        assert dashboard_service.cache_storage is not None

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_cache_hit(self, dashboard_service, mock_cache_storage):
        """Test getting dashboard data from cache."""
        # Arrange
        cached_data = {
            "user": {"telegram_id": 123456789, "username": "testuser"},
            "data_summary": {"total_used_bytes": 1000, "total_limit_bytes": 5000},
        }
        dashboard_service.cache_storage.get = MagicMock(return_value=cached_data)

        # Act
        result = await dashboard_service.get_dashboard_summary()

        # Assert
        assert result == cached_data
        dashboard_service.cache_storage.get.assert_called_once_with("dashboard:123456789")

    @pytest.mark.asyncio
    async def test_get_dashboard_summary_cache_miss(
        self, dashboard_service, mock_cache_storage, mock_api_client
    ):
        """Test fetching dashboard data from API when cache miss."""
        # Arrange
        dashboard_service.cache_storage.get = MagicMock(return_value=None)

        api_response = {
            "user": {"telegram_id": 123456789, "username": "testuser"},
            "data_summary": {"total_used_bytes": 1000, "total_limit_bytes": 5000},
            "active_keys": [],
            "active_package": None,
        }

        mock_response = AsyncMock()
        mock_response.get = AsyncMock(return_value=api_response)
        dashboard_service.api_client = mock_response

        # Act
        result = await dashboard_service.get_dashboard_summary()

        # Assert
        assert result == api_response
        dashboard_service.api_client.get.assert_called_once_with(
            endpoint="/dashboard/summary", use_auth=True
        )

    @pytest.mark.asyncio
    async def test_refresh_dashboard(self, dashboard_service):
        """Test force refresh dashboard data."""
        # Arrange
        api_response = {
            "user": {"telegram_id": 123456789, "username": "testuser"},
            "data_summary": {"total_used_bytes": 2000, "total_limit_bytes": 5000},
        }

        mock_response = AsyncMock()
        mock_response.get = AsyncMock(return_value=api_response)
        dashboard_service.api_client = mock_response

        # Act
        result = await dashboard_service.refresh_dashboard()

        # Assert
        assert result == api_response
        dashboard_service.api_client.get.assert_called_once_with(
            endpoint="/dashboard/summary", use_auth=True
        )

    def test_format_bytes(self):
        """Test bytes formatting."""
        assert DashboardService.format_bytes(0) == "0 B"
        assert DashboardService.format_bytes(1024) == "1.00 KB"
        assert DashboardService.format_bytes(1048576) == "1.00 MB"
        assert DashboardService.format_bytes(1073741824) == "1.00 GB"
        assert DashboardService.format_bytes(2361393152) == "2.20 GB"

    def test_calculate_percentage(self):
        """Test percentage calculation."""
        assert DashboardService.calculate_percentage(0, 100) == 0.0
        assert DashboardService.calculate_percentage(50, 100) == 50.0
        assert DashboardService.calculate_percentage(100, 100) == 100.0
        assert DashboardService.calculate_percentage(150, 100) == 100.0  # Cap at 100%
        assert DashboardService.calculate_percentage(0, 0) == 0.0  # Avoid division by zero

    def test_get_progress_color(self):
        """Test progress bar color selection."""
        assert DashboardService.get_progress_color(0) == "neon_cyan"
        assert DashboardService.get_progress_color(50) == "neon_cyan"
        assert DashboardService.get_progress_color(60) == "neon_cyan"
        assert DashboardService.get_progress_color(61) == "amber"
        assert DashboardService.get_progress_color(85) == "amber"
        assert DashboardService.get_progress_color(86) == "error"
        assert DashboardService.get_progress_color(100) == "error"

    def test_format_relative_time(self):
        """Test relative time formatting."""
        now = datetime.now(timezone.utc)

        # Just now
        result = DashboardService.format_relative_time(now.isoformat())
        assert "ahora" in result.lower()

        # Invalid input
        result = DashboardService.format_relative_time(None)
        assert result == "Nunca"

        result = DashboardService.format_relative_time("invalid")
        assert result == "Desconocido"


class TestDashboardServiceIntegration:
    """Integration tests for dashboard service."""

    @pytest.mark.asyncio
    async def test_full_dashboard_flow(self):
        """Test complete dashboard data flow."""
        # This test would require a running backend
        # Skipped in CI environment
        pytest.skip("Requires running backend API")
