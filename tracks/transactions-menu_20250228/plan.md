# Implementation Plan: Menu Operaciones + Historial Transacciones

Track ID: `transactions-menu_20250228`
Created: 2025-02-28
Status: pending

---

## Overview

Implementar rediseño del menú de operaciones y agregar funcionalidad de historial de transacciones crypto para el bot uSipipo VPN.

## Architecture

- **Fase 1**: Actualizar teclados y mensajes del menú de operaciones
- **Fase 2**: Implementar servicio de historial de transacciones
- **Fase 3**: Implementar handlers para visualización
- **Fase 4**: Tests y finalización

---

## Phase 1: Actualizar Menú de Operaciones

### Task 1.1: Actualizar OperationsKeyboards.operations_menu()

**Files:**
- Modify: `telegram_bot/features/operations/keyboards_operations.py:11-30`

**Changes:**
- Mejorar layout visual con secciones claras
- Preparar espacio para nuevo botón de historial

```python
# Nuevo layout del menú
keyboard = [
    # Sección de Beneficios
    [
        InlineKeyboardButton(f"🎁 Créditos ({credits})", callback_data="credits_menu"),
        InlineKeyboardButton("👥 Referidos", callback_data="referral_menu"),
    ],
    # Sección de Compras
    [
        InlineKeyboardButton("🛒 Shop", callback_data="shop_menu"),
        InlineKeyboardButton("📜 Historial", callback_data="transactions_history"),
    ],
    # Volver
    [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
]
```

### Task 1.2: Actualizar mensajes del menú

**Files:**
- Modify: `telegram_bot/features/operations/messages_operations.py:12-20`

**Changes:**
- Actualizar mensaje MAIN para reflejar nuevo diseño

```python
MAIN = (
    "⚙️ **Operaciones**\n\n"
    "Gestiona tu cuenta y servicios:\n\n"
    "🎁 **Créditos** - Canjea por beneficios\n"
    "👥 **Referidos** - Invita y gana\n"
    "🛒 **Shop** - Compra paquetes\n"
    "📜 **Historial** - Tus transacciones\n\n"
    "Selecciona una opción:"
)
```

### Task 1.3: Agregar teclado de historial de transacciones

**Files:**
- Modify: `telegram_bot/features/operations/keyboards_operations.py`

**Add method:**
```python
@staticmethod
def transactions_history_menu(has_more: bool = False, page: int = 0) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Volver a Operaciones", callback_data="operations_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

### Task 1.4: Agregar mensajes para historial

**Files:**
- Modify: `telegram_bot/features/operations/messages_operations.py`

**Add class:**
```python
class Transactions:
    HISTORY_HEADER = (
        "📜 **Historial de Transacciones**\n\n"
        "Aquí están todas tus transacciones:\n"
    )
    
    NO_TRANSACTIONS = (
        "📭 **Sin Transacciones**\n\n"
        "Aún no tienes transacciones registradas.\n\n"
        "💡 Ve al 🛒 **Shop** para hacer tu primera compra."
    )
    
    ORDER_ITEM = (
        "{status_emoji} **{package_type}**\n"
        "💰 {amount_usdt} USDT | 📅 {date}\n"
        "Estado: {status_text}\n"
        "───────────────\n"
    )
```

### Verification 1.1
- [ ] Menú de operaciones se muestra correctamente
- [ ] Layout tiene 2 columnas para botones principales
- [ ] Botón "📜 Historial" está presente

---

## Phase 2: Servicio de Historial

### Task 2.1: Agregar método get_user_orders_by_status

**Files:**
- Modify: `infrastructure/persistence/postgresql/crypto_order_repository.py`

**Add method:**
```python
async def get_by_user_with_status(
    self, 
    user_id: int,
    status: Optional[CryptoOrderStatus] = None,
    limit: int = 10,
    offset: int = 0
) -> List[CryptoOrder]:
    query = select(CryptoOrderModel).where(CryptoOrderModel.user_id == user_id)
    
    if status:
        query = query.where(CryptoOrderModel.status == status.value)
    
    query = query.order_by(CryptoOrderModel.created_at.desc()).limit(limit).offset(offset)
    result = await self.session.execute(query)
    models = result.scalars().all()
    return [m.to_entity() for m in models]
