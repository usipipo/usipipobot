# Fix UserModel Incomplete - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix TypeError when creating new users by completing UserModel with all missing fields

**Architecture:** Add missing fields to SQLAlchemy model, create migration, update repository methods

**Tech Stack:** Python 3.13, SQLAlchemy 2.x, Alembic, PostgreSQL

---

## Task 1: Create Migration for Missing User Fields

**Files:**
- Create: `migrations/versions/006_add_missing_user_fields.py`

**Step 1: Write the migration**

```python
"""
Add missing user fields: status, role, max_keys, balance_stars, etc.

Revision ID: 006_add_missing_user_fields
Revises: 005_add_transactions
Create Date: 2026-02-22 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '006_add_missing_user_fields'
down_revision: Union[str, None] = '005_add_transactions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums first
    op.execute("CREATE TYPE user_status_enum AS ENUM ('active', 'suspended', 'blocked', 'free_trial')")
    op.execute("CREATE TYPE user_role_enum AS ENUM ('user', 'admin', 'task_manager', 'announcer')")
    
    # Add missing columns to users table
    op.add_column('users', sa.Column('status', sa.String(), server_default='active', nullable=True))
    op.add_column('users', sa.Column('role', sa.String(), server_default='user', nullable=True))
    op.add_column('users', sa.Column('max_keys', sa.Integer(), server_default='2', nullable=True))
    op.add_column('users', sa.Column('balance_stars', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('total_deposited', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('referral_code', sa.String(), nullable=True))
    op.add_column('users', sa.Column('referred_by', sa.BigInteger(), nullable=True))
    op.add_column('users', sa.Column('total_referral_earnings', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('is_vip', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('users', sa.Column('vip_expires_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add index on referral_code for lookups
    op.create_index('ix_users_referral_code', 'users', ['referral_code'], unique=True)
    op.create_index('ix_users_referred_by', 'users', ['referred_by'])


def downgrade() -> None:
    op.drop_index('ix_users_referred_by', table_name='users')
    op.drop_index('ix_users_referral_code', table_name='users')
    op.drop_column('users', 'vip_expires_at')
    op.drop_column('users', 'is_vip')
    op.drop_column('users', 'total_referral_earnings')
    op.drop_column('users', 'referred_by')
    op.drop_column('users', 'referral_code')
    op.drop_column('users', 'total_deposited')
    op.drop_column('users', 'balance_stars')
    op.drop_column('users', 'max_keys')
    op.drop_column('users', 'role')
    op.drop_column('users', 'status')
    op.execute('DROP TYPE user_role_enum')
    op.execute('DROP TYPE user_status_enum')
```

**Step 2: Run migration**

Run: `./venv/bin/alembic upgrade head`
Expected: Migration successful

---

## Task 2: Update UserModel with Missing Fields

**Files:**
- Modify: `infrastructure/persistence/postgresql/models/base.py`

**Step 1: Update UserModel class**

Replace the `UserModel` class (lines 28-55) with:

```python
class UserModel(Base):
    """Modelo de usuarios del sistema."""

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Status and role
    status: Mapped[Optional[str]] = mapped_column(String, server_default="active")
    role: Mapped[Optional[str]] = mapped_column(String, server_default="user")
    max_keys: Mapped[int] = mapped_column(Integer, server_default="2")
    
    # Balance and deposits
    balance_stars: Mapped[int] = mapped_column(Integer, server_default="0")
    total_deposited: Mapped[int] = mapped_column(Integer, server_default="0")
    
    # Referral system
    referral_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_referral_earnings: Mapped[int] = mapped_column(Integer, server_default="0")
    
    # VIP status
    is_vip: Mapped[bool] = mapped_column(Boolean, server_default="false")
    vip_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Free data
    free_data_limit_bytes: Mapped[int] = mapped_column(
        BigInteger, server_default="10737418240"
    )
    free_data_used_bytes: Mapped[int] = mapped_column(BigInteger, server_default="0")

    keys: Mapped[List["VpnKeyModel"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    data_packages: Mapped[List["DataPackageModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
```

**Step 2: Verify no import issues**

Run: `./venv/bin/python -c "from infrastructure.persistence.postgresql.models import UserModel; print('OK')"`
Expected: `OK`

---

## Task 3: Update Repository Methods

**Files:**
- Modify: `infrastructure/persistence/postgresql/user_repository.py`

**Step 1: Update _model_to_entity method**

Replace the `_model_to_entity` method (lines 31-51) with:

```python
def _model_to_entity(self, model: UserModel) -> User:
    vip_expires = model.vip_expires_at
    if vip_expires is not None and vip_expires.tzinfo is None:
        vip_expires = vip_expires.replace(tzinfo=timezone.utc)

    return User(
        telegram_id=model.telegram_id,
        username=model.username,
        full_name=model.full_name,
        status=UserStatus(model.status) if model.status else UserStatus.ACTIVE,
        role=UserRole(model.role) if model.role else UserRole.USER,
        max_keys=model.max_keys or 2,
        balance_stars=model.balance_stars or 0,
        total_deposited=model.total_deposited or 0,
        referral_code=model.referral_code,
        referred_by=model.referred_by,
        total_referral_earnings=model.total_referral_earnings or 0,
        is_vip=model.is_vip or False,
        vip_expires_at=vip_expires,
        free_data_limit_bytes=model.free_data_limit_bytes or 10 * 1024**3,
        free_data_used_bytes=model.free_data_used_bytes or 0,
    )
```

**Step 2: Add UserRole import**

Add to imports (line 15):
```python
from domain.entities.user import User, UserStatus, UserRole
```

---

## Task 4: Run Tests and Verify

**Step 1: Run existing tests**

Run: `./venv/bin/pytest tests/ -v --asyncio-mode=auto`
Expected: All tests pass

**Step 2: Run migration**

Run: `./venv/bin/alembic upgrade head`
Expected: Migration successful

**Step 3: Test bot startup**

Run: `./venv/bin/python main.py` (cancel with Ctrl+C after confirming no errors)
Expected: No TypeError

---

## Task 5: Commit and Push

**Step 1: Stage changes**

```bash
git add infrastructure/persistence/postgresql/models/base.py
git add infrastructure/persistence/postgresql/user_repository.py
git add migrations/versions/006_add_missing_user_fields.py
```

**Step 2: Commit**

```bash
git commit -m "fix: complete UserModel with missing fields

- Add status, role, max_keys, balance_stars, total_deposited fields
- Add referral_code, referred_by, total_referral_earnings fields  
- Add is_vip, vip_expires_at fields
- Create migration 006_add_missing_user_fields
- Update _model_to_entity to handle all fields

Fixes #110"
```

**Step 3: Push branch**

```bash
git push -u origin fix/issue-110-usermodel-incomplete
```
