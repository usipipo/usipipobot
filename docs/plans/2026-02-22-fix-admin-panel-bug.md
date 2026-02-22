# Fix Admin Panel Access Bug - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the bug that prevents admin users from accessing the admin panel when clicking the "🔧 Admin" button from the main menu.

**Architecture:** The fix requires aligning AdminService method calls with the repository interfaces, completing missing interface methods, and ensuring proper `current_user_id` parameter passing throughout the call chain.

**Tech Stack:** Python 3.11, SQLAlchemy Async, PostgreSQL, python-telegram-bot

**Related Issue:** #138 - Bug: Error al acceder al panel de administración desde el menú principal

---

## Root Cause Analysis Summary

1. **Method name mismatches**: AdminService calls non-existent methods on repositories
2. **Missing parameters**: `current_user_id` not passed to repository methods
3. **Incomplete interfaces**: ITransactionRepository missing `get_balance` and `get_transactions_by_type`
4. **Missing method**: IUserRepository missing `delete_user` method
5. **Type handling**: `key.key_type.lower()` fails when key_type is an Enum

---

### Task 1: Fix ITransactionRepository Interface

**Files:**
- Modify: `domain/interfaces/itransaction_repository.py`

**Step 1: Add missing methods to interface**

Add these methods to `ITransactionRepository`:

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Balance:
    stars: int = 0

class ITransactionRepository(ABC):
    @abstractmethod
    async def record_transaction(
        self,
        user_id: int,
        transaction_type: str,
        amount: int,
        balance_after: int,
        description: str,
        reference_id: Optional[str] = None,
        telegram_payment_id: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    async def get_user_transactions(self, user_id: int, limit: int = 10) -> list:
        pass

    @abstractmethod
    async def get_balance(self, user_id: int) -> Balance:
        """Get the balance for a user."""
        pass

    @abstractmethod
    async def get_transactions_by_type(self, transaction_type: str) -> List[Dict[str, Any]]:
        """Get all transactions of a specific type."""
        pass
```

**Step 2: Commit**

```bash
git add domain/interfaces/itransaction_repository.py
git commit -m "feat: add get_balance and get_transactions_by_type to ITransactionRepository"
```

---

### Task 2: Fix TransactionRepository Implementation

**Files:**
- Modify: `infrastructure/persistence/postgresql/transaction_repository.py`

**Step 1: Read current implementation**

Run: `cat infrastructure/persistence/postgresql/transaction_repository.py`

**Step 2: Add missing methods**

Add implementation for `get_balance` and `get_transactions_by_type`:

```python
from typing import List, Dict, Any
from domain.interfaces.itransaction_repository import ITransactionRepository, Balance

# In the class, add:

async def get_balance(self, user_id: int) -> Balance:
    """Get the balance for a user (returns 0 stars balance for now)."""
    return Balance(stars=0)

async def get_transactions_by_type(self, transaction_type: str) -> List[Dict[str, Any]]:
    """Get all transactions of a specific type."""
    try:
        from sqlalchemy import select
        from .models import TransactionModel
        
        query = select(TransactionModel).where(
            TransactionModel.transaction_type == transaction_type
        )
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "user_id": m.user_id,
                "transaction_type": m.transaction_type,
                "amount": m.amount,
                "description": m.description,
                "created_at": m.created_at,
            }
            for m in models
        ]
    except Exception as e:
        logger.error(f"Error getting transactions by type: {e}")
        return []
```

**Step 3: Commit**

```bash
git add infrastructure/persistence/postgresql/transaction_repository.py
git commit -m "feat: implement get_balance and get_transactions_by_type in TransactionRepository"
```

---

### Task 3: Fix IUserRepository Interface

**Files:**
- Modify: `domain/interfaces/iuser_repository.py`

**Step 1: Add delete_user method**

Add to `IUserRepository`:

```python
async def update_user(self, user: User, current_user_id: int) -> User:
    """Updates an existing user."""
    ...

async def delete_user(self, telegram_id: int, current_user_id: int) -> bool:
    """Deletes a user from the database."""
    ...
```

**Step 2: Commit**

```bash
git add domain/interfaces/iuser_repository.py
git commit -m "feat: add update_user and delete_user to IUserRepository"
```

---

### Task 4: Fix UserRepository Implementation

**Files:**
- Modify: `infrastructure/persistence/postgresql/user_repository.py`

**Step 1: Add update_user method**

Add after the `save` method:

```python
async def update_user(self, user: User, current_user_id: int) -> User:
    """Updates an existing user."""
    return await self.save(user, current_user_id)
```

**Step 2: Add delete_user method**

Add at the end of the class:

```python
async def delete_user(self, telegram_id: int, current_user_id: int) -> bool:
    """Deletes a user from the database."""
    await self._set_current_user(current_user_id)
    try:
        from sqlalchemy import delete
        query = delete(UserModel).where(UserModel.telegram_id == telegram_id)
        await self.session.execute(query)
        await self.session.commit()
        logger.info(f"Usuario {telegram_id} eliminado correctamente.")
        return True
    except Exception as e:
        await self.session.rollback()
        logger.error(f"Error al eliminar usuario {telegram_id}: {e}")
        return False
