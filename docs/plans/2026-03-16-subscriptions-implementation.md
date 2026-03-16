# Subscription Plans - Telegram Bot & Mini App Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Implement complete subscription plans system (1, 3, 6 months) with unlimited data, integrating Telegram Bot handlers, Mini App page, and payment flows (Stars + Crypto) following the same pattern as package/slots purchases.

**Architecture:** Clean Architecture / Hexagonal pattern. Domain entities → Repository interfaces → Infrastructure implementations → Application services → Background jobs → Bot handlers + Mini App routes. Coexists with existing GB package system.

**Tech Stack:** Python 3.13+, SQLAlchemy 2.0 async, PostgreSQL, python-telegram-bot, Punq DI, Alembic migrations, FastAPI, Jinja2 templates.

---

## Critical Integration Points (DO NOT BREAK)

1. **VPN Key Creation** - `VpnService.create_key()` must check subscription status for data limits
2. **Consumption Billing** - `ConsumptionBillingService` must bypass GB tracking for premium users
3. **Data Package Coexistence** - Users can have BOTH active subscription + GB packages
4. **Payment Infrastructure** - Reuse existing Telegram Stars + Crypto payment flows
5. **Background Jobs** - Add subscription expiration + reminder jobs alongside existing package expiration

---

## Code Review Fixes Applied (from previous implementation)

| # | Issue | Fix Applied |
|---|-------|-------------|
| 1 | `is_premium_user` always returns `False` | Changed to `async` with proper repo call |
| 2 | `_get_user_data_limit` always returns `-1` | Made `async` with actual subscription check |
| 3 | `.copy()` on dataclass | Replaced with `dataclasses.replace()` |
| 4 | Test for `is_premium_user` sync | Updated to `@pytest.mark.asyncio` |
| 5 | Duplicate CheckConstraint in model | Removed `info={}` from column definition |
| 6 | `payment_id` not persisted | Added to entity, model, and used for idempotency |
| 7 | `down_revision = None` in migration | Will use actual latest revision |
| 8 | `scalar_one_or_none` may throw | Changed to `scalars().first()` |
| 9 | `stars_paid` accumulation semantics | Keep as total paid for audit trail |
| 10 | Markdown `**` invalid in v1 | Changed to `*` for bold |
| 11 | DI container double instantiation | Use `container.resolve()` consistently |

---

## Phase 1: Domain Layer (Entities + Interfaces)

### Task 1.1: Verify SubscriptionPlan Entity Exists

**Files:**
- Check: `domain/entities/subscription_plan.py`
- Check: `tests/domain/entities/test_subscription_plan.py`

**Step 1: Verify entity exists**

Run:
```bash
ls -la domain/entities/subscription_plan.py
```

Expected: File exists

**Step 2: If file doesn't exist, create it**

If file missing, create:

```python
# domain/entities/subscription_plan.py
"""Subscription plan domain entity."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional


class PlanType(str, Enum):
    """Subscription plan types."""

    ONE_MONTH = "one_month"
    THREE_MONTHS = "three_months"
    SIX_MONTHS = "six_months"


@dataclass
class SubscriptionPlan:
    """Represents an active subscription plan for a user.

    Attributes:
        user_id: Telegram ID of the user
        plan_type: Type of plan (1, 3, or 6 months)
        stars_paid: Total stars paid for this plan
        payment_id: Payment reference for idempotency
        starts_at: Plan activation datetime
        expires_at: Plan expiration datetime
        id: Unique plan identifier
        is_active: Whether plan is currently active
        created_at: Record creation datetime
        updated_at: Record last update datetime
    """

    user_id: int
    plan_type: PlanType
    stars_paid: int
    payment_id: str  # For idempotency - prevents duplicate plans from same payment
    starts_at: datetime
    expires_at: datetime
    id: Optional[uuid.UUID] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid.uuid4()
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

    @property
    def duration_days(self) -> int:
        """Returns plan duration in days."""
        duration_map = {
            PlanType.ONE_MONTH: 30,
            PlanType.THREE_MONTHS: 90,
            PlanType.SIX_MONTHS: 180,
        }
        return duration_map.get(self.plan_type, 0)

    @property
    def days_remaining(self) -> int:
        """Returns days remaining until expiration."""
        now = datetime.now(timezone.utc)
        delta = self.expires_at - now
        return max(0, delta.days)

    @property
    def is_expiring_soon(self) -> bool:
        """True if plan expires in less than 3 days."""
        return self.days_remaining <= 3

    @property
    def is_expired(self) -> bool:
        """True if plan has expired."""
        now = datetime.now(timezone.utc)
        return now > self.expires_at

    def deactivate(self) -> None:
        """Deactivate this subscription plan."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
```

**Step 3: Run tests to verify**

Run:
```bash
uv run pytest tests/domain/entities/test_subscription_plan.py -v
```

Expected: PASS (5+ tests)

**Step 4: Commit**

