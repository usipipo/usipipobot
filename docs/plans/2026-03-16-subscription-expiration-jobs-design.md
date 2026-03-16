# Subscription Expiration Jobs - Design Document

**Created:** 2026-03-16
**Status:** Approved
**Priority:** High
**Estimated Effort:** 4-6 hours

---

## Overview

Implement automated background jobs to manage subscription lifecycle: expiration handling and renewal reminders.

---

## Architecture

### Job Structure

Two independent jobs running in parallel via APScheduler:

```
infrastructure/jobs/
├── subscription_expiration_job.py    # Expira suscripciones vencidas
└── subscription_reminder_job.py      # Envía notificaciones de expiración
```

### Schedule Configuration

| Job | Schedule | Time | Purpose |
|-----|----------|------|---------|
| `subscription_expiration_job` | Daily | 02:00 AM UTC | Deactivate expired subscriptions |
| `subscription_reminder_job` | Daily | 09:00 AM UTC | Send renewal reminders |

---

## Job 1: Subscription Expiration

### Purpose
Automatically deactivate subscriptions that have passed their expiration date.

### Implementation

```python
# infrastructure/jobs/subscription_expiration_job.py

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
                    await notification_service.send_subscription_expired(
                        user_id=plan.user_id,
                        plan_name=plan.plan_type.value,
                        expired_date=plan.expires_at
                    )

                deactivated_count += 1
                logger.info(f"✅ Suscripción expirada desactivada: user={plan.user_id}")

            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Error desactivando suscripción {plan.id}: {e}")

        # Report to admin
        if deactivated_count > 0 or failed_count > 0:
            await notify_admin_summary(
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
```

### Notification Message

```python
# telegram_bot/features/subscriptions/messages.py

class SubscriptionExpiredMessage:
    _HEADER = (
        f"{_SEP_HEADER}\n"
        "⚠️ *SUSCRIPCIÓN EXPIRADA*\n"
        f"{_SEP_HEADER}\n"
    )

    _BODY = (
        "\n"
        "Tu suscripción Premium ha expirado.\n"
        "\n"
        "*Plan:* {plan_name}\n"
        "*Fecha de expiración:* {expired_date}\n"
        f"{_SEP_DIVIDER}\n"
        "🔓 *Estado actual:* Datos limitados (10 GB)\n"
        "\n"
        "¿Quieres renovar para recuperar datos ilimitados?\n"
    )

    _FOOTER = (
        f"\n{_SEP_DIVIDER}\n"
        "👇 *Toca para renovar:*\n"
    )
```

---

## Job 2: Subscription Reminder

### Purpose
Send proactive renewal reminders to users with subscriptions expiring soon.

### Implementation

```python
# infrastructure/jobs/subscription_reminder_job.py

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
            await send_urgent_reminder(plan, subscription_service)
            sent_count += 1

        # Send standard reminders (7 days)
        for plan in reminder_only:
            await send_standard_reminder(plan, subscription_service)
            sent_count += 1

        logger.info(f"✅ Job completado: {sent_count} recordatorios enviados")

    except Exception as e:
        logger.error(f"❌ Error en job de recordatorios: {e}")


async def send_urgent_reminder(plan, subscription_service):
    """Send urgent reminder (3 days)."""
    from telegram_bot.features.subscriptions.messages import SubscriptionReminderMessages

    plan_option = subscription_service.get_plan_option(plan.plan_type.value)
    plan_name = plan_option.name if plan_option else plan.plan_type.value

    message = SubscriptionReminderMessages.URGENT.format(
        plan_name=plan_name,
        days_remaining=plan.days_remaining,
        expires_at=plan.expires_at.strftime("%d/%m/%Y")
    )

    # Send via Telegram Bot
    await send_telegram_message(
        user_id=plan.user_id,
        text=message,
        reply_markup=SubscriptionKeyboards.renew_now(plan.plan_type.value),
        parse_mode="Markdown"
    )

    logger.info(f"🔔 Urgent reminder sent to user {plan.user_id}")


async def send_standard_reminder(plan, subscription_service):
    """Send standard reminder (7 days)."""
    from telegram_bot.features.subscriptions.messages import SubscriptionReminderMessages

    plan_option = subscription_service.get_plan_option(plan.plan_type.value)
    plan_name = plan_option.name if plan_option else plan.plan_type.value

    message = SubscriptionReminderMessages.STANDARD.format(
        plan_name=plan_name,
        days_remaining=plan.days_remaining,
        expires_at=plan.expires_at.strftime("%d/%m/%Y")
    )

    # Send via Telegram Bot
    await send_telegram_message(
        user_id=plan.user_id,
        text=message,
        reply_markup=SubscriptionKeyboards.renew_now(plan.plan_type.value),
        parse_mode="Markdown"
    )

    logger.info(f"📅 Standard reminder sent to user {plan.user_id}")
```

