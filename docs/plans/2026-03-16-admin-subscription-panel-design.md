# Admin Panel - Subscription Management Design Document

**Created:** 2026-03-16
**Status:** Approved
**Priority:** Medium
**Estimated Effort:** 6-8 hours

---

## Overview

Add subscription management capabilities to the existing admin panel, enabling monitoring and management of all user subscriptions.

---

## Architecture

### File Structure

```
telegram_bot/features/admin/
├── handlers_subscriptions.py        # Main handler class
├── handlers_subscriptions_list.py   # List and pagination
├── handlers_subscriptions_actions.py # Actions (deactivate, extend)
├── keyboards_subscriptions.py       # Admin keyboards
└── messages_subscriptions.py        # Admin messages

telegram_bot/features/subscriptions/
└── admin_stats.py                   # Statistics service
```

---

## Views

### 1. Subscription Dashboard

**Purpose:** High-level overview of subscription metrics.

**Metrics Displayed:**

| Metric | Description | Source |
|--------|-------------|--------|
| Total Activas | Current active subscriptions | `COUNT WHERE is_active=true AND expires_at > NOW()` |
| MRR (Monthly Recurring Revenue) | Estimated monthly revenue | `SUM(stars_paid) / duration_months` |
| Por Plan | Breakdown by plan type | `GROUP BY plan_type` |
| Vencimientos (7 días) | Subscriptions expiring soon | `WHERE expires_at BETWEEN NOW() AND NOW() + 7 days` |

**Implementation:**

```python
# telegram_bot/features/subscriptions/admin_stats.py

@dataclass
class SubscriptionStats:
    """Subscription statistics for admin dashboard."""

    total_active: int
    total_revenue_stars: int
    mrr_stars: int
    by_plan: Dict[str, int]  # plan_type -> count
    expiring_7_days: int
    expired_today: int


class SubscriptionStatsService:
    """Service for calculating subscription statistics."""

    def __init__(self, subscription_repo: ISubscriptionRepository):
        self.subscription_repo = subscription_repo

    async def get_dashboard_stats(self, current_user_id: int) -> SubscriptionStats:
        """Get comprehensive subscription statistics."""

        # Get all active subscriptions
        all_subs = await self.subscription_repo.get_all_subscriptions(current_user_id)
        active_subs = [s for s in all_subs if s.is_active and not s.is_expired]

        # Calculate metrics
        total_active = len(active_subs)

        # MRR calculation (simplified)
        mrr_stars = sum(
            s.stars_paid / s.duration_days * 30
            for s in active_subs
        )

        # By plan
        by_plan = {}
        for sub in active_subs:
            plan_type = sub.plan_type.value
            by_plan[plan_type] = by_plan.get(plan_type, 0) + 1

        # Expiring soon
        expiring_soon = await self.subscription_repo.get_expiring_plans(
            days=7,
            current_user_id=current_user_id
        )

        # Expired today
        now = datetime.now(timezone.utc)
        expired_today = sum(
            1 for s in all_subs
            if s.is_active and s.expires_at.date() == now.date()
        )

        return SubscriptionStats(
            total_active=total_active,
            total_revenue_stars=sum(s.stars_paid for s in active_subs),
            mrr_stars=int(mrr_stars),
            by_plan=by_plan,
            expiring_7_days=len(expiring_soon),
            expired_today=expired_today
        )
```

**UI Layout:**

```
╔════════════════════════════════════════╗
║  📊 ESTADÍSTICAS DE SUSCRIPCIONES      ║
╠════════════════════════════════════════╣
║                                        ║
║  💎 Total Activas:        47           ║
║  💰 MRR Estimado:         1,234 ⭐     ║
║  📅 Vencimientos (7 días): 8           ║
║  ⚠️  Expiradas Hoy:       2            ║
║                                        ║
║  ─────────────────────────────────     ║
║                                        ║
║  📊 Por Plan:                          ║
║  ┌────────────────────────────────┐   ║
║  │ 1 Mes:    ████████  23 (49%)   │   ║
║  │ 3 Meses:  ██████     15 (32%)   │   ║
║  │ 6 Meses:  ████        9 (19%)   │   ║
║  └────────────────────────────────┘   ║
║                                        ║
╠════════════════════════════════════════╣
║  [📋 Lista Completa] [⏰ Vencimientos] ║
║  [💰 Ingresos]      [🔙 Volver]        ║
╚════════════════════════════════════════╝
```

