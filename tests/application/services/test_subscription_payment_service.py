"""Tests for SubscriptionPaymentService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.services.subscription_payment_service import SubscriptionPaymentService


class TestSubscriptionPaymentService:
    """Tests for SubscriptionPaymentService."""

    @pytest.fixture
    def mock_subscription_service(self):
        """Create mock subscription service."""
        service = MagicMock()
        service.is_premium_user = AsyncMock(return_value=False)
        service.get_plan_option = MagicMock(return_value=None)
        return service

    @pytest.fixture
    def mock_crypto_payment_service(self):
        """Create mock crypto payment service."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_subscription_service, mock_crypto_payment_service):
        """Create SubscriptionPaymentService instance."""
        return SubscriptionPaymentService(
            subscription_service=mock_subscription_service,
            crypto_payment_service=mock_crypto_payment_service,
        )

    @pytest.mark.asyncio
    async def test_create_stars_invoice_success(self, service, mock_subscription_service):
        """Test creating Stars invoice for subscription."""
        # Arrange
        mock_subscription_service.is_premium_user.return_value = False
        mock_subscription_service.get_plan_option.return_value = MagicMock(
            name="1 Month",
            duration_months=1,
            stars=360,
        )

        # Mock the _send_stars_invoice method
        with patch.object(service, "_send_stars_invoice", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            # Act
            result = await service.create_stars_invoice(
                user_id=123,
                plan_type="one_month",
                transaction_id="test_txn_123",
            )

            # Assert
            assert result["success"] is True
            assert result["amount_stars"] == 360
            assert result["transaction_id"] == "test_txn_123"
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_stars_invoice_fails_if_already_premium(
        self, service, mock_subscription_service
    ):
        """Test that creating invoice fails if user already has subscription."""
        # Arrange
        mock_subscription_service.is_premium_user.return_value = True
        mock_subscription_service.get_plan_option.return_value = MagicMock(
            name="1 Month",
            duration_months=1,
            stars=360,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Ya tienes una suscripción activa"):
            await service.create_stars_invoice(
                user_id=123,
                plan_type="one_month",
                transaction_id="test_txn_123",
            )

    @pytest.mark.asyncio
    async def test_create_stars_invoice_invalid_plan(self, service, mock_subscription_service):
        """Test that creating invoice fails with invalid plan."""
        # Arrange
        mock_subscription_service.get_plan_option.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Plan no válido"):
            await service.create_stars_invoice(
                user_id=123,
                plan_type="invalid_plan",
                transaction_id="test_txn_123",
            )

    @pytest.mark.asyncio
    async def test_create_stars_invoice_sending_fails(self, service, mock_subscription_service):
        """Test handling when invoice sending fails."""
        # Arrange
        mock_subscription_service.is_premium_user.return_value = False
        mock_subscription_service.get_plan_option.return_value = MagicMock(
            name="1 Month",
            duration_months=1,
            stars=360,
        )

        with patch.object(service, "_send_stars_invoice", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = False

            # Act & Assert
            with pytest.raises(Exception, match="No se pudo crear la factura"):
                await service.create_stars_invoice(
                    user_id=123,
                    plan_type="one_month",
                    transaction_id="test_txn_123",
                )

    @pytest.mark.asyncio
    async def test_create_crypto_order_success(self, service, mock_subscription_service):
        """Test creating crypto order for subscription."""
        # Arrange
        mock_subscription_service.is_premium_user.return_value = False
        mock_subscription_service.get_plan_option.return_value = MagicMock(
            name="1 Month",
            duration_months=1,
            usdt=2.99,
        )

        # Act
        result = await service.create_crypto_order(
            user_id=123,
            plan_type="one_month",
            transaction_id="test_txn_456",
        )

        # Assert
        assert result["success"] is True
        assert result["amount_usdt"] == 2.99
        assert result["plan_type"] == "one_month"
        assert "wallet_address" in result
        assert "qr_code_url" in result

    @pytest.mark.asyncio
    async def test_create_crypto_order_fails_if_already_premium(
        self, service, mock_subscription_service
    ):
        """Test that creating crypto order fails if user already has subscription."""
        # Arrange
        mock_subscription_service.is_premium_user.return_value = True
        mock_subscription_service.get_plan_option.return_value = MagicMock(
            name="1 Month",
            duration_months=1,
            usdt=2.99,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Ya tienes una suscripción activa"):
            await service.create_crypto_order(
                user_id=123,
                plan_type="one_month",
                transaction_id="test_txn_456",
            )

    @pytest.mark.asyncio
    async def test_create_crypto_order_invalid_plan(self, service, mock_subscription_service):
        """Test that creating crypto order fails with invalid plan."""
        # Arrange
        mock_subscription_service.is_premium_user.return_value = False
        mock_subscription_service.get_plan_option.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Plan no válido"):
            await service.create_crypto_order(
                user_id=123,
                plan_type="invalid_plan",
                transaction_id="test_txn_456",
            )
