# Telegram Stars Webhook Integration - Design Document

**Created:** 2026-03-16
**Status:** Approved
**Priority:** High
**Estimated Effort:** 6-8 hours

---

## Overview

Implement Telegram Stars payment webhook to automatically confirm and activate subscriptions when users pay via Telegram (outside the Mini App).

---

## Architecture

### Current Flow (Without Webhook)

```
1. User selects plan in Mini App
2. Mini App calls /api/create-stars-invoice
3. Bot sends invoice to user's Telegram chat
4. User pays in Telegram
5. ❌ Manual confirmation required OR user must return to Mini App
```

### New Flow (With Webhook)

```
1. User selects plan in Mini App
2. Mini App calls /api/create-stars-invoice
3. Bot sends invoice to user's Telegram chat
4. User pays in Telegram
5. ✅ Telegram sends webhook to /api/v1/webhooks/telegram-stars
6. Backend automatically activates subscription
7. Bot sends confirmation to user
```

---

## Webhook Endpoint

### URL

```
POST /api/v1/webhooks/telegram-stars
```

### Request Format

Telegram sends `PreCheckoutQuery` and `SuccessfulPayment` updates via bot, NOT via HTTP webhook.

**Correction:** Telegram Stars uses bot updates, not HTTP webhooks like TronDealer.

### Implementation Approach

We'll handle `Message.successful_payment` in the bot handlers:

```python
# telegram_bot/features/subscriptions/handlers_payment.py

from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

from application.services.common.container import get_service
from application.services.subscription_service import SubscriptionService
from utils.logger import logger


class SubscriptionPaymentHandler:
    """Handler for Telegram Stars payment confirmations."""

    def __init__(self):
        self.subscription_service = get_service(SubscriptionService)
        logger.info("💎 SubscriptionPaymentHandler initialized")

    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle successful Telegram Stars payment.

        This is triggered when a user completes payment in Telegram.
        """
        if update.message is None or update.message.successful_payment is None:
            return

        payment = update.message.successful_payment
        user_id = update.effective_user.id

        logger.info(f"⭐ Successful payment received from user {user_id}: {payment.total_amount} stars")

        try:
            # Parse payload to extract product info
            # Format: "subscription_<plan_type>_<user_id>_<transaction_id>"
            payload_parts = payment.payload.split("_")

            if len(payload_parts) < 4 or payload_parts[0] != "subscription":
                logger.warning(f"Invalid subscription payload: {payment.payload}")
                return

            plan_type = payload_parts[1]
            transaction_id = payload_parts[3]

            # Check if already processed (idempotency)
            existing = await self.check_existing_payment(transaction_id)
            if existing:
                logger.info(f"Payment already processed: {transaction_id}")
                return

            # Activate subscription
            subscription = await self.subscription_service.activate_subscription(
                user_id=user_id,
                plan_type=plan_type,
                stars_paid=payment.total_amount,
                payment_id=f"telegram_{transaction_id}",
                current_user_id=settings.ADMIN_ID
            )

            # Send confirmation message
            await self.send_confirmation_message(
                update=update,
                context=context,
                subscription=subscription,
                payment=payment
            )

            logger.info(f"✅ Subscription activated: {subscription.id} for user {user_id}")

        except ValueError as e:
            logger.warning(f"Payment validation failed for user {user_id}: {e}")
            await update.message.reply_text(
                f"⚠️ Error: {e}\n\nPor favor contacta a soporte si el problema persiste."
            )
        except Exception as e:
            logger.error(f"Error processing payment for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Error al procesar tu pago. Por favor contacta a soporte."
            )

    async def check_existing_payment(self, transaction_id: str) -> bool:
        """Check if payment was already processed (idempotency check)."""
        # TODO: Implement in SubscriptionService or separate PaymentLog
        # For now, rely on payment_id uniqueness in subscription_plans table
        return False

    async def send_confirmation_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        subscription,
        payment
    ):
        """Send payment confirmation message to user."""
        from telegram_bot.features.subscriptions.messages import SubscriptionMessages

        expires_at = subscription.expires_at.strftime("%d/%m/%Y")

        message = SubscriptionMessages.Success.subscription_activated(
            plan_name=subscription.plan_type.value,
            stars=payment.total_amount,
            expires_at=expires_at
        )

        await update.message.reply_text(
            text=message,
            parse_mode="Markdown"
        )
```

---

## Invoice Creation Update

### Update Existing Handler

```python
# miniapp/routes_payments.py

@router.post("/api/create-stars-invoice")
async def api_create_stars_invoice(
    payment_req: PaymentRequest,
    ctx: MiniAppContext = Depends(get_current_user),
):
    # ... existing code ...

    elif payment_req.product_type == "subscription":
        # Handle subscription plans
        from application.services.common.container import get_service
        from application.services.subscription_service import SubscriptionService

        subscription_service = get_service(SubscriptionService)
        plan_opt = subscription_service.get_plan_option(payment_req.product_id)

        if not plan_opt:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Plan de suscripción no válido."}
            )

        title = f"Suscripción {plan_opt.name}"
        description = f"{plan_opt.duration_months} meses de datos ilimitados"

        # Payload format: subscription_<plan_type>_<user_id>_<transaction_id>
        payload = f"subscription_{payment_req.product_id}_{ctx.user.id}_{transaction_id}"
        amount = plan_opt.stars

        # Store transaction for tracking
        await store_subscription_transaction(
            transaction_id=transaction_id,
            user_id=ctx.user.id,
            plan_type=payment_req.product_id,
            amount=amount,
            payload=payload
        )

    # ... rest of existing code ...
```

