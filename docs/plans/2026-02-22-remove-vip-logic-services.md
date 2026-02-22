# Remove VIP Logic from Services Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove all VIP-related logic from VpnService, PaymentService, and AdminService to complete the business model v2.0 refactoring.

**Architecture:** Clean removal of VIP checks and references. The `_get_user_data_limit()` method already returns FREE_PLAN_DATA_LIMIT_GB, so no VIP logic exists there. The critical fix is removing `user.is_vip` reference in AdminService that causes AttributeError since the field was removed from User entity.

**Tech Stack:** Python 3.x, pytest, async/await patterns

---

## Investigation Summary

### Current State
- `User` entity: VIP fields (`is_vip`, `vip_expires_at`) already removed
- `VpnService._get_user_data_limit()`: Already returns FREE_PLAN_DATA_LIMIT_GB (no VIP check)
- `PaymentService`: No `activate_vip()` method exists (already clean)
- `AdminService.get_users_paginated()`: **CRITICAL BUG** - references `user.is_vip` which no longer exists

### Files Affected
1. `application/services/admin_service.py:618` - Remove `is_vip` from user list dict
2. `config.py:203-212` - Remove VIP_PLAN_* settings (optional cleanup)
3. `telegram_bot/features/operations/messages_operations.py:24` - Remove VIP messages
4. `telegram_bot/features/operations/keyboards_operations.py:132-138` - Remove VIP upgrade options

---

### Task 1: Fix Critical Bug in AdminService

**Files:**
- Modify: `application/services/admin_service.py:618`

**Step 1: Locate and fix the is_vip reference**

Remove line 618 that references `user.is_vip`:

```python
# BEFORE (lines 611-624):
user_list.append(
    {
        "user_id": user.telegram_id,
        "username": user.username,
        "full_name": user.full_name,
        "status": user.status.value,
        "role": user.role.value,
        "is_vip": user.is_vip,  # REMOVE THIS LINE
        "total_keys": len(user_keys),
        "active_keys": len(active_keys),
        "balance_stars": balance.stars if balance else 0,
        "created_at": user.created_at.isoformat(),
    }
)

# AFTER:
user_list.append(
    {
        "user_id": user.telegram_id,
        "username": user.username,
        "full_name": user.full_name,
        "status": user.status.value,
        "role": user.role.value,
        "total_keys": len(user_keys),
        "active_keys": len(active_keys),
        "balance_stars": balance.stars if balance else 0,
        "created_at": user.created_at.isoformat(),
    }
)
```

**Step 2: Verify no other VIP references in services**

Run: `grep -rn "is_vip\|vip_expires_at" application/services/`
Expected: No matches

**Step 3: Commit**

```bash
git add application/services/admin_service.py
git commit -m "fix(admin): remove is_vip reference causing AttributeError"
```

---

### Task 2: Remove VIP Configuration Settings

**Files:**
- Modify: `config.py:203-212`

**Step 1: Remove VIP_PLAN_* settings**

Delete lines 203-212:
```python
# DELETE THESE LINES:
VIP_PLAN_MAX_KEYS: int = Field(
    default=10, ge=1, description="Máximo de llaves para el plan VIP"
)

VIP_PLAN_DATA_LIMIT_GB: int = Field(
    default=50, ge=1, description="Límite de datos por clave en GB para el plan VIP"
)

VIP_PLAN_COST_STARS: int = Field(
    default=10, ge=1, description="Costo en Telegram Stars por mes de VIP"
)
```

**Step 2: Verify no VIP references in config**

Run: `grep -in "vip" config.py`
Expected: No matches

**Step 3: Commit**

```bash
git add config.py
git commit -m "refactor(config): remove unused VIP plan settings"
```

---

### Task 3: Remove VIP UI Messages

**Files:**
- Modify: `telegram_bot/features/operations/messages_operations.py`

**Step 1: Find and remove VIP message reference**

Read the file around line 24 and remove any VIP-related message content.

**Step 2: Commit**

```bash
git add telegram_bot/features/operations/messages_operations.py
git commit -m "refactor(ui): remove VIP plan messages"
```

---

### Task 4: Remove VIP Keyboard Options

**Files:**
- Modify: `telegram_bot/features/operations/keyboards_operations.py`

**Step 1: Remove VIP upgrade action handling**

Remove lines around 132-138:
```python
# DELETE:
elif action == "vip_upgrade":
    # ... VIP upgrade keyboard code
```

**Step 2: Commit**

```bash
git add telegram_bot/features/operations/keyboards_operations.py
git commit -m "refactor(ui): remove VIP upgrade keyboard options"
```

---

### Task 5: Run Tests and Verify

**Step 1: Run all tests**

Run: `pytest -v`
Expected: All tests pass

**Step 2: Final grep for any remaining VIP references**

Run: `grep -rn "vip\|VIP" --include="*.py" application/ domain/ telegram_bot/ config.py | grep -v migrations | grep -v "__pycache__"`
Expected: No matches (except migration files which are expected)

**Step 3: Push changes**

```bash
git push origin develop
```

---

## Summary

| Task | File | Change |
|------|------|--------|
| 1 | `application/services/admin_service.py` | Remove `is_vip` from user dict |
| 2 | `config.py` | Remove VIP_PLAN_* settings |
| 3 | `telegram_bot/features/operations/messages_operations.py` | Remove VIP messages |
| 4 | `telegram_bot/features/operations/keyboards_operations.py` | Remove VIP keyboard options |
| 5 | Tests | Verify all pass |

## Risk Assessment

- **Critical Bug:** `admin_service.py:618` causes `AttributeError` when accessing `user.is_vip`
- **Low Risk:** Other changes are cleanup of unused code
- **No Breaking Changes:** VIP functionality is already non-operational