```

**Step 3: Commit**

```bash
git add infrastructure/persistence/postgresql/user_repository.py
git commit -m "feat: implement update_user and delete_user in UserRepository"
```

---

### Task 5: Fix AdminService - Method Names and Parameters (Part 1)

**Files:**
- Modify: `application/services/admin_service.py`

**Step 1: Fix get_user_keys method (line 144-150)**

Change from:
```python
async def get_user_keys(self, user_id: int) -> List[Key]:
    """Obtener todas las claves de un usuario específico."""
    try:
        return await self.key_repository.get_user_keys(user_id)
```

To:
```python
async def get_user_keys(self, user_id: int, current_user_id: int) -> List[Key]:
    """Obtener todas las claves de un usuario específico."""
    try:
        return await self.key_repository.get_by_user(user_id, current_user_id)
```

**Step 2: Fix delete_key_from_servers method (line 188-220)**

Change line 191 from:
```python
key = await self.key_repository.get_key(key_id)
```

To:
```python
key = await self.key_repository.get_by_id(key_id, admin_id or 0)
```

Add `admin_id` parameter to method signature and pass it through.

**Step 3: Fix delete_key_from_db method (line 222-234)**

Change line 225 from:
```python
result = await self.key_repository.delete_key(key_id)
```

To:
```python
result = await self.key_repository.delete(key_id, current_user_id or 0)
```

Add `current_user_id` parameter.

**Step 4: Commit**

```bash
git add application/services/admin_service.py
git commit -m "fix: correct repository method names in AdminService (part 1)"
```

---

### Task 6: Fix AdminService - Method Names and Parameters (Part 2)

**Files:**
- Modify: `application/services/admin_service.py`

**Step 1: Fix delete_user_key_complete method (line 235-279)**

Update to pass `current_user_id` to all repository calls:

```python
async def delete_user_key_complete(self, key_id: str, current_user_id: int = 0) -> Dict[str, Any]:
    """Eliminar completamente una clave (servidores + BD)."""
    try:
        key = await self.key_repository.get_by_id(key_id, current_user_id)
        if not key:
            return {
                "success": False,
                "server_deleted": False,
                "db_deleted": False,
                "error": "Clave no encontrada",
            }

        # Eliminar de servidores
        server_deleted = await self.delete_key_from_servers(key_id, key.key_type, current_user_id)

        # Eliminar de BD
        db_deleted = await self.delete_key_from_db(key_id, current_user_id)
        # ... rest of method
```

**Step 2: Fix get_key_usage_stats method (line 350-390)**

Change line 353:
```python
key = await self.key_repository.get_key(key_id)
```

To:
```python
key = await self.key_repository.get_by_id(key_id, current_user_id or 0)
```

**Step 3: Fix key_type handling (line 360)**

Change from:
```python
if key.key_type.lower() == "wireguard":
```

To:
```python
key_type_str = key.key_type.value if hasattr(key.key_type, 'value') else str(key.key_type)
if key_type_str.lower() == "wireguard":
```

Also fix line 371 similarly.

**Step 4: Commit**

```bash
git add application/services/admin_service.py
git commit -m "fix: correct repository method names in AdminService (part 2)"
```

---

### Task 7: Fix AdminService - User Management Methods

**Files:**
- Modify: `application/services/admin_service.py`

**Step 1: Fix get_user_by_id method (line 396-422)**

Add `current_user_id` parameter:

```python
async def get_user_by_id(self, user_id: int, current_user_id: int) -> Optional[Dict]:
    """Obtener información detallada de un usuario."""
    try:
        user = await self.user_repository.get_user(user_id, current_user_id)
        if not user:
            return None

        user_keys = await self.key_repository.get_by_user(user_id, current_user_id)
        active_keys = [k for k in user_keys if k.is_active]
        balance = await self.payment_repository.get_balance(user_id)
        # ... rest
```

**Step 2: Fix update_user_status method (line 424-466)**

Add `current_user_id` parameter and fix call:

```python
async def update_user_status(
    self, user_id: int, status: str, current_user_id: int
) -> AdminOperationResult:
    try:
        user = await self.user_repository.get_user(user_id, current_user_id)
        # ...
        await self.user_repository.update_user(user, current_user_id)
        # ...
```

**Step 3: Fix assign_role_to_user method (line 468-513)**

Add `current_user_id` parameter and fix calls.

**Step 4: Fix delete_user method (line 523-569)**

Add `current_user_id` parameter:

```python
async def delete_user(self, user_id: int, current_user_id: int) -> AdminOperationResult:
    try:
        user = await self.user_repository.get_user(user_id, current_user_id)
        # ...
        user_keys = await self.key_repository.get_by_user(user_id, current_user_id)
        # ...
        for key in user_keys:
            result = await self.delete_user_key_complete(str(key.id), current_user_id)
        # ...
        await self.user_repository.delete_user(user_id, current_user_id)
        # ...
