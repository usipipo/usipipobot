# Admin Subscription Panel Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Add subscription management capabilities to admin panel with dashboard, list view, and management actions.

**Architecture:** Extend existing admin handler structure with subscription-specific mixins for list, detail, and actions. Use SubscriptionService for all operations.

**Tech Stack:** Python 3.13+, python-telegram-bot v21.10, SQLAlchemy async, SubscriptionService, existing admin panel infrastructure.

---

## Phase 1: Admin Statistics Service

### Task 1.1: Create Subscription Stats Service

**Files:**
- Create: `telegram_bot/features/subscriptions/admin_stats.py`
- Test: `tests/telegram_bot/features/subscriptions/test_admin_stats.py`

**Step 1: Write the failing test**

```python
# tests/telegram_bot/features/subscriptions/test_admin_stats.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
import uuid

from telegram_bot.features.subscriptions.admin_stats import (
    SubscriptionStats,
    SubscriptionStatsService
)
from domain.entities.subscription_plan import SubscriptionPlan, PlanType


class TestSubscriptionStatsService:
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, mock_subscription_repo):
        """Test dashboard statistics calculation."""
        # Arrange
        active_sub = SubscriptionPlan(
            id=uuid.uuid4(),
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="test_pay",
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=25),
            is_active=True
        )

        mock_subscription_repo.get_all_subscriptions = AsyncMock(
            return_value=[active_sub]
        )
        mock_subscription_repo.get_expiring_plans = AsyncMock(
            return_value=[active_sub]
        )

        service = SubscriptionStatsService(mock_subscription_repo)

        # Act
        stats = await service.get_dashboard_stats(current_user_id=999)

        # Assert
        assert stats.total_active == 1
        assert stats.mrr_stars > 0
        assert stats.expiring_7_days == 1
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/telegram_bot/features/subscriptions/test_admin_stats.py -v
```
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# telegram_bot/features/subscriptions/admin_stats.py
"""Servicio de estadísticas para administración de suscripciones."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict

from domain.interfaces.isubscription_repository import ISubscriptionRepository


@dataclass
class SubscriptionStats:
    """Subscription statistics for admin dashboard."""

    total_active: int
    total_revenue_stars: int
    mrr_stars: int
    by_plan: Dict[str, int]
    expiring_7_days: int
    expired_today: int


class SubscriptionStatsService:
    """Service for calculating subscription statistics."""

    def __init__(self, subscription_repo: ISubscriptionRepository):
        self.subscription_repo = subscription_repo

    async def get_dashboard_stats(
        self,
        current_user_id: int
    ) -> SubscriptionStats:
        """Get comprehensive subscription statistics."""

        # Get all subscriptions
        all_subs = await self.subscription_repo.get_all_subscriptions(current_user_id)

        # Filter active
        now = datetime.now(timezone.utc)
        active_subs = [
            s for s in all_subs
            if s.is_active and s.expires_at > now
        ]

        # Calculate metrics
        total_active = len(active_subs)
        total_revenue_stars = sum(s.stars_paid for s in active_subs)

        # MRR calculation (simplified - monthly recurring revenue)
        mrr_stars = sum(
            s.stars_paid / s.duration_days * 30
            for s in active_subs
        )

        # By plan
        by_plan: Dict[str, int] = {}
        for sub in active_subs:
            plan_type = sub.plan_type.value
            by_plan[plan_type] = by_plan.get(plan_type, 0) + 1

        # Expiring soon (7 days)
        expiring_soon = await self.subscription_repo.get_expiring_plans(
            days=7,
            current_user_id=current_user_id
        )

        # Expired today
        expired_today = sum(
            1 for s in all_subs
            if s.is_active and s.expires_at.date() == now.date()
        )

        return SubscriptionStats(
            total_active=total_active,
            total_revenue_stars=total_revenue_stars,
            mrr_stars=int(mrr_stars),
            by_plan=by_plan,
            expiring_7_days=len(expiring_soon),
            expired_today=expired_today
        )
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/telegram_bot/features/subscriptions/test_admin_stats.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add telegram_bot/features/subscriptions/admin_stats.py tests/telegram_bot/features/subscriptions/test_admin_stats.py
git commit -m "feat(admin): add SubscriptionStatsService for dashboard metrics calculation"
```

---

## Phase 2: Admin Messages & Keyboards

### Task 2.1: Create Admin Subscription Messages

**Files:**
- Create: `telegram_bot/features/admin/messages_subscriptions.py`
- Test: `tests/telegram_bot/features/admin/test_messages_subscriptions.py`

**Step 1: Write the test**

```python
# tests/telegram_bot/features/admin/test_messages_subscriptions.py

import pytest
import uuid
from datetime import datetime, timezone, timedelta

from telegram_bot.features.admin.messages_subscriptions import (
    AdminSubscriptionMessages
)
from domain.entities.subscription_plan import SubscriptionPlan, PlanType


class TestAdminSubscriptionMessages:
    def test_dashboard_message_format(self, sample_stats):
        """Test dashboard message formatting."""
        message = AdminSubscriptionMessages.Dashboard.dashboard(sample_stats)

        assert "📊" in message
        assert "ESTADÍSTICAS" in message
        assert str(sample_stats.total_active) in message
        assert str(sample_stats.mrr_stars) in message

    def test_subscription_detail_format(self, sample_subscription):
        """Test subscription detail message."""
        message = AdminSubscriptionMessages.subscription_detail(sample_subscription)

        assert "👤" in message
        assert str(sample_subscription.user_id) in message
        assert sample_subscription.plan_type.value in message
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/telegram_bot/features/admin/test_messages_subscriptions.py -v
```
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# telegram_bot/features/admin/messages_subscriptions.py
"""Mensajes para administración de suscripciones."""

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


class AdminSubscriptionMessages:
    """Mensajes para administración de suscripciones."""

    class Dashboard:
        """Dashboard messages."""

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
        def dashboard(cls, stats) -> str:
            """Generate dashboard message."""
            message = cls._HEADER
            message += cls._METRICS.format(
                total_active=stats.total_active,
                mrr_stars=stats.mrr_stars,
                expiring_7_days=stats.expiring_7_days,
                expired_today=stats.expired_today
            )

            # Format plan bars
            total = sum(stats.by_plan.values()) if stats.by_plan else 0
            bars = []
            for plan_type, count in sorted(stats.by_plan.items()):
                percent = (count / total * 100) if total > 0 else 0
                bar_length = int(percent / 5)
                bar = "█" * bar_length
                bars.append(f"├─ {plan_type}: {bar} {count} ({percent:.0f}%)")

            message += cls._BY_PLAN.format(plan_bars="\n".join(bars))
            message += f"\n{_SEP_DIVIDER}\n"

            return message

    @staticmethod
    def subscription_detail(subscription) -> str:
        """Generate subscription detail message."""
        status_emoji = "✅" if subscription.is_active and not subscription.is_expired else "❌"
        status_text = "Activa" if subscription.is_active and not subscription.is_expired else "Expirada"

        return (
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
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/telegram_bot/features/admin/test_messages_subscriptions.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add telegram_bot/features/admin/messages_subscriptions.py tests/telegram_bot/features/admin/test_messages_subscriptions.py
git commit -m "feat(admin): add subscription admin messages for dashboard and detail views"
```

---

### Task 2.2: Create Admin Subscription Keyboards

**Files:**
- Create: `telegram_bot/features/admin/keyboards_subscriptions.py`
- Test: `tests/telegram_bot/features/admin/test_keyboards_subscriptions.py`

**Step 1: Write the test**

```python
# tests/telegram_bot/features/admin/test_keyboards_subscriptions.py

import pytest
from telegram_bot.features.admin.keyboards_subscriptions import (
    AdminSubscriptionKeyboards
)


class TestAdminSubscriptionKeyboards:
    def test_dashboard_keyboard(self):
        """Test dashboard keyboard structure."""
        keyboard = AdminSubscriptionKeyboards.subscription_dashboard()

        assert len(keyboard.inline_keyboard) == 4
        assert "Lista Completa" in keyboard.inline_keyboard[0][0].text
        assert "Volver al Admin" in keyboard.inline_keyboard[-1][0].text

    def test_list_keyboard_with_pagination(self):
        """Test list keyboard with pagination."""
        keyboard = AdminSubscriptionKeyboards.subscriptions_list(
            page=1,
            total_pages=5
        )

        # Should have navigation buttons
        assert any("Anterior" in btn.text for btn in keyboard.inline_keyboard[0])
        assert any("Siguiente" in btn.text for btn in keyboard.inline_keyboard[0])
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/telegram_bot/features/admin/test_keyboards_subscriptions.py -v
```
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# telegram_bot/features/admin/keyboards_subscriptions.py
"""Teclados para administración de suscripciones."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class AdminSubscriptionKeyboards:
    """Teclados para administración de suscripciones."""

    @staticmethod
    def subscription_dashboard() -> InlineKeyboardMarkup:
        """Keyboard for subscription dashboard."""
        keyboard = [
            [InlineKeyboardButton("📋 Lista Completa", callback_data="admin_sub_list")],
            [InlineKeyboardButton("⏰ Vencimientos (7 días)", callback_data="admin_sub_expiring")],
            [InlineKeyboardButton("💰 Ingresos", callback_data="admin_sub_revenue")],
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
            [InlineKeyboardButton("🔍 Ver Usuario", callback_data=f"admin_view_user_{subscription.user_id}")],
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

        keyboard.append([InlineKeyboardButton("💰 Reembolsar", callback_data="admin_sub_refund")])
        keyboard.append([InlineKeyboardButton("🔙 Volver a la Lista", callback_data="admin_sub_list")])

        return InlineKeyboardMarkup(keyboard)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/telegram_bot/features/admin/test_keyboards_subscriptions.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add telegram_bot/features/admin/keyboards_subscriptions.py tests/telegram_bot/features/admin/test_keyboards_subscriptions.py
git commit -m "feat(admin): add subscription admin keyboards for dashboard, list, and detail views"
```

---

## Phase 3: Admin Handlers

### Task 3.1: Create Subscription Admin Handlers

**Files:**
- Create: `telegram_bot/features/admin/handlers_subscriptions.py`
- Test: `tests/telegram_bot/features/admin/test_handlers_subscriptions.py`

**Step 1: Write the failing test**

```python
# tests/telegram_bot/features/admin/test_handlers_subscriptions.py

import pytest
from unittest.mock import AsyncMock, MagicMock

from telegram_bot.features.admin.handlers_subscriptions import (
    AdminSubscriptionHandler,
    VIEWING_SUBSCRIPTIONS
)


class TestAdminSubscriptionHandler:
    @pytest.mark.asyncio
    async def test_show_subscription_dashboard(
        self,
        mock_admin_service,
        mock_stats_service
    ):
        """Test dashboard display."""
        handler = AdminSubscriptionHandler(mock_admin_service)
        handler.stats_service = mock_stats_service

        update = MagicMock()
        update.callback_query.data = "admin_sub_dashboard"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock()

        result = await handler.show_subscription_dashboard(update, context)

        assert result == VIEWING_SUBSCRIPTIONS
        update.callback_query.edit_message_text.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/telegram_bot/features/admin/test_handlers_subscriptions.py -v
```
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# telegram_bot/features/admin/handlers_subscriptions.py
"""Handlers para administración de suscripciones."""

from typing import List, Optional
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from application.services.admin_service import AdminService
from application.services.subscription_service import SubscriptionService
from config import settings
from utils.logger import logger

from .keyboards_subscriptions import AdminSubscriptionKeyboards
from .messages_subscriptions import AdminSubscriptionMessages
from ..subscriptions.admin_stats import SubscriptionStatsService

VIEWING_SUBSCRIPTIONS = "VIEWING_SUBSCRIPTIONS"
VIEWING_SUBSCRIPTION_DETAILS = "VIEWING_SUBSCRIPTION_DETAILS"


class AdminSubscriptionHandler:
    """Handler para administración de suscripciones."""

    def __init__(self, admin_service: AdminService):
        self.admin_service = admin_service
        self.subscription_service = SubscriptionService(
            subscription_repo=admin_service.key_repository,  # Will be fixed in integration
            user_repo=admin_service.user_repository
        )
        logger.info("💎 AdminSubscriptionHandler initialized")

    async def show_subscription_dashboard(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Show subscription dashboard."""
        if not self._is_admin(update.effective_user.id):
            await update.callback_query.answer("⚠️ Acceso denegado", show_alert=True)
            return ConversationHandler.END

        try:
            # Get stats
            stats = await self.subscription_service.get_dashboard_stats(
                current_user_id=settings.ADMIN_ID
            )

            message = AdminSubscriptionMessages.Dashboard.dashboard(stats)
            keyboard = AdminSubscriptionKeyboards.subscription_dashboard()

            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

            return VIEWING_SUBSCRIPTIONS

        except Exception as e:
            logger.error(f"Error showing subscription dashboard: {e}")
            await update.callback_query.answer("❌ Error al cargar estadísticas", show_alert=True)
            return ConversationHandler.END

    def _is_admin(self, user_id: int) -> bool:
        """Verifica si el usuario es administrador."""
        return str(user_id) == str(settings.ADMIN_ID)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/telegram_bot/features/admin/test_handlers_subscriptions.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add telegram_bot/features/admin/handlers_subscriptions.py tests/telegram_bot/features/admin/test_handlers_subscriptions.py
git commit -m "feat(admin): add subscription admin handlers for dashboard view"
```

---

## Phase 4: Integration

### Task 4.1: Register Admin Subscription Handlers

**Files:**
- Modify: `telegram_bot/handlers/handler_initializer.py:220-240`

**Step 1: Add handler registration**

```python
# telegram_bot/handlers/handler_initializer.py

from telegram_bot.features.admin.handlers_subscriptions import (
    AdminSubscriptionHandler,
    VIEWING_SUBSCRIPTIONS,
)


def _get_admin_subscription_handlers(container) -> List[BaseHandler]:
    """Initialize admin subscription handlers."""
    from telegram.ext import CallbackQueryHandler

    admin_service = container.resolve(AdminService)
    handler = AdminSubscriptionHandler(admin_service)

    return [
        CallbackQueryHandler(handler.show_subscription_dashboard, pattern="^admin_sub_dashboard$"),
        CallbackQueryHandler(handler.show_subscriptions_list, pattern="^admin_sub_list$"),
        CallbackQueryHandler(handler.view_subscription_details, pattern="^admin_sub_view_"),
        CallbackQueryHandler(handler.deactivate_subscription, pattern="^admin_sub_deactivate$"),
    ]


def initialize_handlers(...) -> List[BaseHandler]:
    # ... existing handlers ...

    # Admin subscription handlers
    handlers.extend(_get_admin_subscription_handlers(container))
    logger.info("✅ Admin subscription handlers configured")

    return handlers
```

**Step 2: Commit**

```bash
git add telegram_bot/handlers/handler_initializer.py
git commit -m "feat(integration): register admin subscription handlers"
```

---

## Phase 5: Testing & Verification

### Task 5.1: Run Full Test Suite

**Step 1: Run all admin subscription tests**

```bash
uv run pytest tests/telegram_bot/features/admin/test_*subscriptions*.py tests/telegram_bot/features/subscriptions/test_admin_stats.py -v
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
git commit -am "test: add comprehensive tests for admin subscription panel"
```

---

## Success Criteria

- [ ] Admin can view subscription dashboard with metrics
- [ ] Admin can browse all subscriptions with pagination
- [ ] Admin can filter by plan type and status
- [ ] Admin can view detailed subscription information
- [ ] Admin can deactivate/reactivate subscriptions
- [ ] All tests pass (439+)
- [ ] No regressions in existing functionality

---

## Files Summary

| File | Action | Purpose |
|------|--------|---------|
| `telegram_bot/features/subscriptions/admin_stats.py` | Create | Statistics service |
| `tests/telegram_bot/features/subscriptions/test_admin_stats.py` | Create | Stats tests |
| `telegram_bot/features/admin/messages_subscriptions.py` | Create | Admin messages |
| `tests/telegram_bot/features/admin/test_messages_subscriptions.py` | Create | Message tests |
| `telegram_bot/features/admin/keyboards_subscriptions.py` | Create | Admin keyboards |
| `tests/telegram_bot/features/admin/test_keyboards_subscriptions.py` | Create | Keyboard tests |
| `telegram_bot/features/admin/handlers_subscriptions.py` | Create | Admin handlers |
| `tests/telegram_bot/features/admin/test_handlers_subscriptions.py` | Create | Handler tests |
| `telegram_bot/handlers/handler_initializer.py` | Modify | Register handlers |

---

## Estimated Time

- Phase 1: 45 minutes
- Phase 2: 60 minutes
- Phase 3: 60 minutes
- Phase 4: 30 minutes
- Phase 5: 30 minutes

**Total: ~3.5 hours**
