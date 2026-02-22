# ReferralService Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the ReferralService for managing referral credits system.

**Architecture:** Create a new service layer component (ReferralService) that handles referral registration, credit redemption, and integration with existing PaymentService and user registration flow.

**Tech Stack:** Python 3.13, SQLAlchemy Async, Pydantic, Telegram Bot API

---

## Overview

Based on issue #121 and the Business Model v2.0 design document, this implementation adds:
1. ReferralService with credit logic
2. Configuration settings for referral credits
3. Repository method for updating referral credits
4. Integration with user registration

## Task 1: Add Referral Configuration to Settings

**Files:**
- Modify: `config.py:203-209` (add referral settings)

**Step 1: Add referral configuration fields**

Add after `REFERRAL_COMMISSION_PERCENT`:

```python
    REFERRAL_CREDITS_PER_REFERRAL: int = Field(
        default=100,
        ge=0,
        description="Créditos otorgados por cada referido exitoso",
    )

    REFERRAL_BONUS_NEW_USER: int = Field(
        default=50,
        ge=0,
        description="Créditos de bienvenida para nuevo usuario referido",
    )

    REFERRAL_CREDITS_PER_GB: int = Field(
        default=100,
        ge=1,
        description="Créditos necesarios para canjear 1 GB de datos",
    )

    REFERRAL_CREDITS_PER_SLOT: int = Field(
        default=500,
        ge=1,
        description="Créditos necesarios para canjear +1 slot de clave",
    )
```

**Step 2: Run tests to verify**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

**Step 3: Commit**

```bash
git add config.py
git commit -m "feat: add referral credits configuration settings"
```

---

## Task 2: Add Repository Method for Credits Update

**Files:**
- Modify: `infrastructure/persistence/postgresql/user_repository.py:230` (add method)
- Modify: `domain/interfaces/iuser_repository.py:60` (add interface method)

**Step 1: Add interface method to IUserRepository**

Add at the end of `domain/interfaces/iuser_repository.py`:

```python
    async def update_referral_credits(
        self, telegram_id: int, credits_delta: int, current_user_id: int
    ) -> bool:
        """Actualiza los créditos de referido de un usuario."""
        ...

    async def increment_max_keys(
        self, telegram_id: int, slots: int, current_user_id: int
    ) -> bool:
        """Incrementa el límite de claves de un usuario."""
        ...
```

**Step 2: Add implementation to PostgresUserRepository**

Add at the end of `infrastructure/persistence/postgresql/user_repository.py`:

```python
    async def update_referral_credits(
        self, telegram_id: int, credits_delta: int, current_user_id: int
    ) -> bool:
        """Actualiza los créditos de referido de un usuario."""
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(
                    referral_credits=UserModel.referral_credits + credits_delta
                )
            )
            await self.session.execute(query)
            await self.session.commit()
            logger.debug(
                f"Créditos actualizados para usuario {telegram_id}: {credits_delta:+d}"
            )
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al actualizar créditos de referido: {e}")
            return False

    async def increment_max_keys(
        self, telegram_id: int, slots: int, current_user_id: int
    ) -> bool:
        """Incrementa el límite de claves de un usuario."""
        await self._set_current_user(current_user_id)
        try:
            query = (
                update(UserModel)
                .where(UserModel.telegram_id == telegram_id)
                .values(max_keys=UserModel.max_keys + slots)
            )
            await self.session.execute(query)
            await self.session.commit()
            logger.debug(
                f"Límite de claves incrementado para usuario {telegram_id}: +{slots}"
            )
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al incrementar límite de claves: {e}")
            return False
```

**Step 3: Run tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

**Step 4: Commit**

```bash
git add domain/interfaces/iuser_repository.py infrastructure/persistence/postgresql/user_repository.py
git commit -m "feat: add update_referral_credits and increment_max_keys to repository"
```

---

## Task 3: Create ReferralService

