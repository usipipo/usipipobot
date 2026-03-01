import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import uuid

from application.services import consumption_billing_service
from application.services.consumption_billing_service import (
    ConsumptionBillingService,
    CancellationResult,
)
from domain.entities.consumption_billing import ConsumptionBilling, BillingStatus
from domain.entities.user import User


class TestCanCancelConsumption:
    """Tests para can_cancel_consumption."""

    @pytest.fixture
    def service(self, mock_billing_repo, mock_user_repo):
        return ConsumptionBillingService(
            billing_repo=mock_billing_repo,
            user_repo=mock_user_repo
        )

    @pytest.fixture
    def mock_billing_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_user_without_active_cycle_cannot_cancel(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Usuario sin ciclo activo no puede cancelar."""
        user = User(telegram_id=123, consumption_mode_enabled=True)
        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = None

        can_cancel, error = await service.can_cancel_consumption(123, 123)

        assert can_cancel is False
        assert "No tienes un ciclo de consumo activo" in error

    @pytest.mark.asyncio
    async def test_user_with_pending_debt_cannot_cancel(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Usuario con deuda pendiente no puede cancelar."""
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=True
        )
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=uuid.uuid4()
        )
        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        can_cancel, error = await service.can_cancel_consumption(123, 123)

        assert can_cancel is False
        assert "deuda pendiente" in error

    @pytest.mark.asyncio
    async def test_user_with_active_cycle_can_cancel_even_without_flag(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Usuario con ciclo activo puede cancelar aunque el flag esté desactivado."""
        user = User(
            telegram_id=123,
            consumption_mode_enabled=False,  # Flag desactivado
            has_pending_debt=False
        )
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=uuid.uuid4()
        )
        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        can_cancel, error = await service.can_cancel_consumption(123, 123)

        # Ahora usa el billing como fuente de verdad, no el flag
        assert can_cancel is True
        assert error is None

    @pytest.mark.asyncio
    async def test_user_not_found_cannot_cancel(self, service, mock_user_repo):
        """Usuario no encontrado no puede cancelar."""
        mock_user_repo.get_by_id.return_value = None

        can_cancel, error = await service.can_cancel_consumption(123, 123)

        assert can_cancel is False
        assert "Usuario no encontrado" in error

    @pytest.mark.asyncio
    async def test_user_with_active_cycle_can_cancel(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Usuario con ciclo activo puede cancelar."""
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=False
        )
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=uuid.uuid4()
        )
        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        can_cancel, error = await service.can_cancel_consumption(123, 123)

        assert can_cancel is True
        assert error is None


class TestCancelConsumptionMode:
    """Tests para cancel_consumption_mode."""

    @pytest.fixture
    def service(self, mock_billing_repo, mock_user_repo):
        return ConsumptionBillingService(
            billing_repo=mock_billing_repo,
            user_repo=mock_user_repo
        )

    @pytest.fixture
    def mock_billing_repo(self):
        repo = AsyncMock()
        repo.update_status = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_cancel_consumption_mode_success(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Cancelación exitosa del modo consumo."""
        # Setup
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=False
        )
        billing_id = uuid.uuid4()
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=billing_id,
            mb_consumed=Decimal("512.50"),
            total_cost_usd=Decimal("0.125")
        )

        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        # Mock container and vpn integration
        mock_container = MagicMock()
        mock_vpn_integration = AsyncMock()
        mock_vpn_integration.block_user_keys.return_value = {"success": True, "errors": []}
        mock_container.resolve.return_value = mock_vpn_integration

        mock_container_module = MagicMock()
        mock_container_module.get_container.return_value = mock_container

        # Mock the imports inside the function
        with patch.dict('sys.modules', {
            'application.services.consumption_vpn_integration_service': MagicMock(),
            'application.services.common.container': mock_container_module
        }):
            # Execute
            result = await service.cancel_consumption_mode(123, 123)

        # Assert
        assert result.success is True
        assert result.billing_id == billing_id
        assert result.mb_consumed == Decimal("512.50")
        assert result.total_cost_usd == Decimal("0.125")
        assert result.days_active >= 0
        assert result.had_debt is True
        assert result.error_message is None

        # Verify user was marked with debt
        assert user.has_pending_debt is True
        mock_user_repo.save.assert_called_once()

        # Verify billing status was updated
        mock_billing_repo.update_status.assert_called_once_with(
            billing_id, BillingStatus.CLOSED, 123
        )

    @pytest.mark.asyncio
    async def test_cancel_consumption_mode_user_not_found(
        self, service, mock_user_repo
    ):
        """Error cuando usuario no existe."""
        mock_user_repo.get_by_id.return_value = None

        result = await service.cancel_consumption_mode(123, 123)

        assert result.success is False
        assert "Usuario no encontrado" in result.error_message

    @pytest.mark.asyncio
    async def test_cancel_consumption_mode_no_active_billing(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Error cuando no hay ciclo activo."""
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=False
        )
        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = None

        result = await service.cancel_consumption_mode(123, 123)

        assert result.success is False
        assert "No tienes un ciclo de consumo activo" in result.error_message

    @pytest.mark.asyncio
    async def test_cancel_consumption_mode_already_has_debt(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Error cuando usuario ya tiene deuda."""
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=True
        )
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=uuid.uuid4()
        )
        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        result = await service.cancel_consumption_mode(123, 123)

        assert result.success is False
        assert "deuda pendiente" in result.error_message

    @pytest.mark.asyncio
    async def test_cancel_consumption_mode_handles_container_none(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Maneja caso cuando container es None."""
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=False
        )
        billing_id = uuid.uuid4()
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=billing_id
        )

        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        # Mock the imports inside the function - container will return None
        mock_container_module = MagicMock()
        mock_container_module.get_container.return_value = None

        with patch.dict('sys.modules', {
            'application.services.consumption_vpn_integration_service': MagicMock(),
            'application.services.common.container': mock_container_module
        }):
            # Should not raise, should complete successfully
            result = await service.cancel_consumption_mode(123, 123)

        assert result.success is True
        assert result.billing_id == billing_id