```

### Task 2.2: Agregar método count_user_orders

**Files:**
- Modify: `infrastructure/persistence/postgresql/crypto_order_repository.py`

**Add method:**
```python
async def count_by_user(self, user_id: int) -> int:
    from sqlalchemy import func
    result = await self.session.execute(
        select(func.count()).where(CryptoOrderModel.user_id == user_id)
    )
    return result.scalar() or 0
```

### Verification 2.1
- [ ] Tests del repositorio pasan
- [ ] Métodos nuevos funcionan correctamente

---

## Phase 3: Implementar Handlers

### Task 3.1: Implementar método show_transactions_history

**Files:**
- Modify: `telegram_bot/features/operations/handlers_operations.py`

**Add imports:**
```python
from infrastructure.persistence.postgresql.crypto_order_repository import PostgresCryptoOrderRepository
from domain.entities.crypto_order import CryptoOrderStatus
```

**Add method:**
```python
async def show_transactions_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.callback_query or not update.effective_user:
        return
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"📜 User {user_id} viewing transaction history")
    
    try:
        # Obtener órdenes del usuario
        orders = await self.crypto_order_repo.get_by_user(user_id)
        
        if not orders:
            message = OperationsMessages.Transactions.NO_TRANSACTIONS
            keyboard = OperationsKeyboards.transactions_history_menu()
        else:
            message = OperationsMessages.Transactions.HISTORY_HEADER
            message += self._format_orders_list(orders[:10])  # Primeras 10
            
            has_more = len(orders) > 10
            keyboard = OperationsKeyboards.transactions_history_menu(has_more=has_more)
        
        await TelegramUtils.safe_edit_message(
            query, context, text=message, reply_markup=keyboard, parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error showing transaction history: {e}")
        await TelegramUtils.safe_edit_message(
            query, context, text=OperationsMessages.Error.SYSTEM_ERROR, parse_mode="Markdown"
        )
```

### Task 3.2: Agregar método auxiliar _format_orders_list

**Files:**
- Modify: `telegram_bot/features/operations/handlers_operations.py`

**Add method:**
```python
def _format_orders_list(self, orders: List) -> str:
    """Formatear lista de órdenes para mostrar al usuario."""
    status_map = {
        CryptoOrderStatus.PENDING: ("⏳", "Pendiente"),
        CryptoOrderStatus.COMPLETED: ("✅", "Completada"),
        CryptoOrderStatus.FAILED: ("❌", "Fallida"),
        CryptoOrderStatus.EXPIRED: ("⏰", "Expirada"),
    }
    
    lines = []
    for order in orders:
        emoji, text = status_map.get(order.status, ("❓", str(order.status)))
        date_str = order.created_at.strftime("%d/%m/%Y %H:%M")
        lines.append(
            OperationsMessages.Transactions.ORDER_ITEM.format(
                status_emoji=emoji,
                package_type=order.package_type.upper(),
                amount_usdt=order.amount_usdt,
                date=date_str,
                status_text=text,
            )
        )
    
    return "".join(lines)
```

### Task 3.3: Actualizar constructor para inyectar crypto_order_repo

**Files:**
- Modify: `telegram_bot/features/operations/handlers_operations.py:27-34`

```python
def __init__(
    self, 
    vpn_service: VpnService, 
    referral_service: ReferralService,
    crypto_order_repo: Optional[PostgresCryptoOrderRepository] = None
):
    self.vpn_service = vpn_service
    self.referral_service = referral_service
    self.crypto_order_repo = crypto_order_repo
    logger.info("⚙️ OperationsHandler inicializado")
```

### Task 3.4: Registrar nuevo callback handler

**Files:**
- Modify: `telegram_bot/features/operations/handlers_operations.py:202-220`

**Add to get_operations_callback_handlers:**
```python
CallbackQueryHandler(handler.show_transactions_history, pattern="^transactions_history$"),
```

### Task 3.5: Actualizar handler_initializer para inyectar dependencia

**Files:**
- Modify: `telegram_bot/handlers/handler_initializer.py:95-108`

**Update _get_core_handlers:**
```python
from infrastructure.persistence.postgresql.crypto_order_repository import PostgresCryptoOrderRepository
# ...
async def _get_core_handlers(...):
    crypto_order_repo = container.resolve(PostgresCryptoOrderRepository)
    # ...
    handlers.extend(get_operations_handlers(vpn_service, referral_service, crypto_order_repo))
    handlers.extend(get_operations_callback_handlers(vpn_service, referral_service, crypto_order_repo))
```

### Verification 3.1
- [ ] Handler responde al callback "transactions_history"
- [ ] Muestra lista formateada de transacciones
- [ ] Estados se muestran con emojis correctos
- [ ] Botón volver funciona

---

## Phase 4: Tests

### Task 4.1: Crear test para OperationsKeyboards.transactions_history_menu

**Files:**
- Create: `tests/telegram_bot/features/operations/test_keyboards_operations.py`

```python
import pytest
from telegram_bot.features.operations.keyboards_operations import OperationsKeyboards


class TestOperationsKeyboards:
    def test_operations_menu_contains_history_button(self):
        keyboard = OperationsKeyboards.operations_menu(credits=0)
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]
        assert "📜 Historial" in buttons
    
    def test_transactions_history_menu_has_back_button(self):
        keyboard = OperationsKeyboards.transactions_history_menu()
        buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]
        assert "🔙 Volver a Operaciones" in buttons
