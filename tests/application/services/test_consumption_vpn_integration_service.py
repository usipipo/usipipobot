import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal


class TestConsumptionVpnIntegrationService:
    @pytest.fixture
    def service(self):
        from application.services.consumption_vpn_integration_service import (
            ConsumptionVpnIntegrationService,
        )

        return ConsumptionVpnIntegrationService(
            user_repo=AsyncMock(),
            key_repo=AsyncMock(),
            vpn_infra_service=AsyncMock(),
            billing_service=AsyncMock(),
        )

    @pytest.mark.asyncio
    async def test_service_exists(self, service):
        assert service is not None


class TestCheckCanCreateKey:
    @pytest.fixture
    def service(self):
        from application.services.consumption_vpn_integration_service import (
            ConsumptionVpnIntegrationService,
        )

        mock_user_repo = AsyncMock()
        return ConsumptionVpnIntegrationService(
            user_repo=mock_user_repo,
            key_repo=AsyncMock(),
            vpn_infra_service=AsyncMock(),
            billing_service=AsyncMock(),
        )

    @pytest.mark.asyncio
    async def test_user_with_debt_cannot_create_key(self, service):
        user = MagicMock()
        user.has_pending_debt = True
        service.user_repo.get_by_id.return_value = user

        can_create, error = await service.check_can_create_key(123, 123)

        assert can_create is False
        assert "deuda" in error.lower()

    @pytest.mark.asyncio
    async def test_user_without_debt_can_create_key(self, service):
        user = MagicMock()
        user.has_pending_debt = False
        service.user_repo.get_by_id.return_value = user

        can_create, error = await service.check_can_create_key(123, 123)

        assert can_create is True
        assert error is None

    @pytest.mark.asyncio
    async def test_user_not_found_cannot_create_key(self, service):
        service.user_repo.get_by_id.return_value = None

        can_create, error = await service.check_can_create_key(123, 123)

        assert can_create is False
        assert "no encontrado" in error.lower()


class TestBlockUserKeys:
    @pytest.fixture
    def service(self):
        from application.services.consumption_vpn_integration_service import (
            ConsumptionVpnIntegrationService,
        )

        return ConsumptionVpnIntegrationService(
            user_repo=AsyncMock(),
            key_repo=AsyncMock(),
            vpn_infra_service=AsyncMock(),
            billing_service=AsyncMock(),
        )

    @pytest.fixture
    def mock_outline_key(self):
        key = MagicMock()
        key.id = uuid.uuid4()
        key.key_type.value = "outline"
        key.external_id = "outline-key-123"
        key.is_active = True
        return key

    @pytest.fixture
    def mock_wireguard_key(self):
        key = MagicMock()
        key.id = uuid.uuid4()
        key.key_type.value = "wireguard"
        key.external_id = "wireguard-peer-456"
        key.is_active = True
        return key

    @pytest.mark.asyncio
    async def test_block_user_keys_success(
        self, service, mock_outline_key, mock_wireguard_key
    ):
        user = MagicMock()
        user.has_pending_debt = False
        service.user_repo.get_by_id.return_value = user
        service.key_repo.get_by_user_id.return_value = [
            mock_outline_key,
            mock_wireguard_key,
        ]
        service.vpn_infra_service.disable_key.return_value = {"success": True}

        result = await service.block_user_keys(123, 123)

        assert result["success"] is True
        assert result["keys_blocked"] == 2
        assert result["keys_failed"] == 0
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_block_user_keys_partial_failure(
        self, service, mock_outline_key, mock_wireguard_key
    ):
        user = MagicMock()
        user.has_pending_debt = False
        service.user_repo.get_by_id.return_value = user
        service.key_repo.get_by_user_id.return_value = [
            mock_outline_key,
            mock_wireguard_key,
        ]

        # First call succeeds, second fails
        service.vpn_infra_service.disable_key.side_effect = [
            {"success": True},
            {"success": False, "error": "Server error"},
        ]

        result = await service.block_user_keys(123, 123)

        assert result["success"] is False  # Partial success = overall failure
        assert result["keys_blocked"] == 1
        assert result["keys_failed"] == 1
        assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_block_user_keys_no_keys(self, service):
        user = MagicMock()
        user.has_pending_debt = False
        service.user_repo.get_by_id.return_value = user
        service.key_repo.get_by_user_id.return_value = []

        result = await service.block_user_keys(123, 123)

        assert result["success"] is True
        assert result["keys_blocked"] == 0
        user.mark_as_has_debt.assert_called_once()
        service.user_repo.update.assert_called_once()


class TestUnblockUserKeys:
    @pytest.fixture
    def service(self):
        from application.services.consumption_vpn_integration_service import (
            ConsumptionVpnIntegrationService,
        )

        return ConsumptionVpnIntegrationService(
            user_repo=AsyncMock(),
            key_repo=AsyncMock(),
            vpn_infra_service=AsyncMock(),
            billing_service=AsyncMock(),
        )

    @pytest.fixture
    def mock_outline_key(self):
        key = MagicMock()
        key.id = uuid.uuid4()
        key.key_type.value = "outline"
        key.external_id = "outline-key-123"
        key.is_active = False
        return key

    @pytest.fixture
    def mock_wireguard_key(self):
        key = MagicMock()
        key.id = uuid.uuid4()
        key.key_type.value = "wireguard"
        key.external_id = "wireguard-peer-456"
        key.is_active = False
        return key

    @pytest.mark.asyncio
    async def test_unblock_user_keys_success(
        self, service, mock_outline_key, mock_wireguard_key
    ):
        user = MagicMock()
        user.has_pending_debt = True
        service.user_repo.get_by_id.return_value = user
        service.key_repo.get_by_user_id.return_value = [
            mock_outline_key,
            mock_wireguard_key,
        ]
        service.vpn_infra_service.enable_key.return_value = {"success": True}

        result = await service.unblock_user_keys(123, 123)

        assert result["success"] is True
        assert result["keys_unblocked"] == 2
        assert result["keys_failed"] == 0
        assert len(result["errors"]) == 0
        user.mark_debt_as_paid.assert_called_once()
        service.user_repo.update.assert_called_once_with(user, 123)

    @pytest.mark.asyncio
    async def test_unblock_user_keys_partial_failure(
        self, service, mock_outline_key, mock_wireguard_key
    ):
        user = MagicMock()
        user.has_pending_debt = True
        service.user_repo.get_by_id.return_value = user
        service.key_repo.get_by_user_id.return_value = [
            mock_outline_key,
            mock_wireguard_key,
        ]

        # First call succeeds, second fails
        service.vpn_infra_service.enable_key.side_effect = [
            {"success": True},
            {"success": False, "error": "Server error"},
        ]

        result = await service.unblock_user_keys(123, 123)

        assert result["success"] is False  # Partial success = overall failure
        assert result["keys_unblocked"] == 1
        assert result["keys_failed"] == 1
        assert len(result["errors"]) == 1
        user.mark_debt_as_paid.assert_called_once()
        service.user_repo.update.assert_called_once_with(user, 123)

    @pytest.mark.asyncio
    async def test_unblock_user_keys_no_keys(self, service):
        user = MagicMock()
        user.has_pending_debt = True
        service.user_repo.get_by_id.return_value = user
        service.key_repo.get_by_user_id.return_value = []

        result = await service.unblock_user_keys(123, 123)

        assert result["success"] is True
        assert result["keys_unblocked"] == 0
        assert result["keys_failed"] == 0
        user.mark_debt_as_paid.assert_called_once()
        service.user_repo.update.assert_called_once_with(user, 123)
