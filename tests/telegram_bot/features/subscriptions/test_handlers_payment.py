"""Tests for SubscriptionPaymentHandler successful_payment handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update, User

from application.services.subscription_service import SubscriptionService
from domain.entities.subscription_plan import PlanType, SubscriptionPlan
from telegram_bot.features.subscriptions.handlers_payment import SubscriptionPaymentHandler


class TestSubscriptionPaymentHandler:
    """Tests for SubscriptionPaymentHandler payment handling."""

    @pytest.fixture
    def subscription_service(self):
        """Mock SubscriptionService."""
        return AsyncMock(spec=SubscriptionService)

    @pytest.fixture
    def handler(self, subscription_service):
        """Create SubscriptionPaymentHandler instance."""
        with patch(
            "telegram_bot.features.subscriptions.handlers_payment.get_service",
            return_value=subscription_service,
        ):
            handler = SubscriptionPaymentHandler()
            handler.subscription_service = subscription_service
            return handler

    @pytest.fixture
    def mock_update_successful_payment(self):
        """Create mock Update with successful payment."""
        update = MagicMock(spec=Update)
        user = MagicMock(spec=User)

        # Create successful_payment as a simple object with attributes
        class MockPayment:
            def __init__(self, payload=""):
                self.telegram_payment_charge_id = "charge_123"
                self.total_amount = 360
                self.payload = payload

        # Use hyphen instead of underscore in plan_type to avoid split issues
        # Format: subscription_<plan_type>_<user_id>_<transaction_id>
        successful_payment = MockPayment(payload="subscription_one-month_12345_txn456")
        user.id = 12345

        update.effective_user = user
        update.message = MagicMock()
        update.message.successful_payment = successful_payment
        update.message.reply_text = AsyncMock()

        return update

    @pytest.mark.asyncio
    async def test_successful_payment_activates_subscription(
        self, handler, mock_update_successful_payment, subscription_service
    ):
        """Test that successful payment activates subscription."""
        # Arrange - payload is set in fixture: subscription_one-month_12345_txn456
        successful_payment = mock_update_successful_payment.message.successful_payment
        # Override total_amount to match plan
        successful_payment.total_amount = 360

        mock_subscription = MagicMock(spec=SubscriptionPlan)
        mock_subscription.id = "sub-uuid-123"
        mock_subscription.plan_type = PlanType.ONE_MONTH
        mock_subscription.expires_at = MagicMock()
        mock_subscription.expires_at.strftime.return_value = "18/04/2026"

        subscription_service.activate_subscription = AsyncMock(return_value=mock_subscription)
        # Mock get_plan_option to return an object with proper attributes
        mock_plan_option = MagicMock()
        mock_plan_option.name = "1 Month"
        mock_plan_option.plan_type = PlanType.ONE_MONTH
        mock_plan_option.stars = 360  # This is the key attribute
        subscription_service.get_plan_option = MagicMock(return_value=mock_plan_option)

        context = MagicMock()

        # Act
        await handler.handle_successful_payment(mock_update_successful_payment, context)

        # Assert
        subscription_service.activate_subscription.assert_called_once()
        call_args = subscription_service.activate_subscription.call_args
        assert call_args.kwargs["user_id"] == 12345
        assert call_args.kwargs["plan_type"] == "one-month"
        assert call_args.kwargs["stars_paid"] == 360
        assert call_args.kwargs["payment_id"] == "telegram_txn456"

        mock_update_successful_payment.message.reply_text.assert_called_once()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "✅ *¡SUSCRIPCIÓN ACTIVADA!*" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_invalid_payload_logs_warning(self, handler, mock_update_successful_payment):
        """Test that invalid payload is handled gracefully."""
        # Arrange
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.payload = "invalid_payload"

        context = MagicMock()

        # Act
        await handler.handle_successful_payment(mock_update_successful_payment, context)

        # Assert
        mock_update_successful_payment.message.reply_text.assert_called()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "❌ Error al procesar tu pago" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_amount_mismatch_rejects_payment(
        self, handler, mock_update_successful_payment, subscription_service
    ):
        """Test that payment with wrong amount is rejected."""
        # Arrange
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.payload = "subscription_one-month_12345_txn789"
        successful_payment.total_amount = 100  # Wrong amount (should be 360)

        subscription_service.get_plan_option = MagicMock(
            return_value=MagicMock(name="1 Month", plan_type=PlanType.ONE_MONTH, stars=360)
        )

        context = MagicMock()

        # Act
        await handler.handle_successful_payment(mock_update_successful_payment, context)

        # Assert
        mock_update_successful_payment.message.reply_text.assert_called()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "Monto incorrecto" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_user_mismatch_rejects_payment(
        self, handler, mock_update_successful_payment, subscription_service
    ):
        """Test that payment from wrong user is rejected."""
        # Arrange
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.payload = "subscription_one-month_99999_txn999"
        # User ID in payload (99999) doesn't match actual user (12345)

        mock_plan_option = MagicMock()
        mock_plan_option.name = "1 Month"
        mock_plan_option.plan_type = PlanType.ONE_MONTH
        mock_plan_option.stars = 360
        subscription_service.get_plan_option = MagicMock(return_value=mock_plan_option)

        context = MagicMock()

        # Act
        await handler.handle_successful_payment(mock_update_successful_payment, context)

        # Assert
        mock_update_successful_payment.message.reply_text.assert_called()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "Usuario no coincide" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_invalid_plan_type_rejected(
        self, handler, mock_update_successful_payment, subscription_service
    ):
        """Test that invalid plan type is rejected."""
        # Arrange
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.payload = "subscription_invalid-plan_12345_txn111"

        subscription_service.get_plan_option = MagicMock(return_value=None)

        context = MagicMock()

        # Act
        await handler.handle_successful_payment(mock_update_successful_payment, context)

        # Assert
        mock_update_successful_payment.message.reply_text.assert_called()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "Plan no válido" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_subscription_activation_error_handled(
        self, handler, mock_update_successful_payment, subscription_service
    ):
        """Test that subscription activation errors are handled."""
        # Arrange
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.payload = "subscription_one-month_12345_txn222"

        mock_plan_option = MagicMock()
        mock_plan_option.name = "1 Month"
        mock_plan_option.plan_type = PlanType.ONE_MONTH
        mock_plan_option.stars = 360
        subscription_service.get_plan_option = MagicMock(return_value=mock_plan_option)
        subscription_service.activate_subscription = AsyncMock(
            side_effect=ValueError("User already has active subscription")
        )

        context = MagicMock()

        # Act
        await handler.handle_successful_payment(mock_update_successful_payment, context)

        # Assert
        mock_update_successful_payment.message.reply_text.assert_called()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "User already has active subscription" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_general_exception_handled(
        self, handler, mock_update_successful_payment, subscription_service
    ):
        """Test that general exceptions are handled."""
        # Arrange
        successful_payment = mock_update_successful_payment.message.successful_payment
        successful_payment.payload = "subscription_one-month_12345_txn333"

        subscription_service.get_plan_option = MagicMock(side_effect=Exception("Unexpected error"))

        context = MagicMock()

        # Act
        await handler.handle_successful_payment(mock_update_successful_payment, context)

        # Assert
        mock_update_successful_payment.message.reply_text.assert_called()
        call_args = mock_update_successful_payment.message.reply_text.call_args
        assert "❌ Error al procesar tu pago" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_null_message_ignored(self, handler):
        """Test that updates with null message are ignored."""
        # Arrange
        update = MagicMock(spec=Update)
        update.message = None
        context = MagicMock()

        # Act
        await handler.handle_successful_payment(update, context)

        # Assert - should not raise exception and should not call reply_text
        # (no message to reply to)

    @pytest.mark.asyncio
    async def test_null_successful_payment_ignored(self, handler):
        """Test that updates without successful_payment are ignored."""
        # Arrange
        update = MagicMock(spec=Update)
        update.message = MagicMock()
        update.message.successful_payment = None
        context = MagicMock()

        # Act
        await handler.handle_successful_payment(update, context)

        # Assert - should not raise exception


class TestSubscriptionPaymentHandlerValidation:
    """Tests for payment validation logic."""

    @pytest.fixture
    def subscription_service(self):
        """Mock SubscriptionService."""
        return AsyncMock(spec=SubscriptionService)

    @pytest.fixture
    def handler(self, subscription_service):
        """Create SubscriptionPaymentHandler instance."""
        with patch(
            "telegram_bot.features.subscriptions.handlers_payment.get_service",
            return_value=subscription_service,
        ):
            handler = SubscriptionPaymentHandler()
            handler.subscription_service = subscription_service
            return handler

    @pytest.mark.asyncio
    async def test_validate_payment_success(self, handler, subscription_service):
        """Test successful payment validation."""
        # Arrange
        payment = MagicMock()
        payment.total_amount = 360

        payload_parts = ["subscription", "one-month", "12345", "txn123"]
        user_id = 12345

        subscription_service.get_plan_option = MagicMock(
            return_value=MagicMock(name="1 Month", plan_type=PlanType.ONE_MONTH, stars=360)
        )

        # Act
        is_valid, error_message = await handler._validate_payment(payment, payload_parts, user_id)

        # Assert
        assert is_valid is True
        assert error_message == ""

    @pytest.mark.asyncio
    async def test_validate_payment_invalid_plan(self, handler, subscription_service):
        """Test validation with invalid plan type."""
        # Arrange
        payment = MagicMock()
        payload_parts = ["subscription", "invalid-plan", "12345", "txn123"]
        user_id = 12345

        subscription_service.get_plan_option = MagicMock(return_value=None)

        # Act
        is_valid, error_message = await handler._validate_payment(payment, payload_parts, user_id)

        # Assert
        assert is_valid is False
        assert error_message == "Plan no válido"

    @pytest.mark.asyncio
    async def test_validate_payment_amount_mismatch(self, handler, subscription_service):
        """Test validation with amount mismatch."""
        # Arrange
        payment = MagicMock()
        payment.total_amount = 100  # Wrong amount

        payload_parts = ["subscription", "one-month", "12345", "txn123"]
        user_id = 12345

        subscription_service.get_plan_option = MagicMock(
            return_value=MagicMock(name="1 Month", plan_type=PlanType.ONE_MONTH, stars=360)
        )

        # Act
        is_valid, error_message = await handler._validate_payment(payment, payload_parts, user_id)

        # Assert
        assert is_valid is False
        assert "Monto incorrecto" in error_message

    @pytest.mark.asyncio
    async def test_validate_payment_user_mismatch(self, handler, subscription_service):
        """Test validation with user mismatch."""
        # Arrange
        payment = MagicMock()
        payment.total_amount = 360

        payload_parts = ["subscription", "one-month", "99999", "txn123"]  # Different user
        user_id = 12345

        subscription_service.get_plan_option = MagicMock(
            return_value=MagicMock(name="1 Month", plan_type=PlanType.ONE_MONTH, stars=360)
        )

        # Act
        is_valid, error_message = await handler._validate_payment(payment, payload_parts, user_id)

        # Assert
        assert is_valid is False
        assert "Usuario no coincide" in error_message

    @pytest.mark.asyncio
    async def test_validate_payment_invalid_user_id(self, handler, subscription_service):
        """Test validation with invalid user ID in payload."""
        # Arrange
        payment = MagicMock()
        payment.total_amount = 360

        payload_parts = ["subscription", "one-month", "not_a_number", "txn123"]
        user_id = 12345

        subscription_service.get_plan_option = MagicMock(
            return_value=MagicMock(name="1 Month", plan_type=PlanType.ONE_MONTH, stars=360)
        )

        # Act
        is_valid, error_message = await handler._validate_payment(payment, payload_parts, user_id)

        # Assert
        assert is_valid is False
        assert "ID de usuario inválido" in error_message
