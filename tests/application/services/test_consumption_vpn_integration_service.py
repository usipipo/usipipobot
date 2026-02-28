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