### Notification Messages

```python
# telegram_bot/features/subscriptions/messages.py

class SubscriptionReminderMessages:
    """Mensajes de recordatorio de renovación."""

    URGENT = (
        f"{_SEP_HEADER}\n"
        "🚨 *ÚLTIMOS DÍAS*\n"
        f"{_SEP_HEADER}\n"
        "\n"
        "Tu suscripción {plan_name} vence en *{days_remaining} días*\n"
        "\n"
        "*Fecha de vencimiento:* {expires_at}\n"
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

    STANDARD = (
        f"{_SEP_HEADER}\n"
        "📅 *RECORDATORIO DE RENOVACIÓN*\n"
        f"{_SEP_HEADER}\n"
        "\n"
        "Tu suscripción {plan_name} vence en *{days_remaining} días*\n"
        "\n"
        "*Fecha de vencimiento:* {expires_at}\n"
        f"{_SEP_DIVIDER}\n"
        "💡 *Consejo:* Renueva con anticipación para evitar interrupciones\n"
        f"\n{_SEP_DIVIDER}\n"
        "👇 *Ver planes de renovación:*\n"
    )
```

---

## Integration

### Job Registration

```python
# telegram_bot/handlers/handler_initializer.py

async def post_init(application: Application) -> None:
    """Register background jobs after bot initialization."""

    # ... existing jobs ...

    # Subscription expiration job (daily at 02:00 AM)
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

    # Subscription reminder job (daily at 09:00 AM)
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

---

## Error Handling

### Retry Strategy
- Jobs are idempotent (safe to run multiple times)
- Failed deactivations are logged and reported to admin
- Individual failures don't stop the entire job

### Admin Notification

```python
async def notify_admin_summary(context, deactivated: int, failed: int):
    """Send daily summary to admin."""
    from config import settings

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

---

## Testing

### Unit Tests

```python
# tests/infrastructure/jobs/test_subscription_expiration_job.py

class TestSubscriptionExpirationJob:
    @pytest.mark.asyncio
    async def test_expire_active_subscriptions(
        self, mock_subscription_service, mock_notification_service
    ):
        """Test that job deactivates expired subscriptions."""
        # Arrange
        mock_subscription_service.get_expired_subscriptions.return_value = [
            SubscriptionPlan(
                user_id=123,
                plan_type=PlanType.ONE_MONTH,
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                is_active=True
            )
        ]

        # Act
        await subscription_expiration_job(MockContext(
            data={
                "subscription_service": mock_subscription_service,
                "notification_service": mock_notification_service
            }
        ))

        # Assert
        mock_subscription_service.cancel_subscription.assert_called_once()
        mock_notification_service.send_subscription_expired.assert_called_once()

    @pytest.mark.asyncio
    async def test_expire_no_subscriptions(self, mock_subscription_service):
        """Test job handles empty list gracefully."""
        mock_subscription_service.get_expired_subscriptions.return_value = []

        await subscription_expiration_job(MockContext(
            data={"subscription_service": mock_subscription_service}
        ))

        mock_subscription_service.cancel_subscription.assert_not_called()
```

---

## Success Criteria

- [ ] Jobs run daily without manual intervention
- [ ] Expired subscriptions are deactivated within 24 hours
- [ ] Users receive expiration notifications
- [ ] Users receive 3-day and 7-day renewal reminders
- [ ] Admin receives daily summary report
- [ ] Failed operations are logged and reported
- [ ] Tests cover all scenarios

---

## Rollback Plan

If jobs cause issues:

1. **Disable jobs:** Comment out job registration in `handler_initializer.py`
2. **Manual cleanup:** Run SQL query to deactivate expired subscriptions
3. **Fix and redeploy:** Address issues, test locally, redeploy

```sql
-- Manual deactivation query
UPDATE subscription_plans
SET is_active = FALSE
WHERE expires_at < NOW() AND is_active = TRUE;
```

---

## Future Enhancements

1. **Configurable schedules** via environment variables
2. **Multiple reminder intervals** (14, 7, 3, 1 days)
3. **Email notifications** in addition to Telegram
4. **Auto-renewal** option for users
5. **Grace period** (e.g., 24 hours after expiration before deactivation)
