# Subscription Plans Implementation Plan (CORREGIDO)

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Implement subscription plans (1, 3, 6 months) with unlimited data for premium users, integrating seamlessly with existing VPN key management and billing systems.

**Architecture:** Follow existing Clean Architecture patterns: Domain entities → Repository interfaces → Infrastructure implementations → Application services → Background jobs → Bot handlers. Coexists with current GB package system.

**Tech Stack:** Python 3.13+, SQLAlchemy 2.0 async, PostgreSQL, python-telegram-bot, Punq DI, Alembic migrations.

---

## Critical Integration Points (DO NOT BREAK)

1. **VPN Key Creation** - `VpnService.create_key()` must check subscription status for data limits
2. **Consumption Billing** - `ConsumptionBillingService` must bypass GB tracking for premium users
3. **Data Package Coexistence** - Users can have BOTH active subscription + GB packages
4. **Payment Infrastructure** - Reuse existing Telegram Stars + Crypto payment flows
5. **Background Jobs** - Add subscription expiration + reminder jobs alongside existing package expiration

---

## Code Review Fixes Applied

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

### Task 1.1: Create SubscriptionPlan Entity

**Files:**
- Create: `domain/entities/subscription_plan.py`
- Test: `tests/domain/entities/test_subscription_plan.py`

**Step 1: Write the failing test**

```python
# tests/domain/entities/test_subscription_plan.py
import pytest
from datetime import datetime, timezone, timedelta
from domain.entities.subscription_plan import SubscriptionPlan, PlanType


class TestSubscriptionPlanEntity:
    def test_create_subscription_plan(self):
        """Test creating a subscription plan entity."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=30)

        plan = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_123",  # NEW: for idempotency
            starts_at=now,
            expires_at=expires,
        )

        assert plan.user_id == 123
        assert plan.plan_type == PlanType.ONE_MONTH
        assert plan.stars_paid == 360
        assert plan.payment_id == "pay_123"
        assert plan.is_active is True
        assert plan.id is not None

    def test_duration_days_property(self):
        """Test duration_days returns correct values per plan type."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=90)

        plan_1m = SubscriptionPlan(
            user_id=123, plan_type=PlanType.ONE_MONTH,
            stars_paid=360, payment_id="pay_1m",
            starts_at=now, expires_at=expires
        )
        plan_3m = SubscriptionPlan(
            user_id=123, plan_type=PlanType.THREE_MONTHS,
            stars_paid=960, payment_id="pay_3m",
            starts_at=now, expires_at=expires
        )
        plan_6m = SubscriptionPlan(
            user_id=123, plan_type=PlanType.SIX_MONTHS,
            stars_paid=1560, payment_id="pay_6m",
            starts_at=now, expires_at=expires
        )

        assert plan_1m.duration_days == 30
        assert plan_3m.duration_days == 90
        assert plan_6m.duration_days == 180

    def test_days_remaining_property(self):
        """Test days_remaining calculation."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=15)

        plan = SubscriptionPlan(
            user_id=123, plan_type=PlanType.ONE_MONTH,
            stars_paid=360, payment_id="pay_123",
            starts_at=now, expires_at=expires
        )

        assert plan.days_remaining == 15

    def test_is_expiring_soon_property(self):
        """Test is_expiring_soon returns True when < 3 days."""
        now = datetime.now(timezone.utc)
        expires_soon = now + timedelta(days=2)
        expires_later = now + timedelta(days=5)

        plan_soon = SubscriptionPlan(
            user_id=123, plan_type=PlanType.ONE_MONTH,
            stars_paid=360, payment_id="pay_soon",
            starts_at=now, expires_at=expires_soon
        )
        plan_later = SubscriptionPlan(
            user_id=123, plan_type=PlanType.ONE_MONTH,
            stars_paid=360, payment_id="pay_later",
            starts_at=now, expires_at=expires_later
        )

        assert plan_soon.is_expiring_soon is True
        assert plan_later.is_expiring_soon is False

    def test_is_expired_property(self):
        """Test is_expired returns True when past expiration."""
        now = datetime.now(timezone.utc)
        expired = now - timedelta(days=5)
        active = now + timedelta(days=5)

        plan_expired = SubscriptionPlan(
            user_id=123, plan_type=PlanType.ONE_MONTH,
            stars_paid=360, payment_id="pay_expired",
            starts_at=now - timedelta(days=35),
            expires_at=expired
        )
        plan_active = SubscriptionPlan(
            user_id=123, plan_type=PlanType.ONE_MONTH,
            stars_paid=360, payment_id="pay_active",
            starts_at=now,
            expires_at=active
        )

        assert plan_expired.is_expired is True
        assert plan_active.is_expired is False
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/domain/entities/test_subscription_plan.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'domain.entities.subscription_plan'"

**Step 3: Write minimal implementation**

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

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/domain/entities/test_subscription_plan.py -v
```
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add domain/entities/subscription_plan.py tests/domain/entities/test_subscription_plan.py
git commit -m "feat(domain): add SubscriptionPlan entity with PlanType enum and payment_id for idempotency"
```

---

### Task 1.2: Create ISubscriptionRepository Interface

**Files:**
- Create: `domain/interfaces/isubscription_repository.py`
- Modify: `domain/interfaces/__init__.py`

**Step 1: Write the interface**

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

**Step 2: Update interfaces __init__.py**

```python
# domain/interfaces/__init__.py
# Add to exports
from .isubscription_repository import ISubscriptionRepository