---

### 2. Subscription List

**Purpose:** View and search all subscriptions.

**Features:**
- Paginated list (20 per page)
- Filters: By plan, by status (active/expired), by date range
- Search by user_id
- Sort by: expiration date, creation date, amount

**Implementation:**

```python
# telegram_bot/features/admin/handlers_subscriptions_list.py

VIEWING_SUBSCRIPTIONS = "VIEWING_SUBSCRIPTIONS"
SUBSCRIPTIONS_PER_PAGE = 20


class SubscriptionsListMixin:
    """Mixin for subscription list functionality."""

    async def show_subscriptions_list(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        page: int = 0,
        plan_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ):
        """Show paginated list of subscriptions."""

        # Get all subscriptions
        all_subs = await self.subscription_service.get_all_subscriptions(
            current_user_id=settings.ADMIN_ID
        )

        # Apply filters
        filtered = self._apply_filters(
            all_subs,
            plan_filter=plan_filter,
            status_filter=status_filter
        )

        # Paginate
        total_pages = (len(filtered) + SUBSCRIPTIONS_PER_PAGE - 1) // SUBSCRIPTIONS_PER_PAGE
        start_idx = page * SUBSCRIPTIONS_PER_PAGE
        end_idx = min(start_idx + SUBSCRIPTIONS_PER_PAGE, len(filtered))
        page_subs = filtered[start_idx:end_idx]

        # Format message
        message = self._format_subscriptions_list(page_subs, page, total_pages)
        keyboard = AdminSubscriptionKeyboards.subscriptions_list(
            page=page,
            total_pages=total_pages,
            has_filters=plan_filter or status_filter
        )

        await self._edit_or_reply(
            update, context,
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        return VIEWING_SUBSCRIPTIONS

    def _apply_filters(
        self,
        subscriptions: List[SubscriptionPlan],
        plan_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[SubscriptionPlan]:
        """Apply filters to subscription list."""

        filtered = subscriptions

        if plan_filter:
            filtered = [s for s in filtered if s.plan_type.value == plan_filter]

        if status_filter == "active":
            filtered = [s for s in filtered if s.is_active and not s.is_expired]
        elif status_filter == "expired":
            filtered = [s for s in filtered if s.is_expired or not s.is_active]

        return filtered

    def _format_subscriptions_list(
        self,
        subscriptions: List[SubscriptionPlan],
        page: int,
        total_pages: int
    ) -> str:
        """Format subscriptions list for display."""

        message = (
            f"{_SEP_HEADER}\n"
            f"📋 *SUSCRIPCIONES*\n"
            f"{_SEP_HEADER}\n"
            f"Página {page + 1}/{total_pages}\n"
            f"{_SEP_DIVIDER}\n"
        )

        for sub in subscriptions:
            status_emoji = "✅" if sub.is_active and not sub.is_expired else "❌"
            days_remaining = sub.days_remaining

            message += (
                f"{status_emoji} *User {sub.user_id}* - {sub.plan_type.value}\n"
                f"   Vence: {sub.expires_at.strftime('%d/%m/%Y')} "
                f"({days_remaining} días)\n"
                f"   Stars: {sub.stars_paid} ⭐\n"
                f"{_SEP_DIVIDER}\n"
            )

        return message
```

---

### 3. Subscription Detail

**Purpose:** View detailed information and perform actions.

**Information Displayed:**

```
╔════════════════════════════════════════╗
║  👤 SUSCRIPCIÓN #abc123                ║
╠════════════════════════════════════════╣
║                                        ║
║  Usuario: 123456789                    ║
║  Plan:    3 Meses Premium              ║
║  Estado:  ✅ Activa                    ║
║                                        ║
║  Inicio:  01/01/2026                   ║
║  Vence:   31/03/2026 (45 días)         ║
║                                        ║
║  Stars:   960 ⭐                        ║
║  Payment: telegram_txn789              ║
║                                        ║
╠════════════════════════════════════════╣
║  [🔍 Ver Usuario] [⏰ Extender]        ║
║  [❌ Desactivar] [💰 Reembolsar]       ║
║  [🔙 Volver a la Lista]                ║
╚════════════════════════════════════════╝
```

