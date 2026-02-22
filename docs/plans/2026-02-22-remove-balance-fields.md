# Eliminar balance_stars y total_deposited - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminar los campos `balance_stars` y `total_deposited` del sistema, cambiando a un modelo de pagos directos sin balance acumulativo.

**Architecture:** Se eliminarán los campos de todas las capas (domain, infrastructure, application, interface) y se refactorizará PaymentService para registrar transacciones sin mantener balance. Los métodos `can_delete_keys` se actualizarán para usar `referral_credits` o paquetes comprados.

**Tech Stack:** Python, SQLAlchemy, Alembic, pytest

---

## Archivos Afectados

| Archivo | Cambio |
|---------|--------|
| `domain/entities/user.py` | Eliminar campos `balance_stars`, `total_deposited` y método `can_delete_keys` |
| `infrastructure/persistence/postgresql/models/base.py` | Eliminar columnas del modelo |
| `infrastructure/persistence/postgresql/user_repository.py` | Eliminar mapeo de campos |
| `application/services/payment_service.py` | Refactorizar para pagos directos |
| `application/services/admin_service.py` | Eliminar referencias |
| `telegram_bot/features/user_management/handlers_user_management.py` | Actualizar mensajes |
| `telegram_bot/features/payments/handlers_payments.py` | Simplificar handlers |
| `telegram_bot/features/operations/handlers_operations.py` | Eliminar referencias |
| `telegram_bot/features/operations/messages_operations.py` | Actualizar mensajes |
| `telegram_bot/features/admin/messages_admin.py` | Actualizar mensajes |
| `telegram_bot/features/payments/messages_payments.py` | Actualizar mensajes |
| `domain/entities/admin.py` | Eliminar campo `total_deposited` |
| `tests/conftest.py` | Actualizar fixtures |
| `tests/application/services/test_payment_service.py` | Actualizar tests |
| `tests/application/services/test_vpn_service.py` | Actualizar tests |
| `migrations/versions/009_remove_balance_fields.py` | Nueva migración |

---

## Task 1: Actualizar Entity User

**Files:**
- Modify: `domain/entities/user.py:38-39, 79`

**Step 1: Eliminar campos del entity**

```python
# ELIMINAR estas líneas (38-39):
balance_stars: int = 0
total_deposited: int = 0
```

**Step 2: Actualizar método can_delete_keys**

```python
# Reemplazar método can_delete_keys (líneas 71-79):
def can_delete_keys(self) -> bool:
    """
    Lógica de negocio: Usuarios con paquetes comprados pueden eliminar claves.
    Los administradores pueden eliminar sin restricciones.
    """
    if self.role == UserRole.ADMIN:
        return True
    return self.referral_credits > 0
```

**Step 3: Ejecutar test para verificar**

Run: `./venv/bin/pytest tests/domain/ -v 2>/dev/null || echo "Tests domain not found"`
Expected: PASS o no errors en entity

---

## Task 2: Actualizar UserModel

**Files:**
- Modify: `infrastructure/persistence/postgresql/models/base.py:49-50`

**Step 1: Eliminar columnas del modelo**

```python
# ELIMINAR estas líneas (49-50):
balance_stars: Mapped[int] = mapped_column(Integer, server_default="0")
total_deposited: Mapped[int] = mapped_column(Integer, server_default="0")
```

---

## Task 3: Actualizar UserRepository

**Files:**
- Modify: `infrastructure/persistence/postgresql/user_repository.py:39-40, 64-65, 105-106, 170-186`

**Step 1: Eliminar campos de _model_to_entity**

```python
# Eliminar líneas 39-40:
balance_stars=model.balance_stars or 0,
total_deposited=model.total_deposited or 0,
```

**Step 2: Eliminar campos de _entity_to_model**

```python
# Eliminar líneas 64-65:
balance_stars=entity.balance_stars,
total_deposited=entity.total_deposited,
```

**Step 3: Eliminar campos de save()**

```python
# Eliminar líneas 105-106:
existing.balance_stars = user.balance_stars
existing.total_deposited = user.total_deposited
```

**Step 4: Eliminar método update_balance**

Eliminar completamente el método `update_balance` (líneas 170-186).

---

## Task 4: Refactorizar PaymentService

**Files:**
- Modify: `application/services/payment_service.py`

**Step 1: Simplificar update_balance**

```python
async def update_balance(
    self,
    telegram_id: int,
    amount: int,
    transaction_type: str,
    description: str,
    reference_id: Optional[str] = None,
    telegram_payment_id: Optional[str] = None,
    current_user_id: Optional[int] = None,
) -> bool:
    """Registra transacción sin mantener balance acumulativo."""
    try:
        uid = current_user_id or telegram_id
        user = await self.user_repo.get_by_id(telegram_id, uid)
        if not user:
            raise Exception("Usuario no encontrado")

        await self.transaction_repo.record_transaction(
            user_id=telegram_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=0,
            description=description,
            reference_id=reference_id,
            telegram_payment_id=telegram_payment_id,
        )

        logger.info(f"💰 Transaction recorded for user {telegram_id}: {amount} stars")
        return True

    except Exception as e:
        logger.error(f"Error recording transaction: {e}")
        return False
```

**Step 2: Simplificar get_user_balance**