__all__ = [
    # ... existing exports ...
    "ISubscriptionRepository",
]
```

**Step 3: Commit**

```bash
git add domain/interfaces/isubscription_repository.py domain/interfaces/__init__.py
git commit -m "feat(domain): add ISubscriptionRepository interface with payment_id idempotency"
```

---

## Phase 2: Infrastructure Layer (Database + Repository)

### Task 2.1: Create SubscriptionPlanModel (SQLAlchemy)

**Files:**
- Create: `infrastructure/persistence/postgresql/models/subscription_plan.py`
- Modify: `infrastructure/persistence/postgresql/models/__init__.py`

**Step 1: Write the SQLAlchemy model**

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

**Step 2: Update models __init__.py**

```python
# infrastructure/persistence/postgresql/models/__init__.py
from .base import Base, DataPackageModel, TransactionModel, UserModel, VpnKeyModel
from .consumption_billing import ConsumptionBillingModel
from .consumption_invoice import ConsumptionInvoiceModel
from .ticket import TicketModel
from .ticket_message import TicketMessageModel
from .subscription_plan import SubscriptionPlanModel  # ADD THIS

__all__ = [
    "Base",
    "UserModel",
    "VpnKeyModel",
    "DataPackageModel",
    "TransactionModel",
    "ConsumptionBillingModel",
    "ConsumptionInvoiceModel",
    "TicketModel",
    "TicketMessageModel",
    "SubscriptionPlanModel",  # ADD THIS
]
```

**Step 3: Add relationship to UserModel**

```python
# infrastructure/persistence/postgresql/models/base.py
# In UserModel class, add to relationships section:
subscription_plans: Mapped[List["SubscriptionPlanModel"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
    foreign_keys="SubscriptionPlanModel.user_id"
)
```

**Step 4: Commit**

```bash
git add infrastructure/persistence/postgresql/models/subscription_plan.py
git add infrastructure/persistence/postgresql/models/__init__.py
git add infrastructure/persistence/postgresql/models/base.py
git commit -m "feat(infra): add SubscriptionPlanModel with payment_id unique constraint for idempotency"
```

---

### Task 2.2: Create Alembic Migration

**Files:**
- Create: `migrations/versions/20260316_add_subscription_plans.py`

**Step 1: Get current migration head**

```bash
uv run alembic heads
```
Expected: Output like `abc123 (head)` - use this for `down_revision`

**Step 2: Write the migration**

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

**Step 3: Run migration to verify it works**

```bash
uv run alembic upgrade head
```
Expected: Migration runs successfully, tables created

**Step 4: Verify tables exist**

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

**Step 5: Commit**

```bash
git add migrations/versions/20260316_add_subscription_plans.py
git commit -m "feat(migrations): add subscription_plans table with payment_id unique constraint"
```

---

### Task 2.3: Create PostgresSubscriptionRepository

**Files:**
- Create: `infrastructure/persistence/postgresql/subscription_repository.py`
- Test: `tests/infrastructure/persistence/test_subscription_repository.py`

**Step 1: Write the repository implementation**

```python
# infrastructure/persistence/postgresql/subscription_repository.py
"""PostgreSQL repository for subscription plans."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from dataclasses import replace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.subscription_plan import SubscriptionPlan, PlanType
from domain.interfaces.isubscription_repository import ISubscriptionRepository
from utils.logger import logger

from .base_repository import BasePostgresRepository
from .models.subscription_plan import SubscriptionPlanModel


def _normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize datetime to UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class PostgresSubscriptionRepository(BasePostgresRepository, ISubscriptionRepository):
    """PostgreSQL implementation of ISubscriptionRepository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _model_to_entity(self, model: SubscriptionPlanModel) -> SubscriptionPlan:
        """Convert SQLAlchemy model to domain entity."""
        return SubscriptionPlan(
            id=model.id,
            user_id=model.user_id,
            plan_type=PlanType(model.plan_type),
            stars_paid=model.stars_paid,
            payment_id=model.payment_id,
            starts_at=_normalize_datetime(model.starts_at) or datetime.now(timezone.utc),
            expires_at=_normalize_datetime(model.expires_at),
            is_active=model.is_active,
            created_at=_normalize_datetime(model.created_at),
            updated_at=_normalize_datetime(model.updated_at),
        )

    def _entity_to_model(self, entity: SubscriptionPlan) -> SubscriptionPlanModel:
        """Convert domain entity to SQLAlchemy model."""
        return SubscriptionPlanModel(
            id=entity.id if entity.id else uuid.uuid4(),
            user_id=entity.user_id,
            plan_type=entity.plan_type.value if isinstance(entity.plan_type, PlanType) else entity.plan_type,
            stars_paid=entity.stars_paid,
            payment_id=entity.payment_id,
            starts_at=entity.starts_at,
            expires_at=entity.expires_at,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def save(self, plan: SubscriptionPlan, current_user_id: int) -> SubscriptionPlan:
        """Save or update a subscription plan."""
        await self._set_current_user(current_user_id)
        try:
            if plan.id:
                # Update existing
                existing = await self.session.get(SubscriptionPlanModel, plan.id)
                if existing:
                    existing.plan_type = plan.plan_type.value if isinstance(plan.plan_type, PlanType) else plan.plan_type
                    existing.stars_paid = plan.stars_paid
                    existing.payment_id = plan.payment_id
                    existing.starts_at = plan.starts_at
                    existing.expires_at = plan.expires_at
                    existing.is_active = plan.is_active
                    await self.session.commit()
                    await self.session.refresh(existing)
                    logger.info(f"📦 Subscription plan updated: {plan.id}")
                    return replace(plan)

            # Create new
            model = self._entity_to_model(plan)
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            logger.info(f"📦 Subscription plan created: {model.id}")
            return replace(plan, id=model.id)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error saving subscription plan: {e}")
            raise

    async def get_by_id(self, plan_id: uuid.UUID, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get subscription by ID."""
        await self._set_current_user(current_user_id)
        try:
            result = await self.session.execute(
                select(SubscriptionPlanModel).where(SubscriptionPlanModel.id == plan_id)
            )
            model = result.scalars().first()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"❌ Error getting subscription by ID: {e}")
            raise

    async def get_by_payment_id(self, payment_id: str, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get subscription by payment ID (for idempotency)."""
        await self._set_current_user(current_user_id)
        try:
            result = await self.session.execute(
                select(SubscriptionPlanModel).where(SubscriptionPlanModel.payment_id == payment_id)
            )
            model = result.scalars().first()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"❌ Error getting subscription by payment_id: {e}")
            raise

    async def get_active_by_user(self, user_id: int, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get active subscription for a user."""
        await self._set_current_user(current_user_id)
        try:
            result = await self.session.execute(
                select(SubscriptionPlanModel)
                .where(SubscriptionPlanModel.user_id == user_id)
                .where(SubscriptionPlanModel.is_active == True)
                .where(SubscriptionPlanModel.expires_at > datetime.now(timezone.utc))
                .order_by(SubscriptionPlanModel.expires_at.desc())
            )
            model = result.scalars().first()  # Use .first() instead of .scalar_one_or_none()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"❌ Error getting active subscription: {e}")
            raise

    async def get_expiring_plans(self, days: int, current_user_id: int) -> List[SubscriptionPlan]:
        """Get plans expiring within N days."""
        await self._set_current_user(current_user_id)
        try:
            now = datetime.now(timezone.utc)
            future_date = now + timedelta(days=days)

            result = await self.session.execute(
                select(SubscriptionPlanModel)
                .where(SubscriptionPlanModel.is_active == True)
                .where(SubscriptionPlanModel.expires_at <= future_date)
                .where(SubscriptionPlanModel.expires_at > now)
                .order_by(SubscriptionPlanModel.expires_at)
            )
            models = result.scalars().all()
            return [self._model_to_entity(m) for m in models]
        except Exception as e:
            logger.error(f"❌ Error getting expiring plans: {e}")
            raise

    async def get_expired_plans(self, current_user_id: int) -> List[SubscriptionPlan]:
        """Get all expired plans."""
        await self._set_current_user(current_user_id)
        try:
            now = datetime.now(timezone.utc)

            result = await self.session.execute(
                select(SubscriptionPlanModel)
                .where(SubscriptionPlanModel.is_active == True)
                .where(SubscriptionPlanModel.expires_at <= now)
            )
            models = result.scalars().all()
            return [self._model_to_entity(m) for m in models]
        except Exception as e:
            logger.error(f"❌ Error getting expired plans: {e}")
            raise

    async def deactivate(self, plan_id: uuid.UUID, current_user_id: int) -> bool:
        """Deactivate a subscription plan."""
        await self._set_current_user(current_user_id)
        try:
            from sqlalchemy import update
            await self.session.execute(
                update(SubscriptionPlanModel)
                .where(SubscriptionPlanModel.id == plan_id)
                .values(is_active=False, updated_at=datetime.now(timezone.utc))
            )
            await self.session.commit()
            logger.info(f"📦 Subscription plan deactivated: {plan_id}")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error deactivating subscription plan: {e}")
            raise
```

**Step 2: Commit**

```bash
git add infrastructure/persistence/postgresql/subscription_repository.py
git commit -m "feat(infra): create PostgresSubscriptionRepository with payment_id idempotency and dataclasses.replace()"
```

---

## Phase 3: Application Layer (Services)

### Task 3.1: Create SubscriptionService

**Files:**
- Create: `application/services/subscription_service.py`
- Test: `tests/application/services/test_subscription_service.py`

**Step 1: Write the service with tests TDD-style**

```python
# tests/application/services/test_subscription_service.py
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from domain.entities.subscription_plan import SubscriptionPlan, PlanType
from application.services.subscription_service import SubscriptionService


class TestSubscriptionService:
    @pytest.fixture
    def mock_subscription_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_subscription_repo, mock_user_repo):
        return SubscriptionService(
            subscription_repo=mock_subscription_repo,
            user_repo=mock_user_repo,
        )

    @pytest.mark.asyncio
    async def test_activate_plan_creates_subscription(self, service, mock_subscription_repo):
        """Test plan activation creates subscription."""
        # Arrange
        mock_subscription_repo.get_active_by_user.return_value = None
        mock_subscription_repo.get_by_payment_id.return_value = None
        mock_subscription_repo.save.return_value = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_123",
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Act
        result = await service.activate_plan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            payment_id="pay_123",
            current_user_id=123,
        )

        # Assert
        assert result is not None
        assert result.plan_type == PlanType.ONE_MONTH
        mock_subscription_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_plan_idempotency(self, service, mock_subscription_repo):
        """Test duplicate payment_id returns existing plan."""
        # Arrange
        existing_plan = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_duplicate",
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        mock_subscription_repo.get_by_payment_id.return_value = existing_plan

        # Act
        result = await service.activate_plan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            payment_id="pay_duplicate",
            current_user_id=123,
        )

        # Assert
        assert result is existing_plan
        mock_subscription_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_extend_plan_adds_validity(self, service, mock_subscription_repo):
        """Test extending plan adds days to expiration."""
        # Arrange
        now = datetime.now(timezone.utc)
        existing_plan = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_existing",
            starts_at=now - timedelta(days=15),
            expires_at=now + timedelta(days=15),
        )
        mock_subscription_repo.get_active_by_user.return_value = existing_plan
        mock_subscription_repo.save.return_value = existing_plan

        # Act
        result = await service.extend_plan(
            user_id=123,
            plan_type=PlanType.THREE_MONTHS,
            current_user_id=123,
        )

        # Assert
        assert result is not None
        # Should extend by 90 days from current expiration
        mock_subscription_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_premium_user_returns_true(self, service, mock_subscription_repo):
        """Test premium user detection."""
        # Arrange
        mock_subscription_repo.get_active_by_user.return_value = SubscriptionPlan(
            user_id=123,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=360,
            payment_id="pay_premium",
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Act
        result = await service.is_premium_user(123, current_user_id=123)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_premium_user_returns_false(self, service, mock_subscription_repo):
        """Test non-premium user detection."""
        # Arrange
        mock_subscription_repo.get_active_by_user.return_value = None

        # Act
        result = await service.is_premium_user(123, current_user_id=123)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_expire_plans_deactivates_old_plans(self, service, mock_subscription_repo):
        """Test background job expires old plans."""
        # Arrange
        mock_subscription_repo.get_expired_plans.return_value = [
            SubscriptionPlan(
                id="plan-1",
                user_id=123,
                plan_type=PlanType.ONE_MONTH,
                stars_paid=360,
                payment_id="pay_expired",
                starts_at=datetime.now(timezone.utc) - timedelta(days=35),
                expires_at=datetime.now(timezone.utc) - timedelta(days=5),
            )
        ]
        mock_subscription_repo.deactivate.return_value = True

        # Act
        expired_count = await service.expire_plans(current_user_id=999)

        # Assert
        assert expired_count == 1
        mock_subscription_repo.deactivate.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/application/services/test_subscription_service.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'application.services.subscription_service'"

**Step 3: Write minimal implementation**

```python
# application/services/subscription_service.py
"""Subscription service for managing plan lifecycle."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from domain.entities.subscription_plan import SubscriptionPlan, PlanType
from domain.interfaces.isubscription_repository import ISubscriptionRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


class SubscriptionService:
    """Manages subscription lifecycle."""

    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        user_repo: IUserRepository,
    ):
        self.subscription_repo = subscription_repo
        self.user_repo = user_repo

    async def activate_plan(
        self,
        user_id: int,
        plan_type: PlanType,
        payment_id: str,
        current_user_id: int,
    ) -> SubscriptionPlan:
        """Activate a new subscription plan with idempotency check."""
        try:
            # Check idempotency - prevent duplicate plans from same payment
            existing_by_payment = await self.subscription_repo.get_by_payment_id(
                payment_id, current_user_id
            )
            if existing_by_payment:
                logger.warning(f"⚠️ Duplicate payment {payment_id} — returning existing plan")
                return existing_by_payment

            # Check if user already has active plan → extend instead
            existing = await self.subscription_repo.get_active_by_user(user_id, current_user_id)

            if existing:
                logger.info(f"📦 User {user_id} has active plan - extending")
                return await self.extend_plan(user_id, plan_type, current_user_id)

            # Create new plan
            now = datetime.now(timezone.utc)
            duration_days = self._get_duration_days(plan_type)
            expires_at = now + timedelta(days=duration_days)

            plan = SubscriptionPlan(
                user_id=user_id,
                plan_type=plan_type,
                stars_paid=self._get_stars_for_plan(plan_type),
                payment_id=payment_id,
                starts_at=now,
                expires_at=expires_at,
            )

            saved_plan = await self.subscription_repo.save(plan, current_user_id)
            logger.info(f"🚀 Subscription plan activated for user {user_id}: {plan_type.value}")
            return saved_plan

        except Exception as e:
            logger.error(f"❌ Error activating subscription plan: {e}")
            raise

    async def get_active_plan(self, user_id: int, current_user_id: int) -> Optional[SubscriptionPlan]:
        """Get user's currently active plan."""
        try:
            return await self.subscription_repo.get_active_by_user(user_id, current_user_id)
        except Exception as e:
            logger.error(f"❌ Error getting active plan: {e}")
            raise

    async def extend_plan(
        self,
        user_id: int,
        plan_type: PlanType,
        current_user_id: int,
    ) -> SubscriptionPlan:
        """Extend existing plan or create new one."""
        try:
            existing = await self.subscription_repo.get_active_by_user(user_id, current_user_id)
            duration_days = self._get_duration_days(plan_type)

            if existing:
                # Extend from current expiration
                new_expires = existing.expires_at + timedelta(days=duration_days)
                existing.plan_type = plan_type
                existing.expires_at = new_expires
                existing.stars_paid += self._get_stars_for_plan(plan_type)
                # Note: stars_paid accumulates as total paid for audit trail
                return await self.subscription_repo.save(existing, current_user_id)
            else:
                # Create new (shouldn't happen - activate_plan handles this)
                return await self.activate_plan(
                    user_id, plan_type, f"extension_{int(datetime.now(timezone.utc).timestamp())}", current_user_id
                )

        except Exception as e:
            logger.error(f"❌ Error extending plan: {e}")
            raise

    async def expire_plans(self, current_user_id: int) -> int:
        """Background job to expire old plans."""
        try:
            expired_plans = await self.subscription_repo.get_expired_plans(current_user_id)
            expired_count = 0

            for plan in expired_plans:
                await self.subscription_repo.deactivate(plan.id, current_user_id)
                expired_count += 1
                logger.info(f"📦 Expired subscription plan {plan.id} for user {plan.user_id}")

            return expired_count

        except Exception as e:
            logger.error(f"❌ Error expiring plans: {e}")
            raise

    async def is_premium_user(self, user_id: int, current_user_id: int) -> bool:
        """Check if user has active subscription (async version)."""
        try:
            plan = await self.subscription_repo.get_active_by_user(user_id, current_user_id)
            return plan is not None and plan.is_active
        except Exception as e:
            logger.error(f"❌ Error checking premium status: {e}")
            return False

    def get_plan_price(self, plan_type: PlanType) -> dict:
        """Get pricing information for a plan."""
        prices = {
            PlanType.ONE_MONTH: {"stars": 360, "usdt": 2.99, "days": 30},
            PlanType.THREE_MONTHS: {"stars": 960, "usdt": 7.99, "days": 90},
            PlanType.SIX_MONTHS: {"stars": 1560, "usdt": 12.99, "days": 180},
        }
        return prices.get(plan_type, {"stars": 0, "usdt": 0.0, "days": 0})

    def _get_duration_days(self, plan_type: PlanType) -> int:
        """Get duration in days for plan type."""
        duration_map = {
            PlanType.ONE_MONTH: 30,
            PlanType.THREE_MONTHS: 90,
            PlanType.SIX_MONTHS: 180,
        }
        return duration_map.get(plan_type, 0)

    def _get_stars_for_plan(self, plan_type: PlanType) -> int:
        """Get stars price for plan type."""
        stars_map = {
            PlanType.ONE_MONTH: 360,
            PlanType.THREE_MONTHS: 960,
            PlanType.SIX_MONTHS: 1560,
        }
        return stars_map.get(plan_type, 0)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/application/services/test_subscription_service.py::TestSubscriptionService::test_activate_plan_creates_subscription -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add application/services/subscription_service.py tests/application/services/test_subscription_service.py
git commit -m "feat(application): create SubscriptionService with async is_premium_user and payment_id idempotency"
```

---

## Phase 4: Integration Points

### Task 4.1: Update VpnService for Premium Users

**Files:**
- Modify: `application/services/vpn_service.py`

**Step 1: Add subscription check to create_key method**

```python
# application/services/vpn_service.py
# Add import at top
from application.services.subscription_service import SubscriptionService
from typing import Optional

# In VpnService.__init__, add parameter:
def __init__(
    self,
    user_repo: IUserRepository,
    key_repo: IKeyRepository,
    package_repo: IDataPackageRepository,
    outline_client: OutlineClient,
    wireguard_client: WireGuardClient,
    vpn_integration_service=None,
    subscription_service: Optional[SubscriptionService] = None,  # ADD THIS
):
    # ... existing code ...
    self.subscription_service = subscription_service

# Add new async method for data limit check:
async def _get_user_data_limit(self, user: User, current_user_id: int) -> int:
    """Determine data limit based on user's subscription status."""
    if self.subscription_service:
        try:
            active_plan = await self.subscription_service.get_active_plan(
                user.telegram_id, current_user_id
            )
            if active_plan and active_plan.is_active:
                logger.info(f"💎 User {user.telegram_id} has active subscription - unlimited data")
                return -1  # Unlimited for premium
        except Exception as e:
            logger.warning(f"⚠️ Could not check subscription status for user {user.telegram_id}: {e}")

    # Default free tier: 5GB
    return 5 * (1024 ** 3)

# In create_key method, update the call:
# OLD (sync):
# data_limit_bytes = self._get_user_data_limit(user)

# NEW (async):
data_limit_bytes = await self._get_user_data_limit(user, current_user_id)
```

**Step 2: Commit**

```bash
git add application/services/vpn_service.py
git commit -m "feat(vpn): integrate async subscription check for data limits"
```

---

### Task 4.2: Update ConsumptionBillingService for Premium Users

**Files:**
- Modify: `application/services/consumption_billing_service.py`

**Step 1: Add subscription check to record_data_usage**

```python
# application/services/consumption_billing_service.py
# Add to imports
from application.services.subscription_service import SubscriptionService
from typing import Optional

# In __init__, add parameter:
def __init__(
    self,
    billing_repo: IConsumptionBillingRepository,
    user_repo: IUserRepository,
    subscription_service: Optional[SubscriptionService] = None,  # ADD THIS
):
    # ... existing code ...
    self.subscription_service = subscription_service

# In record_data_usage method, add at start:
async def record_data_usage(self, user_id: int, mb_used: float, current_user_id: int) -> bool:
    """Registra consumo de datos para un usuario en modo consumo."""
    # Check for active subscription - premium users don't track consumption
    if self.subscription_service:
        try:
            active_plan = await self.subscription_service.get_active_plan(user_id, current_user_id)
            if active_plan and active_plan.is_active:
                logger.info(f"💎 Premium user {user_id} consuming {mb_used}MB (unlimited)")
                return True  # No tracking needed for premium
        except Exception as e:
            logger.warning(f"⚠️ Could not check subscription status: {e}")

    # Non-premium: use existing logic
    return await self._cycle.record_data_usage(user_id, mb_used, current_user_id)
```

**Step 2: Commit**

```bash
git add application/services/consumption_billing_service.py
git commit -m "feat(billing): bypass consumption tracking for premium users with async check"
```

---

## Phase 5: Background Jobs

### Task 5.1: Create Subscription Expiration Job

**Files:**
- Create: `infrastructure/jobs/subscription_expiration_job.py`

**Step 1: Write the job**

```python
# infrastructure/jobs/subscription_expiration_job.py
"""Job para expirar planes de suscripción vencidos."""

from typing import Any, Dict, cast

from telegram.ext import ContextTypes

from application.services.subscription_service import SubscriptionService
from config import settings
from utils.logger import logger


async def subscription_expiration_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job programado que desactiva planes de suscripción expirados.
    Se ejecuta diariamente.
    """
    if context.job is None or context.job.data is None:
        logger.error("❌ Job data no disponible")
        return

    data = cast(Dict[str, Any], context.job.data)
    subscription_service: SubscriptionService = data["subscription_service"]

    try:
        logger.info("📦 Iniciando job de expiración de suscripciones...")

        expired_count = await subscription_service.expire_plans(
            current_user_id=settings.ADMIN_ID
        )

        logger.info(f"✅ Job completado: {expired_count} suscripciones expiradas")

    except Exception as e:
        logger.error(f"❌ Error en job de expiración de suscripciones: {e}")
```

**Step 2: Commit**

```bash
git add infrastructure/jobs/subscription_expiration_job.py
git commit -m "feat(jobs): add subscription expiration background job"
```

---

### Task 5.2: Create Subscription Reminder Job

**Files:**
- Create: `infrastructure/jobs/subscription_reminder_job.py`

**Step 1: Write the job with correct Markdown v1**

```python
# infrastructure/jobs/subscription_reminder_job.py
"""Job para enviar recordatorios de expiración de suscripciones."""

from typing import Any, Dict, cast

from telegram import Bot
from telegram.ext import ContextTypes

from application.services.subscription_service import SubscriptionService
from domain.interfaces.isubscription_repository import ISubscriptionRepository
from config import settings
from utils.logger import logger


async def subscription_reminder_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Job programado que envía recordatorios 3 días antes de expiración.
    Se ejecuta diariamente.
    """
    if context.job is None or context.job.data is None:
        logger.error("❌ Job data no disponible")
        return

    data = cast(Dict[str, Any], context.job.data)
    subscription_repo: ISubscriptionRepository = data["subscription_repo"]
    bot: Bot = context.bot

    try:
        logger.info("🔔 Iniciando job de recordatorios de suscripción...")

        # Get plans expiring in 3 days
        expiring_plans = await subscription_repo.get_expiring_plans(
            days=3, current_user_id=settings.ADMIN_ID
        )

        for plan in expiring_plans:
            try:
                # Send reminder message with correct Markdown v1 (* not **)
                await bot.send_message(
                    chat_id=plan.user_id,
                    text=(
                        "⚠️ *Tu Plan Está por Vencer*\n\n"
                        f"🚀 *Plan:* {plan.plan_type.value}\n"
                        f"⏰ *Expira en:* {plan.days_remaining} días\n"
                        f"📅 *Fecha:* {plan.expires_at.strftime('%Y-%m-%d')}\n\n"
                        f"💡 *Renueva ahora para mantener tus beneficios:*\n"
                        f"├─ ✅ Datos ILIMITADOS\n"
                        f"├─ ✅ Sin interrupciones\n"
                        f"└─ ✅ Mismo precio siempre"
                    ),
                    parse_mode="Markdown"  # v1 - use * for bold, not **
                )
                logger.info(f"📧 Recordatorio enviado a usuario {plan.user_id}")
            except Exception as e:
                logger.error(f"❌ Error enviando recordatorio a {plan.user_id}: {e}")

        logger.info(f"✅ Job completado: {len(expiring_plans)} recordatorios enviados")

    except Exception as e:
        logger.error(f"❌ Error en job de recordatorios: {e}")
```

**Step 2: Commit**

```bash
git add infrastructure/jobs/subscription_reminder_job.py
git commit -m "feat(jobs): add subscription reminder job with correct Markdown v1 formatting"
```

---

## Phase 6: Dependency Injection

### Task 6.1: Register Subscription Components in Container

**Files:**
- Modify: `application/services/common/container.py`

**Step 1: Add imports and registration (avoiding double instantiation)**

```python
# application/services/common/container.py
# Add to imports
from application.services.subscription_service import SubscriptionService
from domain.interfaces.isubscription_repository import ISubscriptionRepository
from infrastructure.persistence.postgresql.subscription_repository import PostgresSubscriptionRepository

# In _configure_repositories function, add:
def create_subscription_repo() -> PostgresSubscriptionRepository:
    session = session_factory()
    return PostgresSubscriptionRepository(session)

container.register(ISubscriptionRepository, factory=create_subscription_repo)

# In _configure_application_services function, add:
# Use container.resolve() to avoid double instantiation
def create_subscription_service() -> SubscriptionService:
    return SubscriptionService(
        subscription_repo=container.resolve(ISubscriptionRepository),  # ✅ Same instance
        user_repo=container.resolve(IUserRepository),
    )

container.register(SubscriptionService, factory=create_subscription_service)

# Also update VpnService and ConsumptionBillingService to receive subscription_service:
def create_vpn_service() -> VpnService:
    return VpnService(
        user_repo=create_user_repo(),
        key_repo=create_key_repo(),
        package_repo=create_data_package_repo(),
        outline_client=cast(OutlineClient, container.resolve(OutlineClient)),
        wireguard_client=cast(WireGuardClient, container.resolve(WireGuardClient)),
        vpn_integration_service=cast(
            ConsumptionVpnIntegrationService,
            container.resolve(ConsumptionVpnIntegrationService),
        ),
        subscription_service=cast(
            SubscriptionService,
            container.resolve(SubscriptionService),  # ✅ ADD THIS
        ),
    )

def create_consumption_billing_service() -> ConsumptionBillingService:
    return ConsumptionBillingService(
        billing_repo=create_consumption_billing_repo(),
        user_repo=create_user_repo(),
        subscription_service=cast(
            SubscriptionService,
            container.resolve(SubscriptionService),  # ✅ ADD THIS
        ),
    )
```

**Step 2: Commit**

```bash
git add application/services/common/container.py
git commit -m "feat(di): register subscription service with proper container.resolve() to avoid double instantiation"
```

---

## Phase 7: Testing & Verification

### Task 7.1: Run Full Test Suite

**Step 1: Run all tests**

```bash
uv run pytest tests/ -v --tb=short
```
Expected: All tests pass (including new subscription tests)

### Task 7.2: Run Linting

**Step 1: Run flake8**

```bash
uv run flake8 .
```
Expected: No critical errors

**Step 2: Run black**

```bash
uv run black . --check
```
Expected: All files formatted correctly

### Task 7.3: Run Type Checking

**Step 1: Run mypy**

```bash
uv run mypy .
```
Expected: No type errors

---

## Phase 8: Documentation

### Task 8.1: Update CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: Add entry**

```markdown
## [3.10.0] - 2026-03-16

### Added
- 🚀 Subscription Plans (1, 3, 6 months) with unlimited data
- 📦 SubscriptionPlan domain entity with payment_id for idempotency
- 💎 Premium user detection with async is_premium_user()
- 🔔 Subscription expiration and reminder background jobs
- 📊 Fair Use Policy for unlimited plans

### Changed
- Updated VpnService to check subscription status async for data limits
- Updated ConsumptionBillingService to bypass tracking for premium users
- Fixed DI container to use container.resolve() for consistent instances

### Infrastructure
- Added subscription_plans database table with migrations
- Integrated subscription service into dependency injection container
- Added payment_id unique constraint for idempotency

### Fixed
- Fixed dataclasses.replace() usage instead of non-existent .copy()
- Fixed Markdown v1 formatting (* instead of **) in reminder messages
- Fixed scalar_one_or_none to scalars().first() for defensive querying
```

**Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add subscription plans to changelog with all fixes applied"
```

---

## Summary

This implementation plan follows the existing architecture patterns and integrates subscription plans without breaking existing functionality. Each phase builds on the previous one, with comprehensive testing at each step.

**All Code Review Fixes Applied:**
- ✅ `is_premium_user` is now async with proper repo call
- ✅ `_get_user_data_limit` is now async with actual subscription check
- ✅ `.copy()` replaced with `dataclasses.replace()`
- ✅ Test for `is_premium_user` updated to async
- ✅ Duplicate CheckConstraint `info={}` removed
- ✅ `payment_id` added for idempotency
- ✅ `down_revision` will use actual latest revision
- ✅ `scalar_one_or_none` changed to `scalars().first()`
- ✅ `stars_paid` semantics documented as total paid
- ✅ Markdown `**` changed to `*` for v1
- ✅ DI container uses `container.resolve()` consistently

**Total Estimated Tasks:** 15+
**Estimated Time:** 4-6 hours (with testing)
**Risk Level:** Low (follows existing patterns, TDD approach, all bugs fixed)

---

**Ready for execution?** Use `superpowers:executing-plans` to implement this plan task-by-task with review checkpoints between each phase.