---

## Handler Registration

### Add to Handler Initializer

```python
# telegram_bot/handlers/handler_initializer.py

from telegram_bot.features.subscriptions.handlers_payment import SubscriptionPaymentHandler


def _get_subscription_payment_handlers() -> List[BaseHandler]:
    """Initialize subscription payment handlers."""
    handler = SubscriptionPaymentHandler()

    return [
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            handler.handle_successful_payment
        )
    ]


def initialize_handlers(...) -> List[BaseHandler]:
    # ... existing handlers ...

    # Subscription payment handlers (MUST be registered early)
    handlers.extend(_get_subscription_payment_handlers())
    logger.info("✅ Subscription payment handlers configured")

    return handlers
```

---

## Transaction Tracking

### Temporary Storage

Store pending transactions to prevent fraud and enable reconciliation:

```python
# infrastructure/persistence/postgresql/subscription_transaction_repository.py

from domain.entities.subscription_transaction import SubscriptionTransaction
from domain.interfaces.isubscription_transaction_repository import ISubscriptionTransactionRepository


class PostgresSubscriptionTransactionRepository(ISubscriptionTransactionRepository):
    """Repository for tracking subscription transactions."""

    async def save(self, transaction: SubscriptionTransaction) -> SubscriptionTransaction:
        """Store pending transaction."""
        # Save to subscription_transactions table
        ...

    async def get_by_transaction_id(self, transaction_id: str) -> Optional[SubscriptionTransaction]:
        """Get transaction by ID."""
        ...

    async def mark_completed(self, transaction_id: str) -> bool:
        """Mark transaction as completed (prevent double-processing)."""
        ...
```

### Entity

```python
# domain/entities/subscription_transaction.py

@dataclass
class SubscriptionTransaction:
    """Represents a pending subscription transaction."""

    transaction_id: str
    user_id: int
    plan_type: str
    amount_stars: int
    payload: str
    created_at: datetime
    status: str  # pending, completed, expired
    expires_at: datetime

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        # Transactions expire after 30 minutes
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(minutes=30)
```

---

## Error Handling

### Idempotency

- Use `payment_id` unique constraint in `subscription_plans` table
- Check for existing subscription before activating
- Store transaction IDs to prevent double-processing

### Validation

```python
async def validate_payment(payment, payload_parts) -> Tuple[bool, str]:
    """Validate payment details."""

    # Check amount matches plan
    plan_type = payload_parts[1]
    plan_opt = subscription_service.get_plan_option(plan_type)

    if not plan_opt:
        return False, "Plan no válido"

    if payment.total_amount != plan_opt.stars:
        return False, f"Monto incorrecto. Esperado: {plan_opt.stars}, Recibido: {payment.total_amount}"

    # Check user matches
    expected_user_id = int(payload_parts[2])
    if payment.invoice_payload_user_id != expected_user_id:
        return False, "Usuario no coincide"

    return True, ""
```

---

## Testing

### Unit Tests

```python
# tests/telegram_bot/features/subscriptions/test_handlers_payment.py

class TestSubscriptionPaymentHandler:
    @pytest.mark.asyncio
    async def test_successful_payment_activates_subscription(
        self, mock_subscription_service
    ):
        """Test that successful payment activates subscription."""
        handler = SubscriptionPaymentHandler()
        handler.subscription_service = mock_subscription_service

        update = MockUpdate(
            message=MockMessage(
                successful_payment=MockPayment(
                    total_amount=360,
                    payload="subscription_one_month_123_txn456"
                ),
                user_id=123
            )
        )

        await handler.handle_successful_payment(update, MockContext())

        mock_subscription_service.activate_subscription.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_payload_logs_warning(self, mock_subscription_service):
        """Test that invalid payload is handled gracefully."""
        handler = SubscriptionPaymentHandler()
        handler.subscription_service = mock_subscription_service

        update = MockUpdate(
            message=MockMessage(
                successful_payment=MockPayment(
                    total_amount=360,
                    payload="invalid_payload"
                )
            )
        )

        await handler.handle_successful_payment(update, MockContext())

        mock_subscription_service.activate_subscription.assert_not_called()
```

---

## Security Considerations

### Payment Validation

1. **Amount verification:** Ensure payment amount matches plan price
2. **User verification:** Ensure payer is the intended user
3. **Payload validation:** Parse and validate payload format
4. **Idempotency:** Prevent double-processing with transaction tracking

### Rate Limiting

- Implement rate limiting on invoice creation (max 3 invoices per minute per user)
- Log suspicious activity (multiple failed payments)

---

## Success Criteria

- [ ] Users can pay subscriptions via Telegram
- [ ] Payments automatically activate subscriptions
- [ ] Confirmation messages sent to users
- [ ] Idempotency prevents double-processing
- [ ] Invalid payments are rejected with clear error messages
- [ ] Transaction tracking enables reconciliation
- [ ] Tests cover all payment scenarios

---

## Migration Path

### Phase 1: Manual Confirmation (Current)
Users must return to Mini App to confirm payment.

### Phase 2: Hybrid (Transition)
- Webhook handles automatic confirmation
- Manual confirmation still available as fallback

### Phase 3: Automatic (Target)
- All payments confirmed automatically via webhook
- Manual confirmation removed

---

## Future Enhancements

1. **Refund handling:** Process refund requests via Telegram Bot
2. **Payment plans:** Allow users to change subscription plans
3. **Prorated upgrades:** Credit remaining time when upgrading
4. **Family sharing:** Share subscription across multiple users
5. **Corporate plans:** Bulk subscriptions for businesses