**Implementation:**

```python
# telegram_bot/features/admin/handlers_subscriptions_actions.py

VIEWING_SUBSCRIPTION_DETAILS = "VIEWING_SUBSCRIPTION_DETAILS"
CONFIRMING_SUBSCRIPTION_DEACTIVATE = "CONFIRMING_SUBSCRIPTION_DEACTIVATE"
CONFIRMING_SUBSCRIPTION_EXTEND = "CONFIRMING_SUBSCRIPTION_EXTEND"


class SubscriptionsActionsMixin:
    """Mixin for subscription actions."""

    async def view_subscription_details(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show detailed view of a subscription."""

        if context.user_data is None:
            return ConversationHandler.END

        sub_id = context.user_data.get("selected_subscription_id")
        if not sub_id:
            await self._reply_message(update, context, "❌ Suscripción no válida")
            return VIEWING_SUBSCRIPTIONS

        # Get subscription details
        sub = await self.subscription_service.get_subscription_by_id(
            plan_id=UUID(sub_id),
            current_user_id=settings.ADMIN_ID
        )

        if not sub:
            await self._reply_message(update, context, "❌ Suscripción no encontrada")
            return VIEWING_SUBSCRIPTIONS

        # Format message
        message = AdminSubscriptionMessages.subscription_detail(sub)
        keyboard = AdminSubscriptionKeyboards.subscription_detail(sub)

        await self._reply_message(
            update, context,
            text=message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        return VIEWING_SUBSCRIPTION_DETAILS

    async def deactivate_subscription(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Deactivate a subscription (admin action)."""

        if context.user_data is None:
            return ConversationHandler.END

        sub_id = context.user_data.get("selected_subscription_id")

        try:
            await self.subscription_service.cancel_subscription(
                user_id=context.user_data.get("selected_user_id"),
                current_user_id=settings.ADMIN_ID
            )

            await self._reply_message(
                update, context,
                text=f"✅ Suscripción {sub_id} desactivada exitosamente",
                parse_mode="Markdown"
            )

            # Clear selection
            context.user_data.pop("selected_subscription_id", None)
            context.user_data.pop("selected_user_id", None)

            return await self.show_subscriptions_list(update, context)

        except Exception as e:
            logger.error(f"Error desactivando suscripción {sub_id}: {e}")
            await self._reply_message(
                update, context,
                text=f"❌ Error: {e}",
                parse_mode="Markdown"
            )
            return VIEWING_SUBSCRIPTION_DETAILS
```

---

## Keyboards

```python
# telegram_bot/features/admin/keyboards_admin.py (add)

class AdminSubscriptionKeyboards:
    """Teclados para administración de suscripciones."""

    @staticmethod
    def subscription_dashboard() -> InlineKeyboardMarkup:
        """Keyboard for subscription dashboard."""
        keyboard = [
            [
                InlineKeyboardButton("📋 Lista Completa", callback_data="admin_sub_list"),
            ],
            [
                InlineKeyboardButton("⏰ Vencimientos (7 días)", callback_data="admin_sub_expiring"),
            ],
            [
                InlineKeyboardButton("💰 Ingresos", callback_data="admin_sub_revenue"),
            ],
            [InlineKeyboardButton("🔙 Volver al Admin", callback_data="admin_panel")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def subscriptions_list(
        page: int,
        total_pages: int,
        has_filters: bool = False
    ) -> InlineKeyboardMarkup:
        """Keyboard for subscription list with pagination."""
        keyboard = []

        # Pagination
        if page > 0 or page < total_pages - 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(
                    InlineKeyboardButton("◀️ Anterior", callback_data=f"admin_sub_page_{page-1}")
                )
            if page < total_pages - 1:
                nav_buttons.append(
                    InlineKeyboardButton("Siguiente ▶️", callback_data=f"admin_sub_page_{page+1}")
                )
            keyboard.append(nav_buttons)

        # Filters
        if not has_filters:
            keyboard.append([
                InlineKeyboardButton("🔍 Filtrar por Plan", callback_data="admin_sub_filter_plan"),
            ])
            keyboard.append([
                InlineKeyboardButton("🟢 Activas", callback_data="admin_sub_filter_active"),
                InlineKeyboardButton("🔴 Expiradas", callback_data="admin_sub_filter_expired"),
            ])

        # Back
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="admin_sub_dashboard")])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def subscription_detail(subscription) -> InlineKeyboardMarkup:
        """Keyboard for subscription detail view."""
        is_active = subscription.is_active and not subscription.is_expired

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Ver Usuario",
                    callback_data=f"admin_view_user_{subscription.user_id}"
                ),
            ],
        ]

        if is_active:
            keyboard.append([
                InlineKeyboardButton("⏰ Extender", callback_data="admin_sub_extend"),
                InlineKeyboardButton("❌ Desactivar", callback_data="admin_sub_deactivate"),
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("✅ Reactivar", callback_data="admin_sub_reactivate"),
            ])

        keyboard.append([
            InlineKeyboardButton("💰 Reembolsar", callback_data="admin_sub_refund"),
        ])

        keyboard.append([
            InlineKeyboardButton("🔙 Volver a la Lista", callback_data="admin_sub_list"),
        ])

        return InlineKeyboardMarkup(keyboard)
```