```

**Step 5: Commit**

```bash
git add application/services/admin_service.py
git commit -m "fix: add current_user_id parameter to AdminService user methods"
```

---

### Task 8: Fix AdminService - get_users_paginated method

**Files:**
- Modify: `application/services/admin_service.py`

**Step 1: Fix get_users_paginated method (line 571-618)**

Change from:
```python
async def get_users_paginated(self, page: int = 1, per_page: int = 10) -> Dict:
    try:
        all_users = await self.user_repository.get_all_users()
```

To:
```python
async def get_users_paginated(self, page: int = 1, per_page: int = 10, current_user_id: int = 0) -> Dict:
    try:
        all_users = await self.user_repository.get_all_users(current_user_id)
        # ...
        for user in paginated_users:
            user_keys = await self.key_repository.get_by_user(user.telegram_id, current_user_id)
```

**Step 2: Commit**

```bash
git add application/services/admin_service.py
git commit -m "fix: add current_user_id to get_users_paginated in AdminService"
```

---

### Task 9: Fix AdminService - delete_key_from_servers signature

**Files:**
- Modify: `application/services/admin_service.py`

**Step 1: Update delete_key_from_servers to handle key_type enum properly**

```python
async def delete_key_from_servers(self, key_id: str, key_type, current_user_id: int = 0) -> bool:
    """Eliminar una clave de los servidores VPN (WireGuard y Outline)."""
    try:
        key = await self.key_repository.get_by_id(key_id, current_user_id)
        if not key:
            logger.error(f"Clave {key_id} no encontrada en BD")
            return False

        success = True
        key_type_str = key_type.value if hasattr(key_type, 'value') else str(key_type)

        if key_type_str.lower() == "wireguard":
            # Eliminar de WireGuard
            wg_result = await self.wireguard_client.delete_client(key.key_name)
            # ...

        elif key_type_str.lower() == "outline":
            # Eliminar de Outline
            outline_result = await self.outline_client.delete_key(key_id)
            # ...
```

**Step 2: Commit**

```bash
git add application/services/admin_service.py
git commit -m "fix: handle key_type enum properly in delete_key_from_servers"
```

---

### Task 10: Update AdminHandler to pass current_user_id

**Files:**
- Modify: `telegram_bot/features/admin/handlers_admin.py`

**Step 1: Verify handlers are passing admin_id correctly**

The handlers already pass `admin_id` as `current_user_id` to the service methods. Verify:
- `show_users` passes `admin_id` to `get_all_users`
- `show_keys` passes `admin_id` to `get_all_keys`
- `show_server_status` passes `admin_id` to `get_server_stats`

**Step 2: No changes needed if already correct**

The handlers already extract `admin_id = update.effective_user.id` and pass it to service methods.

**Step 3: Commit if changes were made**

```bash
git add telegram_bot/features/admin/handlers_admin.py
git commit -m "fix: ensure admin_id is passed as current_user_id in AdminHandler"
```

---

### Task 11: Run Tests and Verify Fix

**Step 1: Run existing tests**

```bash
./venv/bin/pytest tests/ -v --tb=short 2>&1 | head -100
```

**Step 2: Run the bot and test manually**

```bash
./venv/bin/python main.py
```

Then:
1. As admin user, send `/start` to the bot
2. Click "🔧 Admin" button
3. Verify admin menu appears
4. Click "👥 Usuarios" and verify users list appears
5. Click "🔑 Llaves VPN" and verify keys list appears

**Step 3: Check logs for errors**

```bash
tail -50 logs/errors.log
```

---

### Task 12: Final Commit and Push

**Step 1: Review all changes**

```bash
git diff develop --stat
git log --oneline -10
```

**Step 2: Push to origin**

```bash
git push origin develop
```

**Step 3: Close issue with comment**

```bash
gh issue close 138 --comment "Fixed in commit $(git rev-parse HEAD). The following changes were made:
- Added missing methods to ITransactionRepository (get_balance, get_transactions_by_type)
- Added update_user and delete_user methods to IUserRepository
- Fixed all method name mismatches in AdminService
- Added current_user_id parameter to all repository calls
- Fixed key_type enum handling"
```

---

## Summary of Changes

| File | Changes |
|------|---------|
| `domain/interfaces/itransaction_repository.py` | Added `get_balance`, `get_transactions_by_type` methods |
| `domain/interfaces/iuser_repository.py` | Added `update_user`, `delete_user` methods |
| `infrastructure/persistence/postgresql/transaction_repository.py` | Implemented missing methods |
| `infrastructure/persistence/postgresql/user_repository.py` | Implemented `update_user`, `delete_user` |
| `application/services/admin_service.py` | Fixed all method calls to match repository interfaces |
| `telegram_bot/features/admin/handlers_admin.py` | Verified current_user_id passing |

---

## Testing Checklist

- [ ] Admin panel accessible from main menu
- [ ] User list displays correctly
- [ ] Key list displays correctly
- [ ] Server status shows correctly
- [ ] No errors in logs when accessing admin features
- [ ] All existing tests pass
