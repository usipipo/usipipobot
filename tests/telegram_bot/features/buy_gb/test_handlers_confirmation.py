"""Tests for ConfirmationMixin successful_payment handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update, User

from application.services.data_package_service import DataPackageService
from domain.entities.data_package import DataPackage, PackageType
from telegram_bot.features.buy_gb.handlers_confirmation import ConfirmationMixin


class TestConfirmationMixin:
    """Tests for ConfirmationMixin payment handling."""

    @pytest.fixture
    def data_package_service(self):
        """Mock DataPackageService."""
        return AsyncMock(spec=DataPackageService)

    @pytest.fixture
    def mixin(self, data_package_service):
        """Create ConfirmationMixin instance."""
        mixin = ConfirmationMixin()
        mixin.data_package_service = data_package_service
        return mixin

    @pytest.fixture
    def mock_update_successful_payment(self):
        """Create mock Update with successful payment."""
        update = MagicMock(spec=Update)
        user = MagicMock(spec=User)
        successful_payment = MagicMock()

        user.id = 12345
        successful_payment.telegram_payment_charge_id = "charge_123"
        successful_payment.invoice_payload = ""
        successful_payment.total_amount = 250

        update.effective_user = user
        update.message = MagicMock()
        update.message.successful_payment = successful_payment
        update.message.reply_text = AsyncMock()

        return update

    @pytest.mark.asyncio
    async def test_successful_payment_miniapp_package(
        self, mixin, mock_update_successful_payment, data_package_service
    ):
        """Test detection and handling of Mini App package payment with miniapp_* prefix."""
        # Arrange
        # Format: miniapp_data_package_{type}_{user_id}_{tx_id}
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.invoice_payload = "miniapp_data_package_basic_12345_tx_abc123"

        mock_package = MagicMock(spec=DataPackage)
        mock_package.package_type = PackageType.BASIC
        mock_package.data_gb = 10
        mock_package.expires_at = MagicMock()
        mock_package.expires_at.strftime.return_value = "17/03/2027 12:00"

        data_package_service.purchase_package = AsyncMock(return_value=(mock_package, {"bonus": 0}))

        context = MagicMock()

        # Act
        await mixin.successful_payment(mock_update_successful_payment, context)

        # Assert
        data_package_service.purchase_package.assert_called_once()
        call_args = data_package_service.purchase_package.call_args
        assert call_args.kwargs["user_id"] == 12345
        assert call_args.kwargs["package_type"] == "basic"
        assert call_args.kwargs["telegram_payment_id"] == "miniapp_tx_abc123"

        mock_update_successful_payment.message.reply_text.assert_called_once()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "✅ *¡Pago Recibido!*" in call_args.kwargs["text"]
        assert "🚀 Abrir Mini App" in str(call_args.kwargs["reply_markup"])

    @pytest.mark.asyncio
    async def test_successful_payment_miniapp_slots(
        self, mixin, mock_update_successful_payment, data_package_service
    ):
        """Test detection and handling of Mini App slots payment with miniapp_* prefix."""
        # Arrange
        # Format: miniapp_key_slots_{slots}_{user_id}_{tx_id}
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.invoice_payload = "miniapp_key_slots_5_12345_tx_def456"

        data_package_service.purchase_key_slots = AsyncMock(
            return_value={"slots_added": 5, "new_max_keys": 7, "stars_paid": 500}
        )

        context = MagicMock()

        # Act
        await mixin.successful_payment(mock_update_successful_payment, context)

        # Assert
        data_package_service.purchase_key_slots.assert_called_once()
        call_args = data_package_service.purchase_key_slots.call_args
        assert call_args.kwargs["user_id"] == 12345
        assert call_args.kwargs["slots"] == 5
        assert call_args.kwargs["telegram_payment_id"] == "miniapp_tx_def456"

        mock_update_successful_payment.message.reply_text.assert_called_once()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "✅ *¡Pago Recibido!*" in call_args.kwargs["text"]
        assert "🚀 Abrir Mini App" in str(call_args.kwargs["reply_markup"])

    @pytest.mark.asyncio
    async def test_successful_payment_miniapp_subscription(
        self, mixin, mock_update_successful_payment, data_package_service
    ):
        """Test detection and handling of Mini App subscription payment with miniapp_* prefix."""
        # Arrange
        # Format: miniapp_subscription_{plan}_{user_id}_{tx_id}
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.invoice_payload = "miniapp_subscription_one_month_12345_tx_ghi789"

        context = MagicMock()

        # Mock SubscriptionService
        mock_subscription_service = MagicMock()
        mock_subscription_option = MagicMock()
        mock_subscription_option.stars = 360
        mock_subscription_service.get_plan_option.return_value = mock_subscription_option

        mock_subscription = MagicMock()
        mock_subscription_service.activate_subscription = AsyncMock(return_value=mock_subscription)

        with patch(
            "telegram_bot.features.buy_gb.handlers_confirmation.get_service"
        ) as mock_get_service:
            mock_get_service.return_value = mock_subscription_service

            # Act
            await mixin.successful_payment(mock_update_successful_payment, context)

            # Assert
            mock_get_service.assert_called_once()
            mock_subscription_service.get_plan_option.assert_called_once_with("one_month")
            mock_subscription_service.activate_subscription.assert_called_once()

            mock_update_successful_payment.message.reply_text.assert_called_once()
            call_args = mock_update_successful_payment.message.reply_text.call_args
            assert "✅ *¡Pago Recibido!*" in call_args.kwargs["text"]
            assert "🚀 Abrir Mini App" in str(call_args.kwargs["reply_markup"])

    @pytest.mark.asyncio
    async def test_successful_payment_regular_bot_no_regression(
        self, mixin, mock_update_successful_payment, data_package_service
    ):
        """Test that regular Bot payments still work (no regression)."""
        # Arrange - Regular bot payment format: data_package_{type}_{user_id}
        # Note: This format is handled by backward compatibility handler for old Mini App
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.invoice_payload = "data_package_basic_12345_tx_old"

        mock_package = MagicMock(spec=DataPackage)
        mock_package.package_type = PackageType.BASIC
        mock_package.data_gb = 10
        mock_package.expires_at = MagicMock()
        mock_package.expires_at.strftime.return_value = "17/03/2027 12:00"

        data_package_service.purchase_package = AsyncMock(return_value=(mock_package, {"bonus": 0}))

        context = MagicMock()

        # Act
        await mixin.successful_payment(mock_update_successful_payment, context)

        # Assert - Should use old Mini App flow (backward compatibility)
        data_package_service.purchase_package.assert_called_once()
        call_args = data_package_service.purchase_package.call_args
        assert call_args.kwargs["user_id"] == 12345
        assert call_args.kwargs["package_type"] == "basic"
        assert call_args.kwargs["telegram_payment_id"] == "charge_123"  # Not miniapp_ prefixed

        # Should use regular bot keyboard, not Mini App link
        mock_update_successful_payment.message.reply_text.assert_called_once()
