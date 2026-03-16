# Subscription Expiration Jobs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Implement automated background jobs to manage subscription lifecycle with expiration handling and renewal reminders.

**Architecture:** Two independent APScheduler jobs running daily - one for expiration (2 AM UTC), one for reminders (9 AM UTC). Both jobs use SubscriptionService and send Telegram notifications.

**Tech Stack:** Python 3.13+, APScheduler (telegram.ext.job_queue), SQLAlchemy async, Pydantic v2.

---

## Phase 1: Notification Messages

### Task 1.1: Create Subscription Notification Messages

**Files:**
- Create: `telegram_bot/features/subscriptions/messages_notifications.py`
- Test: `tests/telegram_bot/features/subscriptions/test_messages_notifications.py`

**Step 1: Write the test**

```python
# tests/telegram_bot/features/subscriptions/test_messages_notifications.py

import pytest
from telegram_bot.features.subscriptions.messages_notifications import (
    SubscriptionReminderMessages,
    SubscriptionExpiredMessages,
)


class TestSubscriptionReminderMessages:
    def test_urgent_reminder_format(self):
        """Test urgent reminder message format."""
        message = SubscriptionReminderMessages.urgent(
            plan_name="3 Meses",
            days_remaining=2,
            expires_at="25/03/2026"
        )

        assert "🚨" in message
        assert "ÚLTIMOS DÍAS" in message
        assert "2 días" in message
        assert "25/03/2026" in message

    def test_standard_reminder_format(self):
        """Test standard reminder message format."""
        message = SubscriptionReminderMessages.standard(
            plan_name="1 Mes",
            days_remaining=5,
            expires_at="28/03/2026"
        )

        assert "📅" in message
        assert "RECORDATORIO" in message
        assert "5 días" in message


class TestSubscriptionExpiredMessages:
    def test_expired_notification_format(self):
        """Test expired subscription notification."""
        message = SubscriptionExpiredMessages.expired(
            plan_name="6 Meses",
            expired_date="15/03/2026"
        )

        assert "⚠️" in message
        assert "EXPIRADA" in message
        assert "15/03/2026" in message
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/telegram_bot/features/subscriptions/test_messages_notifications.py -v
```
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# telegram_bot/features/subscriptions/messages_notifications.py
"""Mensajes de notificación para suscripciones."""

from utils.message_separators import (
    TELEGRAM_MOBILE_WIDTH,
    MessageSeparatorBuilder,
)