```bash
git add domain/entities/subscription_plan.py
git commit -m "feat(domain): add SubscriptionPlan entity with PlanType enum and payment_id for idempotency"
```

---

### Task 1.2: Verify ISubscriptionRepository Interface

**Files:**
- Check: `domain/interfaces/isubscription_repository.py`
- Modify: `domain/interfaces/__init__.py`

**Step 1: Verify interface exists**

Run:
```bash
ls -la domain/interfaces/isubscription_repository.py
```

Expected: File exists

**Step 2: If file doesn't exist, create it**

```python
# domain/interfaces/isubscription_repository.py
"""Repository interface for subscription operations."""

import uuid
from typing import List, Optional, Protocol
from domain.entities.subscription_plan import SubscriptionPlan


class ISubscriptionRepository(Protocol):
    """Repository interface for subscription operations."""

    async def save(self, plan: SubscriptionPlan, current_user_id: int) -> SubscriptionPlan:
        """Save or update a subscription plan."""
        ...

    async def get_by_id(self, plan_id: uuid.UUID, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get subscription by ID."""
        ...

    async def get_by_payment_id(self, payment_id: str, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get subscription by payment ID (for idempotency)."""
        ...

    async def get_active_by_user(self, user_id: int, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get active subscription for a user."""
        ...

    async def get_expiring_plans(self, days: int, current_user_id: int) -> List[SubscriptionPlan]:
        """Get plans expiring within N days."""
        ...

    async def get_expired_plans(self, current_user_id: int) -> List[SubscriptionPlan]:
        """Get all expired plans."""
        ...

    async def deactivate(self, plan_id: uuid.UUID, current_user_id: int) -> bool:
        """Deactivate a subscription plan."""
        ...
```

**Step 3: Update interfaces __init__.py**

```python
# domain/interfaces/__init__.py
# Add to exports
from .isubscription_repository import ISubscriptionRepository

__all__ = [
    # ... existing exports ...
    "ISubscriptionRepository",
]
```

**Step 4: Commit**

```bash
git add domain/interfaces/isubscription_repository.py domain/interfaces/__init__.py
git commit -m "feat(domain): add ISubscriptionRepository interface with payment_id idempotency"
```

---

## Phase 2: Infrastructure Layer (Database + Repository)

### Task 2.1: Verify SubscriptionPlanModel Exists

**Files:**
- Check: `infrastructure/persistence/postgresql/models/subscription_plan.py`
- Check: `infrastructure/persistence/postgresql/models/__init__.py`

**Step 1: Verify model exists**

Run:
```bash
ls -la infrastructure/persistence/postgresql/models/subscription_plan.py
```

Expected: File exists

**Step 2: If missing, create the SQLAlchemy model**

```python
# infrastructure/persistence/postgresql/models/subscription_plan.py
"""SQLAlchemy model for subscription plans."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class SubscriptionPlanModel(Base):
    """SQLAlchemy model for subscription plans."""

    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[int] = mapped_column(nullable=False)
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    stars_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # For idempotency
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(
        back_populates="subscription_plans",
        foreign_keys=[user_id],
        primaryjoin="SubscriptionPlanModel.user_id == UserModel.telegram_id"
    )

    __table_args__ = (
        CheckConstraint(
            "plan_type IN ('one_month', 'three_months', 'six_months')",
            name="ck_subscription_plans_plan_type"
        ),
    )
```

**Step 3: Update models __init__.py**

```python
# infrastructure/persistence/postgresql/models/__init__.py
from .subscription_plan import SubscriptionPlanModel  # ADD THIS

__all__ = [
    # ... existing exports ...
    "SubscriptionPlanModel",
]
```

**Step 4: Add relationship to UserModel**

In `infrastructure/persistence/postgresql/models/base.py`, add to UserModel:

```python
subscription_plans: Mapped[List["SubscriptionPlanModel"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
    foreign_keys="SubscriptionPlanModel.user_id"
)
```

**Step 5: Commit**

```bash
git add infrastructure/persistence/postgresql/models/subscription_plan.py
git add infrastructure/persistence/postgresql/models/__init__.py
git add infrastructure/persistence/postgresql/models/base.py
git commit -m "feat(infra): add SubscriptionPlanModel with payment_id unique constraint for idempotency"
```

---

### Task 2.2: Verify Alembic Migration

**Files:**
- Check: `migrations/versions/20260316_add_subscription_plans.py`

**Step 1: Get current migration head**

Run:
```bash
uv run alembic heads
```

Expected: Output like `abc123 (head)` - note this revision

**Step 2: Verify migration exists**

Run:
```bash
ls -la migrations/versions/20260316_add_subscription_plans.py
```

Expected: File exists

**Step 3: If missing, create the migration**

