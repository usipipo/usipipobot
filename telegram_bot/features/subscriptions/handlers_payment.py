"""
Payment handlers for Telegram Stars subscription payments.

Handles successful payment webhooks from Telegram to automatically
activate subscriptions when users pay via Telegram (outside Mini App).

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from application.services.common.container import get_service
from application.services.subscription_service import SubscriptionService
from config import settings
from utils.logger import logger

from .messages import SubscriptionMessages

__all__ = ["SubscriptionPaymentHandler"]


class SubscriptionPaymentHandler:
    """Handler for Telegram Stars payment confirmations."""

    def __init__(self):
        self.subscription_service = get_service(SubscriptionService)
        logger.info("⭐ SubscriptionPaymentHandler initialized")

    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle successful Telegram Stars payment.

        This is triggered when a user completes payment in Telegram.
        Payment flow:
        1. User selects plan in Mini App
        2. Bot sends invoice to user's Telegram chat
        3. User pays in Telegram
        4. This handler receives the successful_payment update
        5. Subscription is automatically activated
        """
        if update.message is None or update.message.successful_payment is None:
            return

        payment = update.message.successful_payment
        user_id = update.effective_user.id

        logger.info(
            f"⭐ Successful payment received from user {user_id}: {payment.total_amount} stars"
        )

        try:
            # Parse payload to extract product info
            # Format: "subscription_<plan_type>_<user_id>_<transaction_id>"
            payload_parts = payment.payload.split("_")

            if len(payload_parts) < 4 or payload_parts[0] != "subscription":
                logger.warning(f"Invalid subscription payload: {payment.payload}")
                await update.message.reply_text(
                    text="❌ Error al procesar tu pago. El formato del pago no es válido.\n\nPor favor contacta a soporte si el problema persiste.",
                    parse_mode="Markdown",
                )
                return

            plan_type = payload_parts[1]
            # payload_parts[2] is user_id (we'll verify against actual user)
            transaction_id = payload_parts[3]

            # Validate payment details
            is_valid, error_message = await self._validate_payment(payment, payload_parts, user_id)
            if not is_valid:
                logger.warning(f"Payment validation failed for user {user_id}: {error_message}")
                await update.message.reply_text(
                    text=f"⚠️ Error: {error_message}\n\nPor favor contacta a soporte si el problema persiste.",
                    parse_mode="Markdown",
                )
                return

            # Check if already processed (idempotency)
            existing = await self._check_existing_payment(transaction_id)
            if existing:
                logger.info(f"Payment already processed: {transaction_id}")
                await update.message.reply_text(
                    text="✅ Tu pago ya fue procesado anteriormente.\n\nTu suscripción debería estar activa. Usa /premium para verificar.",
                    parse_mode="Markdown",
                )
                return

            # Activate subscription
            subscription = await self.subscription_service.activate_subscription(
                user_id=user_id,
                plan_type=plan_type,
                stars_paid=payment.total_amount,
                payment_id=f"telegram_{transaction_id}",
                current_user_id=settings.ADMIN_ID,
            )

            # Send confirmation message
            await self._send_confirmation_message(
                update=update,
                context=context,
                subscription=subscription,
                payment=payment,
            )

            logger.info(f"✅ Subscription activated: {subscription.id} for user {user_id}")

        except ValueError as e:
            logger.warning(f"Payment validation failed for user {user_id}: {e}")
            await update.message.reply_text(
                text=f"⚠️ Error: {e}\n\nPor favor contacta a soporte si el problema persiste.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error processing payment for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(
                text="❌ Error al procesar tu pago. Por favor contacta a soporte.",
                parse_mode="Markdown",
            )

    async def _validate_payment(
        self, payment, payload_parts: list[str], user_id: int
    ) -> tuple[bool, str]:
        """
        Validate payment details.

        Args:
            payment: SuccessfulPayment object
            payload_parts: Parsed payload parts
            user_id: Telegram user ID

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check amount matches plan
        plan_type = payload_parts[1]
        plan_opt = self.subscription_service.get_plan_option(plan_type)

        if not plan_opt:
            return False, "Plan no válido"

        if payment.total_amount != plan_opt.stars:
            logger.warning(
                f"Amount mismatch: expected {plan_opt.stars}, received {payment.total_amount}"
            )
            return (
                False,
                f"Monto incorrecto. Esperado: {plan_opt.stars}, Recibido: {payment.total_amount}",
            )

        # Check user matches (payload_parts[2] should be user_id)
        try:
            expected_user_id = int(payload_parts[2])
            if expected_user_id != user_id:
                logger.warning(f"User mismatch: expected {expected_user_id}, got {user_id}")
                return False, "Usuario no coincide con el pago"
        except ValueError:
            return False, "ID de usuario inválido en el pago"

        return True, ""

    async def _check_existing_payment(self, transaction_id: str) -> bool:
        """
        Check if payment was already processed (idempotency check).

        For now, rely on payment_id uniqueness in subscription_plans table.
        TODO: Implement proper transaction tracking with SubscriptionTransactionRepository
        """
        # TODO: Implement transaction tracking
        # For now, the subscription_service.activate_subscription should handle
        # duplicate payment_id via database unique constraint
        return False

    async def _send_confirmation_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        subscription,
        payment,
    ):
        """Send payment confirmation message to user."""
        expires_at = subscription.expires_at.strftime("%d/%m/%Y")

        plan_option = self.subscription_service.get_plan_option(subscription.plan_type.value)
        plan_name = plan_option.name if plan_option else subscription.plan_type.value

        message = SubscriptionMessages.Success.subscription_activated(
            plan_name=plan_name,
            stars=payment.total_amount,
            expires_at=expires_at,
        )

        # Import keyboard here to avoid circular imports
        from .keyboards import SubscriptionKeyboards

        await update.message.reply_text(
            text=message,
            reply_markup=SubscriptionKeyboards.subscription_status(),
            parse_mode="Markdown",
        )


def get_subscription_payment_handlers() -> list:
    """
    Get subscription payment handlers.

    Returns:
        List of MessageHandler instances for subscription payments
    """
    handler = SubscriptionPaymentHandler()

    return [
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            handler.handle_successful_payment,
        )
    ]
