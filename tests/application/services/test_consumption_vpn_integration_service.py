import pytest
from unittest.mock import AsyncMock, MagicMock


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