```python
"""Add subscription plans tables

Revision ID: add_subscriptions_001
Revises: abc123  # ← REPLACE with actual head from 'alembic heads'
Create Date: 2026-03-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_subscriptions_001'
down_revision = 'abc123'  # ← REPLACE with actual head
branch_labels = None
depends_on = None


def upgrade():
    # Create subscription_plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_type', sa.String(length=20), nullable=False),
        sa.Column('stars_paid', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.String(length=255), nullable=False),
        sa.Column('starts_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('payment_id', name='uq_subscription_plans_payment_id'),
        sa.CheckConstraint("plan_type IN ('one_month', 'three_months', 'six_months')", name='ck_subscription_plans_plan_type')
    )

    # Create indexes
    op.create_index('idx_subscription_plans_user_id', 'subscription_plans', ['user_id'])
    op.create_index('idx_subscription_plans_is_active', 'subscription_plans', ['is_active'])
    op.create_index('idx_subscription_plans_expires_at', 'subscription_plans', ['expires_at'])
    op.create_index(
        'idx_subscription_plans_active_user',
        'subscription_plans',
        ['user_id', 'is_active'],
        postgresql_where=sa.text('is_active = TRUE')
    )

    # Add is_premium flag to vpn_keys
    op.add_column('vpn_keys', sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('idx_vpn_keys_is_premium', 'vpn_keys', ['is_premium'])


def downgrade():
    op.drop_index('idx_vpn_keys_is_premium', table_name='vpn_keys')
    op.drop_column('vpn_keys', 'is_premium')
    op.drop_index('idx_subscription_plans_active_user', table_name='subscription_plans')
    op.drop_index('idx_subscription_plans_expires_at', table_name='subscription_plans')
    op.drop_index('idx_subscription_plans_is_active', table_name='subscription_plans')
    op.drop_index('idx_subscription_plans_user_id', table_name='subscription_plans')
    op.drop_table('subscription_plans')
```

**Step 4: Run migration to verify**

Run:
```bash
uv run alembic upgrade head
```

Expected: Migration runs successfully

**Step 5: Verify tables exist**

Run:
```bash
uv run python -c "
from infrastructure.persistence.database import get_session_factory
import asyncio

async def check():
    session_factory = get_session_factory()
    async with session_factory() as session:
        from sqlalchemy import text
        result = await session.execute(text('''
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'subscription_plans'
        '''))
        rows = result.fetchall()
        print('subscription_plans table exists:', len(rows) > 0)

asyncio.run(check())
"
```

Expected: `subscription_plans table exists: True`

**Step 6: Commit**

```bash
git add migrations/versions/20260316_add_subscription_plans.py
git commit -m "feat(migrations): add subscription_plans table with payment_id unique constraint"
```

---

### Task 2.3: Verify PostgresSubscriptionRepository

**Files:**
- Check: `infrastructure/persistence/postgresql/subscription_repository.py`
- Check: `tests/infrastructure/persistence/test_subscription_repository.py`

**Step 1: Verify repository exists**

Run:
```bash
ls -la infrastructure/persistence/postgresql/subscription_repository.py
```

Expected: File exists

**Step 2: If missing, see existing implementation in docs**

The full implementation is in `/home/mowgli/usipipobot/docs/plans/2026-03-16-subscription-plans-implementation.md` (Task 2.3).

**Step 3: Run repository tests**

Run:
```bash
uv run pytest tests/infrastructure/persistence/test_subscription_repository.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add infrastructure/persistence/postgresql/subscription_repository.py
git commit -m "feat(infra): add PostgresSubscriptionRepository with full CRUD operations"
```

---

## Phase 3: Application Services

### Task 3.1: Verify SubscriptionService Exists

**Files:**
- Check: `application/services/subscription_service.py`
- Check: `tests/application/services/test_subscription_service.py`

**Step 1: Verify service exists**

Run:
```bash
ls -la application/services/subscription_service.py
```

Expected: File exists

**Step 2: Review existing implementation**

The service should have methods:
- `activate_subscription()`
- `get_active_plan()`
- `is_premium_user()`
- `get_plan_option()`
- `expire_plans()`

**Step 3: Run service tests**

Run:
```bash
uv run pytest tests/application/services/test_subscription_service.py -v
```

Expected: PASS

**Step 4: Commit if any fixes applied**

```bash
git add application/services/subscription_service.py
git commit -m "fix(application): fix SubscriptionService async methods and idempotency"
```

---

### Task 3.2: Create SubscriptionPaymentService (NEW)

**Files:**
- Create: `application/services/subscription_payment_service.py`
- Create: `tests/application/services/test_subscription_payment_service.py`

**Step 1: Write the failing test**