_SEP_HEADER = (
    MessageSeparatorBuilder().compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_DIVIDER = (
    MessageSeparatorBuilder().compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
)


class SubscriptionReminderMessages:
    """Mensajes de recordatorio de renovación."""

    @staticmethod
    def urgent(plan_name: str, days_remaining: int, expires_at: str) -> str:
        """Generate urgent reminder (3 days)."""
        return (
            f"{_SEP_HEADER}\n"
            f"🚨 *ÚLTIMOS DÍAS*\n"
            f"{_SEP_HEADER}\n"
            "\n"
            f"Tu suscripción {plan_name} vence en *{days_remaining} días*\n"
            "\n"
            f"*Fecha de vencimiento:* {expires_at}\n"
            f"{_SEP_DIVIDER}\n"
            "⚠️ *No pierdas tus beneficios Premium!*\n"
            "\n"
            "Renueva ahora para mantener:\n"
            "│\n"
            "├─ 🌐 Datos ilimitados\n"
            "├─ ⚡ Velocidad prioritaria\n"
            "└─ 🎯 Soporte prioritario\n"
            f"\n{_SEP_DIVIDER}\n"
            "👇 *Renovar ahora:*\n"
        )

    @staticmethod
    def standard(plan_name: str, days_remaining: int, expires_at: str) -> str:
        """Generate standard reminder (7 days)."""
        return (
            f"{_SEP_HEADER}\n"
            f"📅 *RECORDATORIO DE RENOVACIÓN*\n"
            f"{_SEP_HEADER}\n"
            "\n"
            f"Tu suscripción {plan_name} vence en *{days_remaining} días*\n"
            "\n"
            f"*Fecha de vencimiento:* {expires_at}\n"
            f"{_SEP_DIVIDER}\n"
            "💡 *Consejo:* Renueva con anticipación para evitar interrupciones\n"
            f"\n{_SEP_DIVIDER}\n"
            "👇 *Ver planes de renovación:*\n"
        )


class SubscriptionExpiredMessages:
    """Mensajes de suscripción expirada."""

    @staticmethod
    def expired(plan_name: str, expired_date: str) -> str:
        """Generate expired subscription notification."""
        return (
            f"{_SEP_HEADER}\n"
            "⚠️ *SUSCRIPCIÓN EXPIRADA*\n"
            f"{_SEP_HEADER}\n"
            "\n"
            "Tu suscripción Premium ha expirado.\n"
            "\n"
            f"*Plan:* {plan_name}\n"
            f"*Fecha de expiración:* {expired_date}\n"
            f"{_SEP_DIVIDER}\n"
            "🔓 *Estado actual:* Datos limitados (10 GB)\n"
            "\n"
            "¿Quieres renovar para recuperar datos ilimitados?\n"
            f"\n{_SEP_DIVIDER}\n"
            "👇 *Toca para renovar:*\n"
        )
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/telegram_bot/features/subscriptions/test_messages_notifications.py -v
```
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add telegram_bot/features/subscriptions/messages_notifications.py tests/telegram_bot/features/subscriptions/test_messages_notifications.py
git commit -m "feat(messages): add subscription reminder and expired notification messages"
```

---

## Phase 2: Expiration Job

### Task 2.1: Create Subscription Expiration Job

**Files:**
- Create: `infrastructure/jobs/subscription_expiration_job.py`
- Test: `tests/infrastructure/jobs/test_subscription_expiration_job.py`

**Step 1: Write the failing test**

```python
# tests/infrastructure/jobs/test_subscription_expiration_job.py

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime, timezone, timedelta
import uuid

from infrastructure.jobs.subscription_expiration_job import subscription_expiration_job
from domain.entities.subscription_plan import SubscriptionPlan, PlanType


class MockContext:
    def __init__(self, data):
        self.job = MagicMock()
        self.job.data = data
        self.bot = AsyncMock()


class TestSubscriptionExpirationJob:
    @pytest.mark.asyncio
    async def test_expire_active_subscriptions(
        self,
        mock_subscription_service,
        mock_notification_service
    ):
        """Test that job deactivates expired subscriptions."""
        # Arrange
        expired_plan = SubscriptionPlan(
            id=uuid.uuid4(),
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="test_pay",
            starts_at=datetime.now(timezone.utc) - timedelta(days=35),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True
        )

        mock_subscription_service.get_expired_subscriptions.return_value = [expired_plan]
        mock_subscription_service.cancel_subscription = AsyncMock()

        context = MockContext({
            "subscription_service": mock_subscription_service,
            "notification_service": mock_notification_service
        })

        # Act
        await subscription_expiration_job(context)

        # Assert
        mock_subscription_service.cancel_subscription.assert_called_once()
        mock_notification_service.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_expire_no_subscriptions(self, mock_subscription_service):
        """Test job handles empty list gracefully."""
        mock_subscription_service.get_expired_subscriptions.return_value = []

        context = MockContext({
            "subscription_service": mock_subscription_service
        })

        # Act
        await subscription_expiration_job(context)

        # Assert
        mock_subscription_service.cancel_subscription.assert_not_called()
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/infrastructure/jobs/test_subscription_expiration_job.py -v
```
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# infrastructure/jobs/subscription_expiration_job.py
"""Job para expirar suscripciones que han pasado su fecha de expiración."""

from typing import Any, Dict, cast

from telegram.ext import ContextTypes

from application.services.subscription_service import SubscriptionService
from config import settings
from utils.logger import logger


async def subscription_expiration_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job programado que desactiva suscripciones expiradas.

    Schedule: Daily at 02:00 AM UTC
    """
    if context.job is None or context.job.data is None:
        logger.error("❌ Job data no disponible")
        return

    data = cast(Dict[str, Any], context.job.data)
    subscription_service: SubscriptionService = data["subscription_service"]
    notification_service = data.get("notification_service")

    try:
        logger.info("💎 Iniciando job de expiración de suscripciones...")

        # Get all expired subscriptions
        expired_plans = await subscription_service.get_expired_subscriptions(
            current_user_id=settings.ADMIN_ID
        )

        deactivated_count = 0
        failed_count = 0

        for plan in expired_plans:
            try:
                # Deactivate subscription
                await subscription_service.cancel_subscription(
                    user_id=plan.user_id,
                    current_user_id=settings.ADMIN_ID
                )

                # Send notification to user
                if notification_service:
                    from telegram_bot.features.subscriptions.messages_notifications import (
                        SubscriptionExpiredMessages
                    )

                    message = SubscriptionExpiredMessages.expired(
                        plan_name=plan.plan_type.value,
                        expired_date=plan.expires_at.strftime("%d/%m/%Y")
                    )

                    await notification_service.send_message(
                        user_id=plan.user_id,
                        text=message,
                        parse_mode="Markdown"
                    )

                deactivated_count += 1
                logger.info(f"✅ Suscripción expirada desactivada: user={plan.user_id}")

            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Error desactivando suscripción {plan.id}: {e}")

        # Report to admin if there were any actions
        if deactivated_count > 0 or failed_count > 0:
            await _notify_admin_summary(
                context=context,
                deactivated=deactivated_count,
                failed=failed_count
            )

        logger.info(
            f"✅ Job completado: {deactivated_count} suscripciones expiradas, "
            f"{failed_count} fallidas"
        )

    except Exception as e:
        logger.error(f"❌ Error en job de expiración de suscripciones: {e}")


async def _notify_admin_summary(context, deactivated: int, failed: int):
    """Send daily summary to admin."""
    from datetime import datetime

    message = (
        f"📊 *Reporte de Expiración de Suscripciones*\n\n"
        f"✅ Expiradas: {deactivated}\n"
        f"❌ Fallidas: {failed}\n\n"
        f"🕐 Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    if failed > 0:
        message += "\n\n⚠️ *Requiere atención manual*"

    await context.bot.send_message(
        chat_id=settings.ADMIN_ID,
        text=message,
        parse_mode="Markdown"
    )
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/infrastructure/jobs/test_subscription_expiration_job.py::TestSubscriptionExpirationJob::test_expire_active_subscriptions -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add infrastructure/jobs/subscription_expiration_job.py tests/infrastructure/jobs/test_subscription_expiration_job.py
git commit -m "feat(jobs): add subscription expiration job with admin notifications"
```

---

## Phase 3: Reminder Job

### Task 3.1: Create Subscription Reminder Job

**Files:**
- Create: `infrastructure/jobs/subscription_reminder_job.py`
- Test: `tests/infrastructure/jobs/test_subscription_reminder_job.py`

**Step 1: Write the failing test**

```python
# tests/infrastructure/jobs/test_subscription_reminder_job.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
import uuid

from infrastructure.jobs.subscription_reminder_job import subscription_reminder_job
from domain.entities.subscription_plan import SubscriptionPlan, PlanType


class MockContext:
    def __init__(self, data):
        self.job = MagicMock()
        self.job.data = data
        self.bot = AsyncMock()


class TestSubscriptionReminderJob:
    @pytest.mark.asyncio
    async def test_send_reminders(self, mock_subscription_service):
        """Test that job sends reminders for expiring subscriptions."""
        # Arrange
        urgent_plan = SubscriptionPlan(
            id=uuid.uuid4(),
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="test_pay",
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
            is_active=True
        )

        mock_subscription_service.get_expiring_subscriptions = AsyncMock(
            side_effect=[
                [urgent_plan],  # 3 days
                [urgent_plan]   # 7 days
            ]
        )

        context = MockContext({
            "subscription_service": mock_subscription_service
        })

        # Act
        await subscription_reminder_job(context)

        # Assert
        assert mock_subscription_service.get_expiring_subscriptions.call_count == 2
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/infrastructure/jobs/test_subscription_reminder_job.py -v
```
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# infrastructure/jobs/subscription_reminder_job.py
"""Job para enviar recordatorios de renovación de suscripciones."""

from typing import Any, Dict, cast

from telegram.ext import ContextTypes

from application.services.subscription_service import SubscriptionService
from config import settings
from utils.logger import logger


async def subscription_reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job programado que envía recordatorios de renovación.

    Schedule: Daily at 09:00 AM UTC
    """
    if context.job is None or context.job.data is None:
        logger.error("❌ Job data no disponible")
        return

    data = cast(Dict[str, Any], context.job.data)
    subscription_service: SubscriptionService = data["subscription_service"]

    try:
        logger.info("🔔 Iniciando job de recordatorios de suscripción...")

        # Get subscriptions expiring in 3 days (urgent)
        urgent_plans = await subscription_service.get_expiring_subscriptions(
            days=3,
            current_user_id=settings.ADMIN_ID
        )

        # Get subscriptions expiring in 7 days (reminder)
        reminder_plans = await subscription_service.get_expiring_subscriptions(
            days=7,
            current_user_id=settings.ADMIN_ID
        )

        # Remove duplicates (3-day plans already in 7-day list)
        urgent_ids = {p.id for p in urgent_plans}
        reminder_only = [p for p in reminder_plans if p.id not in urgent_ids]

        sent_count = 0

        # Send urgent reminders (3 days)
        for plan in urgent_plans:
            await _send_urgent_reminder(plan, subscription_service)
            sent_count += 1

        # Send standard reminders (7 days)
        for plan in reminder_only:
            await _send_standard_reminder(plan, subscription_service)
            sent_count += 1

        logger.info(f"✅ Job completado: {sent_count} recordatorios enviados")

    except Exception as e:
        logger.error(f"❌ Error en job de recordatorios: {e}")


async def _send_urgent_reminder(plan, subscription_service):
    """Send urgent reminder (3 days)."""
    from telegram_bot.features.subscriptions.messages_notifications import (
        SubscriptionReminderMessages
    )
    from telegram_bot.features.subscriptions.keyboards import SubscriptionKeyboards

    plan_option = subscription_service.get_plan_option(plan.plan_type.value)
    plan_name = plan_option.name if plan_option else plan.plan_type.value

    message = SubscriptionReminderMessages.urgent(
        plan_name=plan_name,
        days_remaining=plan.days_remaining,
        expires_at=plan.expires_at.strftime("%d/%m/%Y")
    )

    # Send via Telegram Bot
    await _send_telegram_message(
        user_id=plan.user_id,
        text=message,
        reply_markup=SubscriptionKeyboards.renew_now(plan.plan_type.value),
        parse_mode="Markdown"
    )

    logger.info(f"🔔 Urgent reminder sent to user {plan.user_id}")


async def _send_standard_reminder(plan, subscription_service):
    """Send standard reminder (7 days)."""
    from telegram_bot.features.subscriptions.messages_notifications import (
        SubscriptionReminderMessages
    )
    from telegram_bot.features.subscriptions.keyboards import SubscriptionKeyboards

    plan_option = subscription_service.get_plan_option(plan.plan_type.value)
    plan_name = plan_option.name if plan_option else plan.plan_type.value

    message = SubscriptionReminderMessages.standard(
        plan_name=plan_name,
        days_remaining=plan.days_remaining,
        expires_at=plan.expires_at.strftime("%d/%m/%Y")
    )

    # Send via Telegram Bot
    await _send_telegram_message(
        user_id=plan.user_id,
        text=message,
        reply_markup=SubscriptionKeyboards.renew_now(plan.plan_type.value),
        parse_mode="Markdown"
    )

    logger.info(f"📅 Standard reminder sent to user {plan.user_id}")


async def _send_telegram_message(user_id: int, text: str, reply_markup=None, parse_mode: str = "Markdown"):
    """Send Telegram message to user."""
    from telegram_bot.features.tickets.ticket_notification_service import TicketNotificationService
    from application.services.common.container import get_service

    notification_service = get_service(TicketNotificationService)
    await notification_service.send_message(
        user_id=user_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/infrastructure/jobs/test_subscription_reminder_job.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add infrastructure/jobs/subscription_reminder_job.py tests/infrastructure/jobs/test_subscription_reminder_job.py
git commit -m "feat(jobs): add subscription reminder job with urgent and standard notifications"
```

---

## Phase 4: Integration

### Task 4.1: Add Renew Now Keyboard

**Files:**
- Modify: `telegram_bot/features/subscriptions/keyboards.py:45-60`

**Step 1: Add renew_now keyboard method**

```python
# telegram_bot/features/subscriptions/keyboards.py

@staticmethod
def renew_now(plan_type: str) -> InlineKeyboardMarkup:
    """Keyboard for renew now CTA."""
    keyboard = [
        [
            InlineKeyboardButton(
                "💳 Renovar Ahora",
                callback_data=f"sub_{plan_type}"
            ),
        ],
        [InlineKeyboardButton("❌ Más Tarde", callback_data="dismiss_reminder")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 2: Commit**

```bash
git add telegram_bot/features/subscriptions/keyboards.py
git commit -m "feat(keyboards): add renew_now CTA keyboard for subscription reminders"
```

---

### Task 4.2: Register Jobs in Handler Initializer

**Files:**
- Modify: `telegram_bot/handlers/handler_initializer.py:180-200`

**Step 1: Add job registration**

```python
# telegram_bot/handlers/handler_initializer.py

from infrastructure.jobs.subscription_expiration_job import subscription_expiration_job
from infrastructure.jobs.subscription_reminder_job import subscription_reminder_job


async def post_init(application: Application) -> None:
    """Register background jobs after bot initialization."""

    # ... existing jobs ...

    # Subscription expiration job (daily at 02:00 AM UTC)
    application.job_queue.run_daily(
        subscription_expiration_job,
        time=datetime.time(2, 0, 0, tzinfo=timezone.utc),
        data={
            "subscription_service": get_service(SubscriptionService),
            "notification_service": get_service(TicketNotificationService),
        },
        name="subscription_expiration_job"
    )
    logger.info("✅ Subscription expiration job scheduled (daily @ 02:00 UTC)")

    # Subscription reminder job (daily at 09:00 AM UTC)
    application.job_queue.run_daily(
        subscription_reminder_job,
        time=datetime.time(9, 0, 0, tzinfo=timezone.utc),
        data={
            "subscription_service": get_service(SubscriptionService),
        },
        name="subscription_reminder_job"
    )
    logger.info("✅ Subscription reminder job scheduled (daily @ 09:00 UTC)")
```

**Step 2: Add imports**

```python
# At top of file
from datetime import datetime, timezone
from application.services.subscription_service import SubscriptionService
from application.services.ticket_notification_service import TicketNotificationService
from application.services.common.container import get_service
```

**Step 3: Commit**

```bash
git add telegram_bot/handlers/handler_initializer.py
git commit -m "feat(integration): register subscription expiration and reminder jobs"
```

---

## Phase 5: Testing & Verification

### Task 5.1: Run Full Test Suite

**Step 1: Run all subscription job tests**

```bash
uv run pytest tests/infrastructure/jobs/test_subscription_*.py tests/telegram_bot/features/subscriptions/test_messages_notifications.py -v
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
git commit -am "test: add comprehensive tests for subscription jobs"
```

---

## Success Criteria

- [ ] Expiration job runs daily at 2 AM UTC
- [ ] Reminder job runs daily at 9 AM UTC
- [ ] Expired subscriptions are deactivated automatically
- [ ] Users receive expiration notifications
- [ ] Users receive 3-day and 7-day renewal reminders
- [ ] Admin receives daily summary report
- [ ] All tests pass (439+)
- [ ] No regressions in existing functionality

---

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `telegram_bot/features/subscriptions/messages_notifications.py` | Create | Notification message templates |
| `tests/telegram_bot/features/subscriptions/test_messages_notifications.py` | Create | Message tests |
| `infrastructure/jobs/subscription_expiration_job.py` | Create | Expiration job |
| `tests/infrastructure/jobs/test_subscription_expiration_job.py` | Create | Expiration job tests |
| `infrastructure/jobs/subscription_reminder_job.py` | Create | Reminder job |
| `tests/infrastructure/jobs/test_subscription_reminder_job.py` | Create | Reminder job tests |
| `telegram_bot/features/subscriptions/keyboards.py` | Modify | Add renew_now keyboard |
| `telegram_bot/handlers/handler_initializer.py` | Modify | Register jobs |

---

## Estimated Time

- Phase 1: 30 minutes
- Phase 2: 45 minutes
- Phase 3: 45 minutes
- Phase 4: 30 minutes
- Phase 5: 30 minutes

**Total: ~3 hours**
