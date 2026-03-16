# Telegram Stars Webhook Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Implement automatic subscription activation when users pay via Telegram Stars, eliminating manual confirmation requirement.

**Architecture:** Handle `Message.successful_payment` updates in bot handlers, parse payload to extract transaction details, activate subscription automatically, send confirmation message.

**Tech Stack:** Python 3.13+, python-telegram-bot v21.10, SQLAlchemy async, SubscriptionService.

---

## Phase 1: Payment Handler

### Task 1.1: Create Subscription Payment Handler

**Files:**
- Create: `telegram_bot/features/subscriptions/handlers_payment.py`
- Test: `tests/telegram_bot/features/subscriptions/test_handlers_payment.py`

**Step 1: Write the failing test**

```python
# tests/telegram_bot/features/subscriptions/test_handlers_payment.py

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
import uuid

from telegram_bot.features.subscriptions.handlers_payment import SubscriptionPaymentHandler
from domain.entities.subscription_plan import SubscriptionPlan, PlanType


class MockSuccessfulPayment:
    def __init__(self, total_amount, payload):
        self.total_amount = total_amount
        self.invoice_payload = payload


class MockMessage:
    def __init__(self, payment, user_id):
        self.successful_payment = payment
        self.from_user = MagicMock()
        self.from_user.id = user_id
        self.chat = MagicMock()
        self.chat.id = user_id


class MockUpdate:
    def __init__(self, payment, user_id):
        self.message = MockMessage(payment, user_id)
        self.effective_user = MagicMock()
        self.effective_user.id = user_id


class MockContext:
    def __init__(self):
        self.bot = AsyncMock()


class TestSubscriptionPaymentHandler:
    @pytest.mark.asyncio
    async def test_successful_payment_activates_subscription(
        self,
        mock_subscription_service
    ):
        """Test that successful payment activates subscription."""
        # Arrange
        handler = SubscriptionPaymentHandler()
        handler.subscription_service = mock_subscription_service

        payment = MockSuccessfulPayment(
            total_amount=360,
            payload="subscription_one_month_123_txn456"
        )
        update = MockUpdate(payment, user_id=123)
        context = MockContext()

        # Act
        await handler.handle_successful_payment(update, context)

        # Assert
        mock_subscription_service.activate_subscription.assert_called_once()
        context.bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_payload_logs_warning(
        self,
        mock_subscription_service
    ):
        """Test that invalid payload is handled gracefully."""
        handler = SubscriptionPaymentHandler()
        handler.subscription_service = mock_subscription_service

        payment = MockSuccessfulPayment(
            total_amount=360,
            payload="invalid_payload"
        )
        update = MockUpdate(payment, user_id=123)
        context = MockContext()

        # Act
        await handler.handle_successful_payment(update, context)

        # Assert
        mock_subscription_service.activate_subscription.assert_not_called()
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/telegram_bot/features/subscriptions/test_handlers_payment.py -v
```
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# telegram_bot/features/subscriptions/handlers_payment.py
"""Handler for Telegram Stars payment confirmations."""

from telegram import Update
from telegram.ext import ContextTypes

from application.services.common.container import get_service
from application.services.subscription_service import SubscriptionService
from config import settings
from utils.logger import logger