```

### Task 4.2: Crear test para show_transactions_history handler

**Files:**
- Create: `tests/telegram_bot/features/operations/test_handlers_operations.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram_bot.features.operations.handlers_operations import OperationsHandler


class TestShowTransactionsHistory:
    @pytest.fixture
    def handler(self, mock_crypto_order_repo):
        return OperationsHandler(
            vpn_service=MagicMock(),
            referral_service=MagicMock(),
            crypto_order_repo=mock_crypto_order_repo
        )
    
    @pytest.mark.asyncio
    async def test_show_transactions_history_no_orders(self, handler, mock_crypto_order_repo):
        mock_crypto_order_repo.get_by_user.return_value = []
        # ... test implementation
    
    @pytest.mark.asyncio
    async def test_show_transactions_history_with_orders(self, handler, mock_crypto_order_repo):
        # ... test implementation with mock orders
```

### Task 4.3: Ejecutar todos los tests

**Command:**
```bash
source venv/bin/activate && pytest tests/telegram_bot/features/operations/ -v
```

### Verification 4.1
- [ ] Todos los tests nuevos pasan
- [ ] Tests existentes no se rompen
- [ ] Coverage mantenido

---

## Phase 5: Finalización

### Task 5.1: Actualizar CHANGELOG.md

### Task 5.2: Commit de cambios

```bash
git add .
git commit -m "feat: redesign operations menu and add transaction history (#<issue-id>)"
```

### Task 5.3: Verificación final

- [ ] Linter pasa (`flake8 .`)
- [ ] Formateo correcto (`black .`)
- [ ] Type checking pasa (`mypy .`)
- [ ] Todos los tests pasan (`pytest`)

## Checkpoints

| Phase | Checkpoint SHA | Date | Status    |
|-------|----------------|------|-----------|
| Phase 1 | ✓              |      | completed |
| Phase 2 | ✓              |      | completed |
| Phase 3 | ✓              |      | completed |
| Phase 4 | ✓              |      | completed |
| Phase 5 | ✓              |      | completed |