**Files:**
- Create: `application/services/referral_service.py`
- Create: `tests/application/services/test_referral_service.py`

**Step 1: Create ReferralService**

Create file `application/services/referral_service.py`:

```python
"""
Servicio de gestión de referidos y créditos.

Author: uSipipo Team
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from config import settings
from domain.entities.user import User
from domain.interfaces.itransaction_repository import ITransactionRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


@dataclass
class ReferralStats:
    """Estadísticas de referidos de un usuario."""
    referral_code: str
    total_referrals: int
    referral_credits: int
    referred_by: Optional[int]


class ReferralService:
    """
    Servicio para gestión del sistema de referidos.
    
    Maneja el registro de referidos, créditos y canjes.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        transaction_repo: ITransactionRepository,
    ):
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo

    async def register_referral(
        self,
        new_user_id: int,
        referral_code: str,
        current_user_id: int,
    ) -> Dict[str, Any]:
        """
        Registra un nuevo referido y otorga créditos.
        
        Args:
            new_user_id: ID del nuevo usuario
            referral_code: Código de referido
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            referrer = await self.user_repo.get_by_referral_code(
                referral_code, current_user_id
            )
            
            if not referrer:
                logger.warning(f"Código de referido no encontrado: {referral_code}")
                return {"success": False, "error": "invalid_code"}
            
            if referrer.telegram_id == new_user_id:
                logger.warning(f"Usuario intentó usarse a sí mismo como referidor")
                return {"success": False, "error": "self_referral"}
            
            new_user = await self.user_repo.get_by_id(new_user_id, current_user_id)
            if not new_user:
                return {"success": False, "error": "user_not_found"}
            
            if new_user.referred_by is not None:
                logger.info(f"Usuario {new_user_id} ya tiene referidor")
                return {"success": False, "error": "already_referred"}
            
            credits_for_referrer = settings.REFERRAL_CREDITS_PER_REFERRAL
            credits_for_new_user = settings.REFERRAL_BONUS_NEW_USER
            
            new_user.referred_by = referrer.telegram_id
            await self.user_repo.save(new_user, current_user_id)
            
            await self.user_repo.update_referral_credits(
                referrer.telegram_id, credits_for_referrer, current_user_id
            )
            
            await self.user_repo.update_referral_credits(
                new_user_id, credits_for_new_user, current_user_id
            )
            
            await self.transaction_repo.record_transaction(
                user_id=referrer.telegram_id,
                transaction_type="referral_bonus",
                amount=credits_for_referrer,
                balance_after=referrer.referral_credits + credits_for_referrer,
                description=f"Créditos por referido: nuevo usuario {new_user_id}",
                reference_id=f"ref_{new_user_id}_{referrer.telegram_id}",
            )
            
            logger.info(
                f"🎉 Referido registrado: {referrer.telegram_id} -> {new_user_id} "
                f"(+{credits_for_referrer} créditos)"
            )
            
            return {
                "success": True,
                "referrer_id": referrer.telegram_id,
                "credits_to_referrer": credits_for_referrer,
                "credits_to_new_user": credits_for_new_user,
            }
            
        except Exception as e:
            logger.error(f"Error registrando referido: {e}")
            return {"success": False, "error": str(e)}

    async def get_referral_stats(
        self, user_id: int, current_user_id: int
    ) -> ReferralStats:
        """
        Obtiene las estadísticas de referidos de un usuario.
        
        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            ReferralStats con estadísticas
        """
        user = await self.user_repo.get_by_id(user_id, current_user_id)
        if not user:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        referrals = await self.user_repo.get_referrals_by_user(user_id, current_user_id)
        
        return ReferralStats(
            referral_code=user.referral_code or "",
            total_referrals=len(referrals),
            referral_credits=user.referral_credits,
            referred_by=user.referred_by,
        )

    async def redeem_credits_for_data(
        self, user_id: int, credits: int, current_user_id: int
    ) -> Dict[str, Any]:
        """
        Canjea créditos por datos adicionales.
        
        Args:
            user_id: ID del usuario
            credits: Cantidad de créditos a canjear
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            Dict con resultado del canje
        """
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                return {"success": False, "error": "user_not_found"}
            
            if user.referral_credits < credits:
                return {"success": False, "error": "insufficient_credits"}
            
            credits_per_gb = settings.REFERRAL_CREDITS_PER_GB
            gb_to_add = credits // credits_per_gb
            
            if gb_to_add < 1:
                return {
                    "success": False,
                    "error": "insufficient_credits_for_gb",
                    "required": credits_per_gb,
                }
            
            actual_credits = gb_to_add * credits_per_gb
            
            await self.user_repo.update_referral_credits(
                user_id, -actual_credits, current_user_id
            )
            
            user.free_data_limit_bytes += gb_to_add * (1024**3)
            await self.user_repo.save(user, current_user_id)
            
            await self.transaction_repo.record_transaction(
                user_id=user_id,
                transaction_type="credit_redemption_data",
                amount=-actual_credits,
                balance_after=user.referral_credits - actual_credits,
                description=f"Canje de créditos: +{gb_to_add}GB",
                reference_id=f"redeem_data_{user_id}",
            )
            
            logger.info(
                f"💳 Créditos canjeados por datos: user {user_id}, "
                f"-{actual_credits} créditos, +{gb_to_add}GB"
            )
            
            return {
                "success": True,
                "credits_spent": actual_credits,
                "gb_added": gb_to_add,
                "remaining_credits": user.referral_credits - actual_credits,
            }
            
        except Exception as e:
            logger.error(f"Error canjeando créditos por datos: {e}")
            return {"success": False, "error": str(e)}

    async def redeem_credits_for_slot(
        self, user_id: int, current_user_id: int
    ) -> Dict[str, Any]:
        """
        Canjea créditos por un slot de clave adicional.
        
        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario que ejecuta la acción
            
        Returns:
            Dict con resultado del canje
        """
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                return {"success": False, "error": "user_not_found"}
            
            credits_per_slot = settings.REFERRAL_CREDITS_PER_SLOT
            
            if user.referral_credits < credits_per_slot:
                return {
                    "success": False,
                    "error": "insufficient_credits",
                    "required": credits_per_slot,
                    "current": user.referral_credits,
                }
            
            await self.user_repo.update_referral_credits(
                user_id, -credits_per_slot, current_user_id
            )
            
            await self.user_repo.increment_max_keys(user_id, 1, current_user_id)
            
            await self.transaction_repo.record_transaction(
                user_id=user_id,
                transaction_type="credit_redemption_slot",
                amount=-credits_per_slot,
                balance_after=user.referral_credits - credits_per_slot,
                description="Canje de créditos: +1 slot de clave",
                reference_id=f"redeem_slot_{user_id}",
            )
            
            logger.info(
                f"💳 Créditos canjeados por slot: user {user_id}, "
                f"-{credits_per_slot} créditos, +1 slot"
            )
            
            return {
                "success": True,
                "credits_spent": credits_per_slot,
                "slots_added": 1,
                "remaining_credits": user.referral_credits - credits_per_slot,
            }
            
        except Exception as e:
            logger.error(f"Error canjeando créditos por slot: {e}")
            return {"success": False, "error": str(e)}
```