```python
async def get_user_balance(self, telegram_id: int) -> Optional[int]:
    """Obtiene el total de transacciones positivas del usuario."""
    try:
        transactions = await self.transaction_repo.get_user_transactions(telegram_id)
        total = sum(t.get("amount", 0) for t in transactions if t.get("amount", 0) > 0)
        return total
    except Exception as e:
        logger.error(f"Error getting user balance: {e}")
        return None
```

**Step 3: Eliminar método deduct_balance**

Eliminar completamente el método `deduct_balance` (líneas 106-138).

---

## Task 5: Actualizar AdminService

**Files:**
- Modify: `application/services/admin_service.py:57, 111, 153, 439-440, 620`

**Step 1: Eliminar total_deposited de get_dashboard_stats**

```python
# Línea 57: Eliminar o comentar
# total_deposited_sum = sum(getattr(u, "total_deposited", 0) or 0 for u in users)

# Línea 111: Cambiar por 0
"total_deposited": 0,  # Eliminado del modelo
```

**Step 2: Eliminar total_deposited de get_all_users**

```python
# Línea 153: Cambiar por referral_credits
"total_deposited": getattr(user, "referral_credits", 0) or 0,
```

**Step 3: Eliminar balance_stars y total_deposited de get_user_by_id**

```python
# Líneas 439-440: Eliminar o cambiar
"balance_stars": 0,  # Eliminado del modelo
"total_deposited": getattr(user, "referral_credits", 0) or 0,
```

**Step 4: Eliminar balance_stars de get_users_paginated**

```python
# Línea 620: Cambiar por referral_credits
"balance_stars": getattr(user, "referral_credits", 0) or 0,
```

---

## Task 6: Actualizar Handlers de Usuario

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py:287-290`

**Step 1: Actualizar info_handler**

```python
# Líneas 287-290: Cambiar por referral_credits
data_used = f"{status_data.get('total_used_gb', 0):.2f} GB"
credits = user_entity.referral_credits
plan = "Premium" if credits > 0 else "Gratis"
```

**Step 2: Actualizar mensaje**

Buscar y actualizar `balance` por `credits` en el mensaje formateado.

---

## Task 7: Actualizar Admin Entity

**Files:**
- Modify: `domain/entities/admin.py:24`

**Step 1: Eliminar campo total_deposited**

```python
# Eliminar línea 24:
total_deposited: int
```

---

## Task 8: Crear Migración

**Files:**
- Create: `migrations/versions/009_remove_balance_fields.py`

**Step 1: Crear migración**

```python
"""
Remove balance_stars and total_deposited columns

Revision ID: 009_remove_balance_fields
Revises: 008_business_model_v2
Create Date: 2026-02-22 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '009_remove_balance_fields'
down_revision: Union[str, None] = '008_business_model_v2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('users', 'balance_stars')
    op.drop_column('users', 'total_deposited')


def downgrade() -> None:
    op.add_column('users', sa.Column('balance_stars', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('total_deposited', sa.Integer(), server_default='0', nullable=True))
```

---

## Task 9: Actualizar Tests

**Files:**
- Modify: `tests/conftest.py:89-90`
- Modify: `tests/application/services/test_payment_service.py`
- Modify: `tests/application/services/test_vpn_service.py:123, 141`

**Step 1: Actualizar fixture sample_user**

```python
# Eliminar líneas 89-90:
balance_stars=100,
total_deposited=50,
```

**Step 2: Actualizar test_payment_service.py**

Eliminar o modificar tests que usan `balance_stars`:

```python
# Eliminar tests que verifican balance_stars
# Modificar para usar referral_credits donde aplique
```

**Step 3: Actualizar test_vpn_service.py**

```python
# Líneas 123, 141: Cambiar total_deposited por referral_credits
sample_user.referral_credits = 100  # en lugar de total_deposited
```

---

## Task 10: Actualizar Mensajes

**Files:**
- Modify: `telegram_bot/features/operations/messages_operations.py:39`
- Modify: `telegram_bot/features/admin/messages_admin.py:49`
- Modify: `telegram_bot/features/payments/messages_payments.py:173`

**Step 1: Eliminar referencias a total_deposited en mensajes**

Buscar y eliminar o reemplazar `{total_deposited}` por `{credits}` en los mensajes.

---

## Task 11: Ejecutar Migración

**Step 1: Verificar estado actual**

Run: `./venv/bin/alembic current`
Expected: `008_business_model_v2 (head)`

**Step 2: Ejecutar migración**

Run: `./venv/bin/alembic upgrade head`
Expected: `009_remove_balance_fields (head)`

---

## Task 12: Ejecutar Tests

**Step 1: Ejecutar todos los tests**

Run: `./venv/bin/pytest -v --tb=short`
Expected: PASS (puede haber failures que requieran ajustes)

**Step 2: Corregir failures**

Si hay failures, revisar y corregir según el error específico.

---

## Commit Final

```bash
git add -A
git commit -m "refactor: eliminar balance_stars y total_deposited

- Eliminar campos balance_stars y total_deposited de User entity
- Eliminar columnas de UserModel
- Refactorizar PaymentService para pagos directos
- Actualizar AdminService
- Actualizar handlers y mensajes
- Actualizar tests
- Crear migración 009_remove_balance_fields

Closes #119"
```