class TestCancelConsumptionModeWithoutDebt:
    """Tests específicos para cancelación sin deuda (fix del bug)."""

    @pytest.fixture
    def service(self, mock_billing_repo, mock_user_repo):
        return ConsumptionBillingService(
            billing_repo=mock_billing_repo,
            user_repo=mock_user_repo
        )

    @pytest.fixture
    def mock_billing_repo(self):
        repo = AsyncMock()
        repo.update_status = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_cancel_without_consumption_no_debt_no_block(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """BUG FIX: Cancelación sin consumo NO bloquea claves ni marca deuda."""
        # Setup - ciclo activo pero sin consumo
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=False
        )
        billing_id = uuid.uuid4()
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=billing_id,
            mb_consumed=Decimal("0"),
            total_cost_usd=Decimal("0")
        )

        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        # Execute - sin mocks de VPN (no debería llamarse)
        result = await service.cancel_consumption_mode(123, 123)

        # Assert - éxito
        assert result.success is True
        assert result.billing_id == billing_id
        assert result.mb_consumed == Decimal("0")
        assert result.total_cost_usd == Decimal("0")
        assert result.had_debt is False

        # Assert - usuario NO marcado como deudor
        assert user.has_pending_debt is False
        assert user.consumption_mode_enabled is False  # Se desactivó
        assert user.current_billing_id is None

        # Assert - ciclo cerrado
        mock_billing_repo.update_status.assert_called_once_with(
            billing_id, BillingStatus.CLOSED, 123
        )

    @pytest.mark.asyncio
    async def test_cancel_with_consumption_blocks_keys_and_marks_debt(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Cancelación CON consumo: SÍ bloquea claves, SÍ marca deuda."""
        # Setup - ciclo activo CON consumo
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=False
        )
        billing_id = uuid.uuid4()
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=billing_id,
            mb_consumed=Decimal("1024.00"),
            total_cost_usd=Decimal("0.25")
        )

        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        # Mock container and vpn integration
        mock_container = MagicMock()
        mock_vpn_integration = AsyncMock()
        mock_vpn_integration.block_user_keys.return_value = {"success": True, "errors": []}
        mock_container.resolve.return_value = mock_vpn_integration

        mock_container_module = MagicMock()
        mock_container_module.get_container.return_value = mock_container

        # Mock the imports inside the function
        with patch.dict('sys.modules', {
            'application.services.consumption_vpn_integration_service': MagicMock(),
            'application.services.common.container': mock_container_module
        }):
            # Execute
            result = await service.cancel_consumption_mode(123, 123)

        # Assert - éxito
        assert result.success is True
        assert result.billing_id == billing_id
        assert result.mb_consumed == Decimal("1024.00")
        assert result.total_cost_usd == Decimal("0.25")
        assert result.had_debt is True

        # Assert - usuario SÍ marcado como deudor
        assert user.has_pending_debt is True

        # Assert - se llamó a bloquear claves
        mock_vpn_integration.block_user_keys.assert_called_once_with(123, 123)
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_with_zero_mb_but_positive_cost(
        self, service, mock_user_repo, mock_billing_repo
    ):
        """Cancelación con costo > 0 aunque MB = 0: SÍ marca deuda."""
        # Setup - ciclo con costo positivo (caso edge)
        user = User(
            telegram_id=123,
            consumption_mode_enabled=True,
            has_pending_debt=False
        )
        billing_id = uuid.uuid4()
        billing = ConsumptionBilling(
            user_id=123,
            started_at=datetime.now(timezone.utc),
            status=BillingStatus.ACTIVE,
            id=billing_id,
            mb_consumed=Decimal("0"),
            total_cost_usd=Decimal("0.01")  # Costo positivo
        )

        mock_user_repo.get_by_id.return_value = user
        mock_billing_repo.get_active_by_user.return_value = billing

        # Mock container and vpn integration
        mock_container = MagicMock()
        mock_vpn_integration = AsyncMock()
        mock_vpn_integration.block_user_keys.return_value = {"success": True, "errors": []}
        mock_container.resolve.return_value = mock_vpn_integration

        mock_container_module = MagicMock()
        mock_container_module.get_container.return_value = mock_container

        with patch.dict('sys.modules', {
            'application.services.consumption_vpn_integration_service': MagicMock(),
            'application.services.common.container': mock_container_module
        }):
            result = await service.cancel_consumption_mode(123, 123)

        # Assert
        assert result.success is True
        assert result.had_debt is True  # Hay deuda por el costo
        assert user.has_pending_debt is True
        mock_vpn_integration.block_user_keys.assert_called_once()