**Step 2: Run linting**

Run: `python -m py_compile application/services/referral_service.py`
Expected: No errors

**Step 3: Commit**

```bash
git add application/services/referral_service.py
git commit -m "feat: create ReferralService for referral credits management"
```

---

## Task 4: Create Tests for ReferralService

**Files:**
- Create: `tests/application/services/test_referral_service.py`

**Step 1: Create test file**

Create file `tests/application/services/test_referral_service.py`:

```python
"""
Tests para ReferralService.

Author: uSipipo Team
Version: 1.0.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from application.services.referral_service import ReferralService, ReferralStats
from domain.entities.user import User


class TestRegisterReferral:
    """Tests para register_referral."""

    @pytest.fixture
    def service(self, mock_user_repo, mock_transaction_repo):
        return ReferralService(
            user_repo=mock_user_repo,
            transaction_repo=mock_transaction_repo,
        )

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_referral_code = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.save = AsyncMock()
        repo.update_referral_credits = AsyncMock(return_value=True)
        repo.get_referrals_by_user = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        repo = AsyncMock()
        repo.record_transaction = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_register_referral_success(
        self, service, mock_user_repo, mock_transaction_repo
    ):
        referrer = User(
            telegram_id=123,
            referral_code="ABC123",
            referral_credits=0,
        )
        new_user = User(
            telegram_id=456,
            referral_code="DEF456",
            referral_credits=0,
            referred_by=None,
        )

        mock_user_repo.get_by_referral_code.return_value = referrer
        mock_user_repo.get_by_id.return_value = new_user

        result = await service.register_referral(456, "ABC123", 123)

        assert result["success"] is True
        assert result["referrer_id"] == 123
        mock_user_repo.update_referral_credits.assert_called()
        mock_transaction_repo.record_transaction.assert_called()

    @pytest.mark.asyncio
    async def test_register_referral_invalid_code(
        self, service, mock_user_repo
    ):
        mock_user_repo.get_by_referral_code.return_value = None

        result = await service.register_referral(456, "INVALID", 123)

        assert result["success"] is False
        assert result["error"] == "invalid_code"

    @pytest.mark.asyncio
    async def test_register_referral_self_referral(
        self, service, mock_user_repo
    ):
        referrer = User(
            telegram_id=123,
            referral_code="ABC123",
        )
        mock_user_repo.get_by_referral_code.return_value = referrer

        result = await service.register_referral(123, "ABC123", 123)

        assert result["success"] is False
        assert result["error"] == "self_referral"

    @pytest.mark.asyncio
    async def test_register_referral_already_referred(
        self, service, mock_user_repo
    ):
        referrer = User(
            telegram_id=123,
            referral_code="ABC123",
        )
        new_user = User(
            telegram_id=456,
            referral_code="DEF456",
            referred_by=999,
        )

        mock_user_repo.get_by_referral_code.return_value = referrer
        mock_user_repo.get_by_id.return_value = new_user

        result = await service.register_referral(456, "ABC123", 123)

        assert result["success"] is False
        assert result["error"] == "already_referred"


class TestGetReferralStats:
    """Tests para get_referral_stats."""

    @pytest.fixture
    def service(self, mock_user_repo, mock_transaction_repo):
        return ReferralService(
            user_repo=mock_user_repo,
            transaction_repo=mock_transaction_repo,
        )

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_referrals_by_user = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_referral_stats_success(
        self, service, mock_user_repo
    ):
        user = User(
            telegram_id=123,
            referral_code="ABC123",
            referral_credits=200,
            referred_by=None,
        )
        mock_user_repo.get_by_id.return_value = user

        stats = await service.get_referral_stats(123, 123)

        assert stats.referral_code == "ABC123"
        assert stats.referral_credits == 200
        assert stats.total_referrals == 0

    @pytest.mark.asyncio
    async def test_get_referral_stats_user_not_found(
        self, service, mock_user_repo
    ):
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Usuario no encontrado"):
            await service.get_referral_stats(999, 999)


class TestRedeemCreditsForData:
    """Tests para redeem_credits_for_data."""

    @pytest.fixture
    def service(self, mock_user_repo, mock_transaction_repo):
        return ReferralService(
            user_repo=mock_user_repo,
            transaction_repo=mock_transaction_repo,
        )

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.save = AsyncMock()
        repo.update_referral_credits = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        repo = AsyncMock()
        repo.record_transaction = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_redeem_credits_for_data_success(
        self, service, mock_user_repo, mock_transaction_repo
    ):
        user = User(
            telegram_id=123,
            referral_credits=250,
            free_data_limit_bytes=10 * 1024**3,
        )
        mock_user_repo.get_by_id.return_value = user

        result = await service.redeem_credits_for_data(123, 200, 123)

        assert result["success"] is True
        assert result["gb_added"] == 2
        assert result["credits_spent"] == 200

    @pytest.mark.asyncio
    async def test_redeem_credits_insufficient(
        self, service, mock_user_repo
    ):
        user = User(
            telegram_id=123,
            referral_credits=50,
        )
        mock_user_repo.get_by_id.return_value = user

        result = await service.redeem_credits_for_data(123, 200, 123)

        assert result["success"] is False
        assert result["error"] == "insufficient_credits"


class TestRedeemCreditsForSlot:
    """Tests para redeem_credits_for_slot."""

    @pytest.fixture
    def service(self, mock_user_repo, mock_transaction_repo):
        return ReferralService(
            user_repo=mock_user_repo,
            transaction_repo=mock_transaction_repo,
        )

    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.update_referral_credits = AsyncMock(return_value=True)
        repo.increment_max_keys = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_transaction_repo(self):
        repo = AsyncMock()
        repo.record_transaction = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_redeem_credits_for_slot_success(
        self, service, mock_user_repo, mock_transaction_repo
    ):
        user = User(
            telegram_id=123,
            referral_credits=600,
            max_keys=2,
        )
        mock_user_repo.get_by_id.return_value = user

        result = await service.redeem_credits_for_slot(123, 123)

        assert result["success"] is True
        assert result["slots_added"] == 1
        assert result["credits_spent"] == 500

    @pytest.mark.asyncio
    async def test_redeem_credits_for_slot_insufficient(
        self, service, mock_user_repo
    ):
        user = User(
            telegram_id=123,
            referral_credits=100,
        )
        mock_user_repo.get_by_id.return_value = user

        result = await service.redeem_credits_for_slot(123, 123)

        assert result["success"] is False
        assert result["error"] == "insufficient_credits"
```