---

## Messages

```python
# telegram_bot/features/admin/messages_admin.py (add)

class AdminSubscriptionMessages:
    """Mensajes para administración de suscripciones."""

    class Dashboard:
        _HEADER = (
            f"{_SEP_HEADER}\n"
            "📊 *ESTADÍSTICAS DE SUSCRIPCIONES*\n"
            f"{_SEP_HEADER}\n"
        )

        _METRICS = (
            "\n"
            "💎 *Total Activas:* `{total_active}`\n"
            "💰 *MRR Estimado:* `{mrr_stars} ⭐`\n"
            "📅 *Vencimientos (7 días):* `{expiring_7_days}`\n"
            "⚠️ *Expiradas Hoy:* `{expired_today}`\n"
            f"{_SEP_DIVIDER}\n"
        )

        _BY_PLAN = (
            "\n"
            "*📊 Por Plan:*\n"
            "│\n"
            "{plan_bars}\n"
        )

        @classmethod
        def dashboard(cls, stats: SubscriptionStats) -> str:
            """Generate dashboard message."""
            message = cls._HEADER
            message += cls._METRICS.format(
                total_active=stats.total_active,
                mrr_stars=stats.mrr_stars,
                expiring_7_days=stats.expiring_7_days,
                expired_today=stats.expired_today
            )

            # Format plan bars
            total = sum(stats.by_plan.values())
            bars = []
            for plan_type, count in sorted(stats.by_plan.items()):
                percent = (count / total * 100) if total > 0 else 0
                bar_length = int(percent / 5)  # Scale to 20 chars max
                bar = "█" * bar_length
                bars.append(f"├─ {plan_type}: {bar} {count} ({percent:.0f}%)")

            message += cls._BY_PLAN.format(plan_bars="\n".join(bars))
            message += f"\n{_SEP_DIVIDER}\n"

            return message

    @staticmethod
    def subscription_detail(subscription: SubscriptionPlan) -> str:
        """Generate subscription detail message."""
        status_emoji = "✅" if subscription.is_active and not subscription.is_expired else "❌"
        status_text = "Activa" if subscription.is_active and not subscription.is_expired else "Expirada"

        message = (
            f"{_SEP_HEADER}\n"
            f"👤 *SUSCRIPCIÓN #{str(subscription.id)[:8]}*\n"
            f"{_SEP_HEADER}\n"
            "\n"
            f"*Usuario:* `{subscription.user_id}`\n"
            f"*Plan:* {subscription.plan_type.value}\n"
            f"*Estado:* {status_emoji} {status_text}\n"
            f"{_SEP_DIVIDER}\n"
            "\n"
            f"*Inicio:* {subscription.starts_at.strftime('%d/%m/%Y')}\n"
            f"*Vence:* {subscription.expires_at.strftime('%d/%m/%Y')} "
            f"({subscription.days_remaining} días)\n"
            f"{_SEP_DIVIDER}\n"
            "\n"
            f"*Stars:* {subscription.stars_paid} ⭐\n"
            f"*Payment ID:* `{subscription.payment_id}`\n"
            f"{_SEP_DIVIDER}\n"
        )

        return message
```

