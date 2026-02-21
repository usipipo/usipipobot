from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.services.vpn_service import VpnService
from domain.entities.user import User
from telegram_bot.features.vpn_keys.handlers_vpn_keys import VpnKeysHandler


class TestVpnKeysHandler:

    @pytest.fixture
    def vpn_service(self):
        service = MagicMock(spec=VpnService)
        service.user_repo = MagicMock()
        return service

    @pytest.fixture
    def handler(self, vpn_service):
        return VpnKeysHandler(vpn_service)

    @pytest.mark.asyncio
    async def test_start_creation_blocks_when_limit_reached(self, handler, vpn_service):
        """Usuario con limite de claves alcanzado no puede crear mas."""
        user = User(telegram_id=123, max_keys=2)
        user.keys = [MagicMock(is_active=True), MagicMock(is_active=True)]

        vpn_service.user_repo.get_by_id = AsyncMock(return_value=user)
        vpn_service.can_user_create_key = AsyncMock(
            return_value=(False, "Has alcanzado el limite de 2 llaves.")
        )

        update = MagicMock()
        update.effective_user.id = 123
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()
        context.user_data = {}

        result = await handler.start_creation(update, context)

        assert result == -1
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert (
            "límite" in call_args.kwargs["text"].lower()
            or "limit" in call_args.kwargs["text"].lower()
        )