**Step 2: Run tests**

Run: `pytest tests/application/services/test_referral_service.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/application/services/test_referral_service.py
git commit -m "test: add tests for ReferralService"
```

---

## Task 5: Register ReferralService in Container

**Files:**
- Modify: `application/services/common/container.py`

**Step 1: Add ReferralService to container**

Find and modify the container registration file to include ReferralService.

**Step 2: Run tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

**Step 3: Commit**

```bash
git add application/services/common/container.py
git commit -m "feat: register ReferralService in dependency container"
```

---

## Task 6: Run Full Test Suite and Final Verification

**Step 1: Run all tests**

Run: `pytest tests/ -v --cov=application/services/referral_service`
Expected: All tests pass with coverage

**Step 2: Run linting**

Run: `python -m py_compile application/services/referral_service.py && python -m py_compile config.py`
Expected: No errors

**Step 3: Final commit if needed**

```bash
git status
git add -A
git commit -m "feat: complete ReferralService implementation (issue #121)"
```

---

## Summary

This plan implements issue #121 - Sistema de créditos por referidos:

1. **Configuration**: Adds referral credit settings to `config.py`
2. **Repository**: Adds `update_referral_credits()` and `increment_max_keys()` methods
3. **Service**: Creates `ReferralService` with:
   - `register_referral()`: Registers new referrals and awards credits
   - `get_referral_stats()`: Returns referral statistics
   - `redeem_credits_for_data()`: Exchanges credits for GB
   - `redeem_credits_for_slot()`: Exchanges credits for key slots
4. **Tests**: Comprehensive test coverage for all service methods

The next issue (#123) will implement the UI/handlers for the `/referir` command.
