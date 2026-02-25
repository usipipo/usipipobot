from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.services.user_profile_service import UserProfileService
from application.services.vpn_service import VpnService
from domain.entities.user import User, UserStatus
from telegram_bot.features.user_management.handlers_user_management import (
    UserManagementHandler,
)


class TestUserManagementHandler:

    @pytest.fixture
    def vpn_service(self):
        service = MagicMock(spec=VpnService)
        service.user_repo = MagicMock()
        return service

    @pytest.fixture
    def user_profile_service(self):
        service = MagicMock(spec=UserProfileService)
        return service

    @pytest.fixture
    def handler(self, vpn_service, user_profile_service):
        return UserManagementHandler(vpn_service, user_profile_service)

    @pytest.mark.asyncio
    async def test_show_usage_callback_calls_info_handler(
        self, handler, user_profile_service
    ):
        """Callback show_usage debe llamar a info_handler."""
        profile = MagicMock()
        profile.user_id = 123
        profile.full_name = "Test User"
        profile.username = "testuser"
        profile.created_at.strftime = MagicMock(return_value="2024-01-01")
        profile.status = "active"
        profile.total_used_gb = 2.5
        profile.free_data_remaining_gb = 7.5
        profile.active_packages = 1
        profile.keys_used = 1
        profile.max_keys = 2
        profile.referral_code = "TEST123"
        profile.total_referrals = 2
        profile.referral_credits = 50

        user_profile_service.get_user_profile_summary = AsyncMock(return_value=profile)

        update = MagicMock()
        update.effective_user.id = 123
        update.callback_query = MagicMock()
        update.callback_query.data = "show_usage"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.message = None

        context = MagicMock()

        await handler.main_menu_callback(update, context)

        assert update.callback_query.answer.called
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "DATA METRICS" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_info_handler_shows_user_profile(self, handler, user_profile_service):
        """info_handler debe mostrar el perfil del usuario."""
        profile = MagicMock()
        profile.user_id = 123
        profile.full_name = "Test User"
        profile.username = "testuser"
        profile.created_at.strftime = MagicMock(return_value="2024-01-01")
        profile.status = "active"
        profile.total_used_gb = 3.5
        profile.free_data_remaining_gb = 6.5
        profile.active_packages = 2
        profile.keys_used = 1
        profile.max_keys = 2
        profile.referral_code = "ABC123"
        profile.total_referrals = 5
        profile.referral_credits = 100

        user_profile_service.get_user_profile_summary = AsyncMock(return_value=profile)

        update = MagicMock()
        update.effective_user.id = 123
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        await handler.info_handler(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        text = call_args.kwargs["text"]
        assert "DATA METRICS" in text
        assert "Test User" in text

    @pytest.mark.asyncio
    async def test_info_handler_without_profile_service(self, handler, vpn_service):
        """info_handler funciona sin user_profile_service usando vpn_service."""
        handler.user_profile_service = None

        user = User(
            telegram_id=123,
            username="testuser",
            full_name="Test User",
            status=UserStatus.ACTIVE,
            max_keys=2,
        )

        vpn_service.get_user_status = AsyncMock(
            return_value={"user": user, "keys": [], "total_used_gb": 1.5}
        )

        update = MagicMock()
        update.effective_user.id = 123
        update.callback_query = None
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        context = MagicMock()

        await handler.info_handler(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        text = call_args.kwargs["text"]
        assert "DATA METRICS" in text
