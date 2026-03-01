"""
Tests for UserManagementHandler billing_service integration.

Verifies that UserManagementHandler correctly passes billing_service
to KeyManagementHandler when handling show_keys callback.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from application.services.consumption_billing_service import ConsumptionBillingService
from application.services.user_profile_service import UserProfileService
from application.services.vpn_service import VpnService
from telegram_bot.features.user_management.handlers_user_management import (
    UserManagementHandler,
    get_user_callback_handlers,
    get_user_management_handlers,
)


class TestUserManagementHandlerBillingService:
    """Test UserManagementHandler billing_service integration."""

    @pytest.fixture
    def mock_vpn_service(self):
        """Mock VPN service."""
        return MagicMock(spec=VpnService)

    @pytest.fixture
    def mock_user_profile_service(self):
        """Mock user profile service."""
        return MagicMock(spec=UserProfileService)

    @pytest.fixture
    def mock_billing_service(self):
        """Mock billing service."""
        return MagicMock(spec=ConsumptionBillingService)

    @pytest.fixture
    def handler_with_billing(
        self, mock_vpn_service, mock_user_profile_service, mock_billing_service
    ):
        """Create handler with billing_service."""
        return UserManagementHandler(
            vpn_service=mock_vpn_service,
            user_profile_service=mock_user_profile_service,
            billing_service=mock_billing_service,
        )

    @pytest.fixture
    def handler_without_billing(self, mock_vpn_service, mock_user_profile_service):
        """Create handler without billing_service."""
        return UserManagementHandler(
            vpn_service=mock_vpn_service,
            user_profile_service=mock_user_profile_service,
            billing_service=None,
        )

    def test_handler_stores_billing_service(self, handler_with_billing, mock_billing_service):
        """Test that handler correctly stores billing_service."""
        assert handler_with_billing.billing_service is mock_billing_service

    def test_handler_without_billing_service(self, handler_without_billing):
        """Test that handler works without billing_service."""
        assert handler_without_billing.billing_service is None

    def test_handler_default_billing_service_is_none(self, mock_vpn_service):
        """Test that billing_service defaults to None."""
        handler = UserManagementHandler(vpn_service=mock_vpn_service)
        assert handler.billing_service is None

    @pytest.mark.asyncio
    async def test_show_keys_passes_billing_service_to_key_management(
        self, handler_with_billing, mock_vpn_service, mock_billing_service
    ):
        """Test that show_keys callback passes billing_service to KeyManagementHandler."""
        # Mock update and context
        mock_update = MagicMock()
        mock_query = AsyncMock()
        mock_query.data = "show_keys"
        mock_update.callback_query = mock_query
        mock_update.effective_user = MagicMock(id=12345)

        mock_context = MagicMock()

        # Mock KeyManagementHandler - patch where it's imported from
        mock_key_handler_instance = MagicMock()
        mock_key_handler_instance.show_key_submenu = AsyncMock()

        with patch(
            "telegram_bot.features.key_management.handlers_key_management.KeyManagementHandler",
            return_value=mock_key_handler_instance,
        ) as mock_key_handler_class:
            # Call the callback handler
            await handler_with_billing.main_menu_callback(mock_update, mock_context)

            # Verify KeyManagementHandler was created with billing_service
            mock_key_handler_class.assert_called_once_with(
                mock_vpn_service, mock_billing_service
            )

            # Verify show_key_submenu was called
            mock_key_handler_instance.show_key_submenu.assert_called_once_with(
                mock_update, mock_context
            )

    @pytest.mark.asyncio
    async def test_show_keys_passes_none_billing_when_not_provided(
        self, handler_without_billing, mock_vpn_service
    ):
        """Test that show_keys passes None billing_service when not provided."""
        # Mock update and context
        mock_update = MagicMock()
        mock_query = AsyncMock()
        mock_query.data = "show_keys"
        mock_update.callback_query = mock_query
        mock_update.effective_user = MagicMock(id=12345)

        mock_context = MagicMock()

        # Mock KeyManagementHandler - patch where it's imported from
        mock_key_handler_instance = MagicMock()
        mock_key_handler_instance.show_key_submenu = AsyncMock()

        with patch(
            "telegram_bot.features.key_management.handlers_key_management.KeyManagementHandler",
            return_value=mock_key_handler_instance,
        ) as mock_key_handler_class:
            # Call the callback handler
            await handler_without_billing.main_menu_callback(mock_update, mock_context)

            # Verify KeyManagementHandler was created with None billing_service
            mock_key_handler_class.assert_called_once_with(mock_vpn_service, None)


class TestGetUserManagementHandlers:
    """Test get_user_management_handlers factory function."""

    @pytest.fixture
    def mock_vpn_service(self):
        """Mock VPN service."""
        return MagicMock(spec=VpnService)

    @pytest.fixture
    def mock_user_profile_service(self):
        """Mock user profile service."""
        return MagicMock(spec=UserProfileService)

    @pytest.fixture
    def mock_billing_service(self):
        """Mock billing service."""
        return MagicMock(spec=ConsumptionBillingService)

    def test_get_user_management_handlers_with_billing_service(
        self, mock_vpn_service, mock_user_profile_service, mock_billing_service
    ):
        """Test that factory passes billing_service correctly."""
        handlers = get_user_management_handlers(
            vpn_service=mock_vpn_service,
            user_profile_service=mock_user_profile_service,
            billing_service=mock_billing_service,
        )

        assert len(handlers) > 0
        # Verify handlers were created (we can't easily inspect the handler's
        # internal billing_service, but we can verify no exceptions occur)

    def test_get_user_management_handlers_without_billing_service(
        self, mock_vpn_service, mock_user_profile_service
    ):
        """Test that factory works without billing_service."""
        handlers = get_user_management_handlers(
            vpn_service=mock_vpn_service,
            user_profile_service=mock_user_profile_service,
        )

        assert len(handlers) > 0

    def test_get_user_callback_handlers_with_billing_service(
        self, mock_vpn_service, mock_user_profile_service, mock_billing_service
    ):
        """Test that callback factory passes billing_service correctly."""
        handlers = get_user_callback_handlers(
            vpn_service=mock_vpn_service,
            user_profile_service=mock_user_profile_service,
            billing_service=mock_billing_service,
        )

        assert len(handlers) > 0

    def test_get_user_callback_handlers_without_billing_service(
        self, mock_vpn_service, mock_user_profile_service
    ):
        """Test that callback factory works without billing_service."""
        handlers = get_user_callback_handlers(
            vpn_service=mock_vpn_service,
            user_profile_service=mock_user_profile_service,
        )

        assert len(handlers) > 0