```python
# tests/application/services/test_subscription_payment_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from application.services.subscription_payment_service import SubscriptionPaymentService


class TestSubscriptionPaymentService:
    @pytest.fixture
    def mock_subscription_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_notification_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_crypto_payment_service(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_subscription_service, mock_notification_service, mock_crypto_payment_service):
        return SubscriptionPaymentService(
            subscription_service=mock_subscription_service,
            notification_service=mock_notification_service,
            crypto_payment_service=mock_crypto_payment_service,
        )

    @pytest.mark.asyncio
    async def test_create_stars_invoice(self, service, mock_subscription_service, mock_notification_service):
        """Test creating Stars invoice for subscription."""
        # Arrange
        mock_subscription_service.is_premium_user.return_value = False
        mock_subscription_service.get_plan_option.return_value = MagicMock(
            name="1 Month",
            duration_months=1,
            stars=360,
        )
        mock_notification_service.send_stars_invoice.return_value = True

        # Act
        result = await service.create_stars_invoice(
            user_id=123,
            plan_type="one_month",
            transaction_id="test_txn_123",
        )

        # Assert
        assert result["success"] is True
        assert result["amount_stars"] == 360
        mock_notification_service.send_stars_invoice.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_stars_invoice_fails_if_already_premium(self, service, mock_subscription_service):
        """Test that creating invoice fails if user already has subscription."""
        # Arrange
        mock_subscription_service.is_premium_user.return_value = True

        # Act & Assert
        with pytest.raises(ValueError, match="Ya tienes una suscripción activa"):
            await service.create_stars_invoice(
                user_id=123,
                plan_type="one_month",
                transaction_id="test_txn_123",
            )
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/application/services/test_subscription_payment_service.py::TestSubscriptionPaymentService::test_create_stars_invoice -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'application.services.subscription_payment_service'"

**Step 3: Write minimal implementation**

```python
# application/services/subscription_payment_service.py
"""Orquesta pagos de suscripciones (Stars + Crypto)."""

from utils.logger import logger


class SubscriptionPaymentService:
    """Orquesta pagos de suscripciones (Stars + Crypto)."""

    def __init__(
        self,
        subscription_service,
        notification_service,
        crypto_payment_service,
    ):
        self.subscription_service = subscription_service
        self.notification_service = notification_service
        self.crypto_payment_service = crypto_payment_service

    async def create_stars_invoice(
        self,
        user_id: int,
        plan_type: str,
        transaction_id: str,
    ) -> dict:
        """Crear factura Stars para suscripción."""
        plan_option = self.subscription_service.get_plan_option(plan_type)

        if not plan_option:
            raise ValueError(f"Plan no válido: {plan_type}")

        # Check existing subscription
        is_premium = await self.subscription_service.is_premium_user(user_id)
        if is_premium:
            raise ValueError("Ya tienes una suscripción activa")

        # Send invoice via Telegram Bot
        invoice_sent = await self.notification_service.send_stars_invoice(
            user_id=user_id,
            title=f"Suscripción {plan_option.name}",
            description=f"{plan_option.duration_months} meses de datos ilimitados",
            payload=f"subscription_{plan_type}_{user_id}_{transaction_id}",
            amount=plan_option.stars,
        )

        if not invoice_sent:
            raise Exception("No se pudo crear la factura")

        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount_stars": plan_option.stars,
        }

    async def create_crypto_order(
        self,
        user_id: int,
        plan_type: str,
        transaction_id: str,
    ) -> dict:
        """Crear orden crypto para suscripción."""
        plan_option = self.subscription_service.get_plan_option(plan_type)

        if not plan_option:
            raise ValueError(f"Plan no válido: {plan_type}")

        # Check existing subscription
        is_premium = await self.subscription_service.is_premium_user(user_id)
        if is_premium:
            raise ValueError("Ya tienes una suscripción activa")

        # Create crypto order via existing service
        usdt_amount = plan_option.usdt
        order_data = await self.crypto_payment_service.create_order(
            user_id=user_id,
            amount_usdt=usdt_amount,
            product_type="subscription",
            product_id=plan_type,
            transaction_id=transaction_id,
        )

        return {
            **order_data,
            "success": True,
            "plan_type": plan_type,
            "amount_usdt": usdt_amount,
        }
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/application/services/test_subscription_payment_service.py -v
```

Expected: PASS

**Step 5: Register in DI container**

Modify: `application/services/common/container.py`

```python
# Add subscription payment service
container.register(SubscriptionPaymentService)
```

**Step 6: Commit**

```bash
git add application/services/subscription_payment_service.py tests/application/services/test_subscription_payment_service.py
git add application/services/common/container.py
git commit -m "feat(application): add SubscriptionPaymentService for orchestrating subscription payments"
```

---

## Phase 4: Telegram Bot - Subscription Handlers

### Task 4.1: Create Subscription Handlers Module

**Files:**
- Create: `telegram_bot/features/subscriptions/__init__.py`
- Create: `telegram_bot/features/subscriptions/handlers_subscriptions.py`

**Step 1: Create __init__.py**

```python
# telegram_bot/features/subscriptions/__init__.py
"""Subscription module for Telegram Bot."""
```

**Step 2: Create handlers file**

```python
# telegram_bot/features/subscriptions/handlers_subscriptions.py
"""Handlers para módulo de suscripciones."""

import uuid
from telegram import Update
from telegram.ext import ContextTypes