---

## Integration

### Handler Registration

```python
# telegram_bot/handlers/handler_initializer.py

from telegram_bot.features.admin.handlers_subscriptions import (
    AdminSubscriptionHandler,
    VIEWING_SUBSCRIPTIONS,
    VIEWING_SUBSCRIPTION_DETAILS,
)


def _get_admin_subscription_handlers(container) -> List[BaseHandler]:
    """Initialize admin subscription handlers."""
    admin_service = container.resolve(AdminService)
    handler = AdminSubscriptionHandler(admin_service)

    return [
        # Main menu
        CallbackQueryHandler(handler.show_subscription_dashboard, pattern="^admin_sub_dashboard$"),

        # List
        CallbackQueryHandler(handler.show_subscriptions_list, pattern="^admin_sub_list$"),
        CallbackQueryHandler(handler.show_subscriptions_list, pattern="^admin_sub_page_"),

        # Filters
        CallbackQueryHandler(handler.filter_by_plan, pattern="^admin_sub_filter_plan$"),
        CallbackQueryHandler(handler.filter_by_status, pattern="^admin_sub_filter_"),

        # Detail
        CallbackQueryHandler(handler.view_subscription_details, pattern="^admin_sub_view_"),

        # Actions
        CallbackQueryHandler(handler.deactivate_subscription, pattern="^admin_sub_deactivate$"),
        CallbackQueryHandler(handler.extend_subscription, pattern="^admin_sub_extend$"),
        CallbackQueryHandler(handler.refund_subscription, pattern="^admin_sub_refund$"),

        # View user
        CallbackQueryHandler(handler.view_user_from_subscription, pattern="^admin_view_user_"),
    ]


def initialize_handlers(...) -> List[BaseHandler]:
    # ... existing handlers ...

    # Admin subscription handlers
    handlers.extend(_get_admin_subscription_handlers(container))
    logger.info("✅ Admin subscription handlers configured")

    return handlers
```

---

## Testing

### Unit Tests

```python
# tests/telegram_bot/features/admin/test_handlers_subscriptions.py

class TestAdminSubscriptionHandlers:
    @pytest.mark.asyncio
    async def test_show_subscription_dashboard(self, mock_admin_service):
        """Test dashboard display."""
        handler = AdminSubscriptionHandler(mock_admin_service)

        update = MockUpdate(callback_data="admin_sub_dashboard")
        context = MockContext()

        result = await handler.show_subscription_dashboard(update, context)

        assert result == VIEWING_SUBSCRIPTIONS
        assert context.bot.edit_message_text.called

    @pytest.mark.asyncio
    async def test_deactivate_subscription(self, mock_admin_service):
        """Test subscription deactivation."""
        handler = AdminSubscriptionHandler(mock_admin_service)

        update = MockUpdate(callback_data="admin_sub_deactivate")
        context = MockContext(user_data={
            "selected_subscription_id": "abc123",
            "selected_user_id": 123
        })

        result = await handler.deactivate_subscription(update, context)

        mock_admin_service.cancel_subscription.assert_called_once()
        assert result == VIEWING_SUBSCRIPTIONS
```

---

## Success Criteria

- [ ] Admin can view subscription dashboard with metrics
- [ ] Admin can browse all subscriptions with pagination
- [ ] Admin can filter by plan type and status
- [ ] Admin can view detailed subscription information
- [ ] Admin can deactivate/reactivate subscriptions
- [ ] Admin can extend subscription expiration
- [ ] All actions are logged for audit trail
- [ ] Tests cover all admin operations

---

## Security Considerations

### Access Control

- All subscription endpoints verify `user_id == ADMIN_ID`
- Actions are logged with admin user ID
- Sensitive operations (deactivate, refund) require confirmation

### Audit Trail

```python
# Log all admin actions
logger.info(
    f"AUDIT: Admin {admin_id} deactivated subscription {sub_id} for user {user_id}"
)
```

---

## Future Enhancements

1. **Bulk actions:** Deactivate/extend multiple subscriptions at once
2. **Export:** CSV export of subscription data
3. **Charts:** Visual charts for revenue trends
4. **Notifications:** Alert admin of unusual activity
5. **Refund automation:** Integrate with Telegram Stars refund API