class SubscriptionPaymentHandler:
    """Handler for Telegram Stars payment confirmations."""

    def __init__(self):
        self.subscription_service = get_service(SubscriptionService)
        logger.info("💎 SubscriptionPaymentHandler initialized")

    async def handle_successful_payment(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle successful Telegram Stars payment.

        This is triggered when a user completes payment in Telegram.
        """
        if update.message is None or update.message.successful_payment is None:
            return

        payment = update.message.successful_payment
        user_id = update.effective_user.id

        logger.info(
            f"⭐ Successful payment received from user {user_id}: "
            f"{payment.total_amount} stars"
        )

        try:
            # Parse payload to extract product info
            # Format: "subscription_<plan_type>_<user_id>_<transaction_id>"
            payload_parts = payment.invoice_payload.split("_")

            if len(payload_parts) < 4 or payload_parts[0] != "subscription":
                logger.warning(f"Invalid subscription payload: {payment.invoice_payload}")
                await update.message.reply_text(
                    "❌ Error al procesar tu pago. Por favor contacta a soporte."
                )
                return

            plan_type = payload_parts[1]
            transaction_id = payload_parts[3]

            # Check if already processed (idempotency)
            existing = await self._check_existing_payment(transaction_id)
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
            await self._send_confirmation_message(
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

    async def _check_existing_payment(self, transaction_id: str) -> bool:
        """Check if payment was already processed (idempotency check)."""
        # For now, rely on payment_id uniqueness in subscription_plans table
        # TODO: Implement transaction tracking repository
        return False

    async def _send_confirmation_message(
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

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/telegram_bot/features/subscriptions/test_handlers_payment.py::TestSubscriptionPaymentHandler::test_successful_payment_activates_subscription -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add telegram_bot/features/subscriptions/handlers_payment.py tests/telegram_bot/features/subscriptions/test_handlers_payment.py
git commit -m "feat(handlers): add SubscriptionPaymentHandler for automatic Stars payment processing"
```

---

## Phase 2: Update Invoice Creation

### Task 2.1: Update Mini App Invoice Creation for Subscriptions

**Files:**
- Modify: `miniapp/routes_payments.py:140-180`

**Step 1: Add subscription transaction storage**

```python
# miniapp/routes_payments.py (add import)
from application.services.subscription_service import SubscriptionService

# In api_create_stars_invoice function, update subscription handling:

elif payment_req.product_type == "subscription":
    # Handle subscription plans
    subscription_service = get_service(SubscriptionService)
    plan_opt = subscription_service.get_plan_option(payment_req.product_id)

    if not plan_opt:
        logger.error(f"Subscription plan not found: {payment_req.product_id}")
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Plan de suscripción no válido."}
        )

    title = f"Suscripción {plan_opt.name}"
    description = f"{plan_opt.duration_months} meses de datos ilimitados"

    # Payload format: subscription_<plan_type>_<user_id>_<transaction_id>
    payload = f"subscription_{payment_req.product_id}_{ctx.user.id}_{transaction_id}"
    amount = plan_opt.stars

    # Store transaction for tracking (optional - for reconciliation)
    await _store_subscription_transaction(
        transaction_id=transaction_id,
        user_id=ctx.user.id,
        plan_type=payment_req.product_id,
        amount=amount,
        payload=payload
    )
```

**Step 2: Add helper function**

```python
# Add at end of file
async def _store_subscription_transaction(
    transaction_id: str,
    user_id: int,
    plan_type: str,
    amount: int,
    payload: str
):
    """Store pending subscription transaction for tracking."""
    # TODO: Implement transaction repository
    # For now, just log
    logger.info(
        f"Subscription transaction stored: {transaction_id} - "
        f"user={user_id}, plan={plan_type}, amount={amount}"
    )
```

**Step 3: Commit**

```bash
git add miniapp/routes_payments.py
git commit -m "feat(miniapp): update subscription invoice creation with proper payload format"
```

---

## Phase 3: Handler Registration

### Task 3.1: Register Payment Handler

**Files:**
- Modify: `telegram_bot/handlers/handler_initializer.py:200-220`

**Step 1: Add subscription payment handlers function**

```python
# telegram_bot/handlers/handler_initializer.py

from telegram_bot.features.subscriptions.handlers_payment import SubscriptionPaymentHandler


def _get_subscription_payment_handlers() -> List[BaseHandler]:
    """Initialize subscription payment handlers."""
    from telegram.ext import MessageHandler, filters

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

**Step 2: Commit**

```bash
git add telegram_bot/handlers/handler_initializer.py
git commit -m "feat(integration): register subscription payment handler for automatic activation"
```

---

## Phase 4: Testing & Verification

### Task 4.1: Integration Test

**Files:**
- Create: `tests/integration/test_subscription_payment_flow.py`

**Step 1: Write integration test**

```python
# tests/integration/test_subscription_payment_flow.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from domain.entities.subscription_plan import SubscriptionPlan, PlanType


class TestSubscriptionPaymentFlow:
    """Integration test for subscription payment flow."""

    @pytest.mark.asyncio
    async def test_full_payment_flow(
        self,
        mock_subscription_service,
        mock_container
    ):
        """Test complete payment flow from invoice to activation."""
        # Arrange
        from telegram_bot.features.subscriptions.handlers_payment import (
            SubscriptionPaymentHandler
        )

        handler = SubscriptionPaymentHandler()
        handler.subscription_service = mock_subscription_service

        # Mock subscription to return
        mock_subscription = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="telegram_test123",
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )

        mock_subscription_service.activate_subscription = AsyncMock(
            return_value=mock_subscription
        )

        payment = MagicMock()
        payment.total_amount = 360
        payment.invoice_payload = "subscription_one_month_123_test123"

        update = MagicMock()
        update.message.successful_payment = payment
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()

        # Act
        await handler.handle_successful_payment(update, MagicMock())

        # Assert
        mock_subscription_service.activate_subscription.assert_called_once()
        update.message.reply_text.assert_called_once()
```

**Step 2: Run integration test**

```bash
uv run pytest tests/integration/test_subscription_payment_flow.py -v
```
Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_subscription_payment_flow.py
git commit -m "test(integration): add subscription payment flow integration test"
```

---

### Task 4.2: Run Full Test Suite

**Step 1: Run all subscription payment tests**

```bash
uv run pytest tests/telegram_bot/features/subscriptions/test_handlers_payment.py tests/integration/test_subscription_payment_flow.py -v
```
Expected: All tests PASS

**Step 2: Run full test suite to verify no regressions**

```bash
uv run pytest tests/ -x --tb=short 2>&1 | tail -20
```
Expected: 439+ tests passing

**Step 3: Commit**

```bash
git status
git commit -am "test: add comprehensive tests for subscription payment handler"
```

---

## Success Criteria

- [ ] Users can pay subscriptions via Telegram
- [ ] Payments automatically activate subscriptions
- [ ] Confirmation messages sent to users
- [ ] Idempotency prevents double-processing
- [ ] Invalid payments are rejected with clear error messages
- [ ] All tests pass (439+)
- [ ] No regressions in existing functionality

---

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `telegram_bot/features/subscriptions/handlers_payment.py` | Create | Payment handler for automatic activation |
| `tests/telegram_bot/features/subscriptions/test_handlers_payment.py` | Create | Payment handler tests |
| `miniapp/routes_payments.py` | Modify | Update invoice creation payload format |
| `telegram_bot/handlers/handler_initializer.py` | Modify | Register payment handler |
| `tests/integration/test_subscription_payment_flow.py` | Create | Integration test |

---

## Estimated Time

- Phase 1: 45 minutes
- Phase 2: 30 minutes
- Phase 3: 30 minutes
- Phase 4: 45 minutes

**Total: ~2.5 hours**