from application.services.common.container import get_service
from application.services.subscription_service import SubscriptionService
from application.services.subscription_payment_service import SubscriptionPaymentService
from utils.logger import logger
from utils.telegram_utils import TelegramUtils

from .keyboards_subscriptions import SubscriptionKeyboards
from .messages_subscriptions import SubscriptionMessages


class SubscriptionsHandler:
    """Manages subscription-related conversations."""

    def __init__(self, subscription_service: SubscriptionService):
        self.subscription_service = subscription_service

    async def show_subscriptions_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra menú de planes de suscripción."""
        query = update.callback_query
        if query:
            await query.answer()

        message = SubscriptionMessages.Menu.PLANS_LIST
        keyboard = SubscriptionKeyboards.subscriptions_menu()

        if query:
            await TelegramUtils.safe_edit_message(
                query, context, text=message, reply_markup=keyboard, parse_mode="Markdown"
            )
        elif update.message:
            await update.message.reply_text(
                text=message, reply_markup=keyboard, parse_mode="Markdown"
            )

    async def select_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Usuario selecciona un plan específico."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        plan_type = query.data.split("_")[-1]  # e.g., "one_month"

        message = SubscriptionMessages.Payment.SELECT_METHOD.format(
            plan_name=plan_type.replace("_", " ").title(),
        )
        keyboard = SubscriptionKeyboards.payment_method_selection(plan_type)

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def select_payment_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa selección de método de pago."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        # Parse: pay_stars_one_month or pay_crypto_three_months
        parts = query.data.split("_")
        payment_method = parts[-2]  # "stars" or "crypto"
        plan_type = parts[-1]  # "one_month", etc.

        if payment_method == "stars":
            await self.process_stars_payment(update, context, plan_type)
        else:
            await self.process_crypto_payment(update, context, plan_type)

    async def process_stars_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type: str):
        """Procesa pago con Telegram Stars."""
        query = update.callback_query
        user_id = update.effective_user.id

        # Generate transaction ID
        transaction_id = str(uuid.uuid4())[:16]

        # Create invoice via service
        payment_service = get_service(SubscriptionPaymentService)
        result = await payment_service.create_stars_invoice(
            user_id=user_id,
            plan_type=plan_type,
            transaction_id=transaction_id,
        )

        # Send confirmation
        message = SubscriptionMessages.Payment.INVOICE_SENT
        await query.edit_message_text(text=message, parse_mode="Markdown")

    async def process_crypto_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type: str):
        """Procesa pago con Crypto (USDT)."""
        query = update.callback_query
        user_id = update.effective_user.id

        # Generate transaction ID
        transaction_id = str(uuid.uuid4())[:16]

        # Create crypto order
        payment_service = get_service(SubscriptionPaymentService)
        result = await payment_service.create_crypto_order(
            user_id=user_id,
            plan_type=plan_type,
            transaction_id=transaction_id,
        )

        # Send wallet info
        message = SubscriptionMessages.Crypto.PAYMENT_INFO.format(
            wallet_address=result["wallet_address"],
            amount_usdt=result["amount_usdt"],
            qr_code_url=result["qr_code_url"],
        )
        keyboard = SubscriptionKeyboards.crypto_payment_complete()

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def view_subscription_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra estado de suscripción activa."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        user_id = update.effective_user.id
        subscription = await self.subscription_service.get_active_subscription(user_id)

        if not subscription:
            message = SubscriptionMessages.Status.NO_ACTIVE_SUBSCRIPTION
            keyboard = SubscriptionKeyboards.back_to_plans()
        else:
            message = SubscriptionMessages.Status.ACTIVE_SUBSCRIPTION.format(
                plan_name=subscription.plan_type.value.replace("_", " ").title(),
                expires_at=subscription.expires_at.strftime("%Y-%m-%d %H:%M"),
                days_remaining=subscription.days_remaining,
            )
            keyboard = SubscriptionKeyboards.subscription_management()

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )
```

**Step 3: Commit**

```bash
git add telegram_bot/features/subscriptions/__init__.py
git add telegram_bot/features/subscriptions/handlers_subscriptions.py
git commit -m "feat(telegram_bot): add SubscriptionsHandler with Stars and Crypto payment flows"
```

---

### Task 4.2: Create Subscription Keyboards

**Files:**
- Create: `telegram_bot/features/subscriptions/keyboards_subscriptions.py`

**Step 1: Create keyboards file**

```python
# telegram_bot/features/subscriptions/keyboards_subscriptions.py
"""Teclados para módulo de suscripciones."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class SubscriptionKeyboards:
    """Teclados para módulo de suscripciones."""

    @staticmethod
    def subscriptions_menu() -> InlineKeyboardMarkup:
        """Menú principal con los 3 planes."""
        keyboard = [
            [
                InlineKeyboardButton("👑 1 Mes - 360⭐", callback_data="select_plan_one_month"),
                InlineKeyboardButton("🥈 3 Meses - 960⭐", callback_data="select_plan_three_months"),
            ],
            [
                InlineKeyboardButton("🥉 6 Meses - 1560⭐", callback_data="select_plan_six_months"),
            ],
            [
                InlineKeyboardButton("📊 Ver Mi Suscripción", callback_data="view_subscription_status"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="shop_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_method_selection(plan_type: str) -> InlineKeyboardMarkup:
        """Seleccionar método de pago (Stars | Crypto)."""
        keyboard = [
            [InlineKeyboardButton("⭐ Pagar con Stars", callback_data=f"pay_stars_{plan_type}")],
            [InlineKeyboardButton("💰 Pagar con Crypto", callback_data=f"pay_crypto_{plan_type}")],
            [InlineKeyboardButton("🔙 Volver a Planes", callback_data="subscription_plans_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def subscription_management() -> InlineKeyboardMarkup:
        """Gestión de suscripción activa."""
        keyboard = [
            [InlineKeyboardButton("🔁 Renovar", callback_data="renew_subscription")],
            [InlineKeyboardButton("📦 Ver Otros Planes", callback_data="subscription_plans_menu")],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def crypto_payment_complete() -> InlineKeyboardMarkup:
        """Confirmar pago crypto completado."""
        keyboard = [
            [InlineKeyboardButton("✅ Ya Envié el Pago", callback_data="crypto_payment_sent")],
            [InlineKeyboardButton("🔙 Volver", callback_data="subscription_plans_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_plans() -> InlineKeyboardMarkup:
        """Volver a planes."""
        keyboard = [
            [InlineKeyboardButton("📦 Ver Planes", callback_data="subscription_plans_menu")],
            [InlineKeyboardButton("🔙 Volver", callback_data="shop_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
```

**Step 2: Commit**

```bash
git add telegram_bot/features/subscriptions/keyboards_subscriptions.py
git commit -m "feat(telegram_bot): add SubscriptionKeyboards with payment method selection"
```

---

### Task 4.3: Create Subscription Messages

**Files:**
- Create: `telegram_bot/features/subscriptions/messages_subscriptions.py`

**Step 1: Create messages file**

```python
# telegram_bot/features/subscriptions/messages_subscriptions.py
"""Mensajes para módulo de suscripciones."""

from utils.message_separators import (
    MessageSeparatorBuilder,
    TELEGRAM_MOBILE_WIDTH,
)

_SEP_HEADER = (
    MessageSeparatorBuilder()
    .compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_DIVIDER = (
    MessageSeparatorBuilder()
    .compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
)


class SubscriptionMessages:
    """Mensajes para módulo de suscripciones."""

    class Menu:
        """Menú de planes."""

        _HEADER = (
            f"{_SEP_HEADER}\n"
            "🚀 PLANES PREMIUM\n"
            f"{_SEP_HEADER}\n"
        )

        _PLANS_LIST = (
            "┌──────────────────────────┐\n"
            "│ 👑 1 MES                 │\n"
            "│ ⭐ 360 Stars             │\n"
            "│ 💰 $2.99 USDT            │\n"
            "└──────────────────────────┘\n"
            "\n"
            "┌──────────────────────────┐\n"
            "│ 🥈 3 MESES               │\n"
            "│ ⭐ 960 Stars             │\n"
            "│ 💰 $7.99 USDT            │\n"
            "│ 💎 Ahorra 11%            │\n"
            "└──────────────────────────┘\n"
            "\n"
            "┌──────────────────────────┐\n"
            "│ 🥉 6 MESES               │\n"
            "│ ⭐ 1,560 Stars           │\n"
            "│ 💰 $12.99 USDT           │\n"
            "│ 💎 Ahorra 28%            │\n"
            "└──────────────────────────┘\n"
        )

        _BENEFITS = (
            "\n"
            "*Beneficios Incluidos:*\n"
            "├─ 📊 Datos ILIMITADOS\n"
            "├─ 🚀 Velocidad prioritaria\n"
            "├─ 💎 Soporte prioritario\n"
            "└─ ⚠️ Uso Justo (Fair Use)\n"
        )

        _FOOTER = (
            f"\n{_SEP_DIVIDER}\n"
            "👇 *Selecciona tu plan:*\n"
        )

        PLANS_LIST = _HEADER + _PLANS_LIST + _BENEFITS + _FOOTER

    class Payment:
        """Mensajes de pago."""

        SELECT_METHOD = (
            "💳 *Seleccionar Método de Pago*\n\n"
            "🚀 **Plan:** {plan_name}\n\n"
            "Elige cómo quieres pagar:\n"
        )

        INVOICE_SENT = (
            "✅ **Factura Enviada**\n\n"
            "Revisa tu chat de Telegram para completar el pago.\n\n"
            "💡 *La factura aparecerá en tu conversación con el bot*"
        )

    class Crypto:
        """Mensajes de pago crypto."""

        PAYMENT_INFO = (
            "💰 **Pago con USDT (BSC)**\n\n"
            "🏦 **Enviar a:**\n"
            "`{wallet_address}`\n\n"
            "💰 **Monto:** `{amount_usdt:.2f} USDT`\n\n"
            "🔗 **Red:** BSC (BEP20)\n\n"
            "⚠️ **Importante:**\n"
            "• Solo envía USDT en red BSC\n"
            "• El pago se detecta automáticamente\n"
            "• QR code enviado a tu Telegram\n\n"
        )

    class Status:
        """Estado de suscripción."""

        NO_ACTIVE_SUBSCRIPTION = (
            "⚠️ **Sin Suscripción Activa**\n\n"
            "No tienes una suscripción premium activa.\n\n"
            "💡 *Adquiere un plan para datos ilimitados*"
        )

        ACTIVE_SUBSCRIPTION = (
            "✅ **Suscripción Activa**\n\n"
            "🚀 **Plan:** {plan_name}\n"
            "📅 **Expira:** {expires_at}\n"
            "⏰ **Días restantes:** {days_remaining}\n\n"
            "💎 *Disfruta de datos ilimitados*"
        )
```

**Step 2: Commit**

```bash
git add telegram_bot/features/subscriptions/messages_subscriptions.py
git commit -m "feat(telegram_bot): add SubscriptionMessages with cyberpunk styling"
```

---

### Task 4.4: Register Subscription Handlers

**Files:**
- Modify: `telegram_bot/__init__.py` or `telegram_bot/router.py`

**Step 1: Add handler registration**

```python
# In telegram_bot/__init__.py or telegram_bot/router.py
from telegram_bot.features.subscriptions.handlers_subscriptions import SubscriptionsHandler

# Create handler instance
subscription_handler = SubscriptionsHandler(get_service(SubscriptionService))

# Register handlers
application.add_handler(
    CallbackQueryHandler(subscription_handler.show_subscriptions_menu, pattern="^subscription_plans_menu$")
)
application.add_handler(
    CallbackQueryHandler(subscription_handler.select_plan, pattern="^select_plan_")
)
application.add_handler(
    CallbackQueryHandler(subscription_handler.select_payment_method, pattern="^pay_(stars|crypto)_")
)
application.add_handler(
    CallbackQueryHandler(subscription_handler.view_subscription_status, pattern="^view_subscription_status$")
)
```

**Step 2: Update shop menu to include subscriptions**

Modify: `telegram_bot/features/operations/keyboards_operations.py`

```python
def shop_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📦 Paquetes de GB", callback_data="buy_gb_menu")],
        [InlineKeyboardButton("🚀 Planes Ilimitados", callback_data="subscription_plans_menu")],  # NEW
        [InlineKeyboardButton("🔑 Slots Adicionales", callback_data="buy_slots_menu")],
        [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 3: Commit**

```bash
git add telegram_bot/__init__.py
git add telegram_bot/features/operations/keyboards_operations.py
git commit -m "feat(telegram_bot): register subscription handlers and update shop menu"
```

---

## Phase 5: Mini App - Subscriptions Page

### Task 5.1: Add Subscriptions Route

**Files:**
- Modify: `miniapp/routes_subscriptions.py`

**Step 1: Add HTML route**

```python
# Add to miniapp/routes_subscriptions.py
from fastapi.responses import HTMLResponse
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_page(request: Request, ctx: MiniAppContext = Depends(get_current_user)):
    """Página dedicada para suscripciones premium."""
    logger.info(f"💎 MiniApp subscriptions page accessed by user {ctx.user.id}")

    # Get user's current subscription
    subscription_service = get_service(SubscriptionService)
    is_premium = await subscription_service.is_premium_user(ctx.user.id, ctx.user.id)
    subscription = await subscription_service.get_user_subscription(ctx.user.id, ctx.user.id)

    # Get plan options
    plan_options = [
        {
            "id": "one_month",
            "name": "1 Mes Premium",
            "duration_months": 1,
            "stars": 360,
            "usdt": 2.99,
            "badge": None,
            "featured": False,
        },
        {
            "id": "three_months",
            "name": "3 Meses Premium",
            "duration_months": 3,
            "stars": 960,
            "usdt": 7.99,
            "badge": "+11% BONUS",
            "featured": True,
        },
        {
            "id": "six_months",
            "name": "6 Meses Premium",
            "duration_months": 6,
            "stars": 1560,
            "usdt": 12.99,
            "badge": "+28% BONUS",
            "featured": False,
        },
    ]

    return templates.TemplateResponse(
        "subscriptions.html",
        {
            "request": request,
            "user": ctx.user,
            "plan_options": plan_options,
            "is_premium": is_premium,
            "current_subscription": subscription,
            "bot_username": settings.BOT_USERNAME,
        },
    )
```

**Step 2: Commit**

```bash
git add miniapp/routes_subscriptions.py
git commit -m "feat(miniapp): add /subscriptions route for premium plans page"
```

---

### Task 5.2: Create Subscriptions Template

**Files:**
- Create: `miniapp/templates/subscriptions.html`

**Step 1: Create template (full content in design doc)**

See full template in `/home/mowgli/usipipobot/docs/plans/2026-03-16-subscriptions-telegram-bot-integration.md` Section 4.2.

**Step 2: Commit**

```bash
git add miniapp/templates/subscriptions.html
git commit -m "feat(miniapp): add subscriptions.html template with cyberpunk theme"
```

---

### Task 5.3: Update Dashboard Navigation

**Files:**
- Modify: `miniapp/templates/dashboard.html`

**Step 1: Add premium button**

```html
<!-- Add to dashboard.html -->
<div class="card" style="margin-top: 20px;">
    <div class="card-title">💎 Premium</div>
    <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 12px;">
        Datos ilimitados para tus claves VPN
    </p>
    <button class="btn btn-primary btn-full" onclick="window.location.href='/miniapp/subscriptions'">
        🚀 Ver Planes Premium
    </button>
</div>
```

**Step 2: Commit**

```bash
git add miniapp/templates/dashboard.html
git commit -m "feat(miniapp): add premium button to dashboard navigation"
```

---

## Phase 6: Integration with VPN Services

### Task 6.1: Patch VpnService

**Files:**
- Modify: `application/services/vpn_service.py:123-145`

**Step 1: Add subscription check to create_key**

```python
# In VpnService.create_key()
async def create_key(self, user_id: int, ...) -> VpnKey:
    # Check if user has active subscription
    active_plan = await self.subscription_service.get_active_plan(user_id, user_id)
    is_premium = active_plan is not None

    # Create key with appropriate limits
    if is_premium:
        # Unlimited data for premium users
        key.data_limit_bytes = -1  # Special value for unlimited
        key.is_premium = True
        logger.info(f"👑 Creating premium key for user {user_id} (unlimited)")
    else:
        # Standard 5GB limit for free users
        key.data_limit_bytes = 5 * (1024 ** 3)
        key.is_premium = False
        logger.info(f"📊 Creating standard key for user {user_id} (5GB)")
```

**Step 2: Commit**

```bash
git add application/services/vpn_service.py
git commit -m "feat(application): patch VpnService to check subscription for unlimited data"
```

---

### Task 6.2: Patch ConsumptionBillingService

**Files:**
- Modify: `application/services/consumption_billing_service.py:89-112`

**Step 1: Add premium bypass**

```python
# In ConsumptionBillingService.consume_data()
async def consume_data(self, user_id: int, bytes_used: int) -> bool:
    # Check for active subscription first
    active_plan = await self.subscription_service.get_active_plan(user_id, user_id)

    if active_plan and active_plan.is_active:
        # Premium user - no consumption tracking needed
        logger.info(f"👑 Premium user {user_id} consuming {bytes_used} bytes (unlimited)")
        return True

    # Non-premium: use existing GB package logic
    return await self._consume_from_packages(user_id, bytes_used)
```

**Step 2: Commit**

```bash
git add application/services/consumption_billing_service.py
git commit -m "feat(application): patch ConsumptionBillingService to bypass GB tracking for premium"
```

---

## Phase 7: Testing

### Task 7.1: Run All Tests

**Step 1: Run full test suite**

Run:
```bash
uv run pytest
```

Expected: All tests pass (406+ backend + 8 android)

**Step 2: Fix any failures**

If any tests fail, fix them and re-run.

**Step 3: Commit**

```bash
git commit -am "fix: fix test failures from subscription implementation"
```

---

## Phase 8: Deployment

### Task 8.1: Deploy to Production

**Step 1: Backup database**

Run:
```bash
pg_dump vpn_manager > backup_$(date +%Y%m%d_%H%M%S).sql
```

**Step 2: Run migrations**

Run:
```bash
uv run alembic upgrade head
```

**Step 3: Sync dependencies**

Run:
```bash
uv sync
```

**Step 4: Restart service**

Run:
```bash
sudo systemctl restart usipipo
```

**Step 5: Verify logs**

Run:
```bash
sudo journalctl -u usipipo -f --no-pager | tail -50
```

Expected: No errors

**Step 6: Manual testing**

- Open bot: `/suscripciones`
- Select plan
- Test Stars payment flow
- Test Crypto payment flow
- Verify Mini App `/miniapp/subscriptions` page

**Step 7: Commit deployment**

```bash
git tag -a v3.10.0 -m "Release: Subscription Plans with Telegram Bot + Mini App"
git push origin v3.10.0
```

---

## Verification Checklist

### ✅ Definition of Done

- [ ] All domain layer tests passing
- [ ] All infrastructure tests passing
- [ ] All service tests passing
- [ ] Bot handlers working (manual test)
- [ ] Mini App page working (manual test)
- [ ] VPN integration working (manual test)
- [ ] All tests passing in CI
- [ ] Migration applied successfully
- [ ] No errors in logs
- [ ] Manual testing completed

---

**Plan complete!** Total estimated time: **30 hours** across 8 phases.
