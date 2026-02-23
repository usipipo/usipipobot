# Rediseño del Flujo de Operaciones - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactorizar el flujo del bot para corregir la estructura del menú "Operaciones", separando compras con Telegram Stars del sistema de créditos de referido.

**Architecture:** Clean Architecture con feature-based modules. Se eliminará el módulo payments obsoleto, se rediseñará operations, y se creará un nuevo módulo shop que integre buy_gb.

**Tech Stack:** Python 3.11, python-telegram-bot, PostgreSQL, Pydantic

---

## Task 1: Actualizar Menú Principal

**Files:**
- Modify: `telegram_bot/keyboards/main_menu.py:15-27`
- Modify: `telegram_bot/keyboards/main_menu.py:29-47`

**Step 1: Cambiar botón "Comprar GB" por "Operaciones"**

En `main_menu.py`, línea 22:
```python
# ANTES
InlineKeyboardButton("📦 Comprar GB", callback_data="buy_data"),
# DESPUÉS
InlineKeyboardButton("⚙️ Operaciones", callback_data="operations_menu"),
```

**Step 2: Actualizar menú con admin**

En `main_menu.py`, línea 41:
```python
# ANTES
InlineKeyboardButton("📦 Comprar GB", callback_data="buy_data"),
# DESPUÉS
InlineKeyboardButton("⚙️ Operaciones", callback_data="operations_menu"),
```

**Step 3: Commit**

```bash
git add telegram_bot/keyboards/main_menu.py
git commit -m "feat: change 'Comprar GB' button to 'Operaciones' in main menu (Issue #143)"
```

---

## Task 2: Eliminar Módulo Payments Obsoleto

**Files:**
- Delete: `telegram_bot/features/payments/handlers_payments.py`
- Delete: `telegram_bot/features/payments/keyboards_payments.py`
- Delete: `telegram_bot/features/payments/messages_payments.py`
- Delete: `telegram_bot/features/payments/__init__.py`
- Modify: `telegram_bot/handlers/handler_initializer.py`

**Step 1: Eliminar archivos del módulo payments**

```bash
rm -rf telegram_bot/features/payments/
```

**Step 2: Limpiar handler_initializer.py**

Eliminar líneas 44-47:
```python
# ELIMINAR
from telegram_bot.features.payments.handlers_payments import (
    get_payments_callback_handlers,
    get_payments_handlers,
)
```

Eliminar líneas 111-113 en `_get_core_handlers`:
```python
# ELIMINAR
handlers.extend(get_payments_handlers(payment_service, vpn_service))
handlers.extend(get_payments_callback_handlers(payment_service, vpn_service))
logger.info("Payments handlers configured")
```

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove obsolete payments module (Issue #146)"
```

---

## Task 3: Rediseñar Módulo Operations

**Files:**
- Modify: `telegram_bot/features/operations/keyboards_operations.py`
- Modify: `telegram_bot/features/operations/messages_operations.py`
- Modify: `telegram_bot/features/operations/handlers_operations.py`
- Modify: `telegram_bot/features/operations/__init__.py`

**Step 1: Actualizar keyboards_operations.py**

Reemplazar la clase completa:
```python
"""
Teclados para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Créditos + Shop
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class OperationsKeyboards:
    """Teclados para operaciones del usuario."""

    @staticmethod
    def operations_menu(credits: int = 0) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(f"🎁 Créditos ({credits})", callback_data="credits_menu"),
            ],
            [
                InlineKeyboardButton("🛒 Shop", callback_data="shop_menu"),
            ],
            [
                InlineKeyboardButton("👥 Referidos", callback_data="referral_menu"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        from telegram_bot.keyboards import MainMenuKeyboard
        return MainMenuKeyboard.main_menu() if not is_admin else MainMenuKeyboard.main_menu_with_admin(0, 0)

    @staticmethod
    def credits_menu(credits: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("✨ Canjear por GB", callback_data="credits_redeem_data"),
                InlineKeyboardButton("🔑 Canjear por Slot", callback_data="credits_redeem_slot"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def shop_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📦 Paquetes de GB", callback_data="buy_gb_menu"),
            ],
            [
                InlineKeyboardButton("🔑 Slots Adicionales", callback_data="buy_slots_menu"),
            ],
            [
                InlineKeyboardButton("✨ Extras con Créditos", callback_data="credits_menu"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
```

**Step 2: Actualizar messages_operations.py**

Reemplazar la clase completa:
```python
"""
Mensajes para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Créditos + Shop
"""


class OperationsMessages:
    """Mensajes para operaciones del usuario."""

    class Menu:
        MAIN = (
            "⚙️ **Operaciones**\n\n"
            "Gestiona tu cuenta y servicios:\n\n"
            "🎁 **Créditos** - Obtén beneficios por referir amigos\n"
            "🛒 **Shop** - Compra paquetes y slots\n"
            "👥 **Referidos** - Invita amigos y gana créditos\n\n"
            "Selecciona una opción:"
        )

    class Credits:
        DISPLAY = (
            "🎁 **Tus Créditos**\n\n"
            "💎 **Créditos disponibles:** {credits}\n\n"
            "💡 Los créditos se obtienen al referir amigos.\n"
            "Úsalos para obtener GB extra o slots adicionales."
        )

        REDEEM_DATA = (
            "📦 **Canjear Créditos por GB**\n\n"
            "💡 {credits_per_gb} créditos = 1 GB de navegación\n\n"
            "Tus créditos: {credits}\n"
            "GB disponibles para canjear: {gb_available}"
        )

        REDEEM_SLOT = (
            "🔑 **Canjear Créditos por Slot**\n\n"
            "💡 {credits_per_slot} créditos = 1 slot adicional\n\n"
            "Tus créditos: {credits}\n"
            "Puedes obtener: {slots_available} slot(s)"
        )

    class Shop:
        MENU = (
            "🛒 **Shop**\n\n"
            "📦 **Paquetes de GB** - Compra con Telegram Stars\n"
            "🔑 **Slots** - Más claves VPN con Telegram Stars\n"
            "✨ **Extras** - Canjea tus créditos de referido\n\n"
            "Selecciona lo que deseas comprar:"
        )

    class Error:
        SYSTEM_ERROR = (
            "❌ **Error del Sistema**\n\n"
            "No pude procesar tu solicitud.\n\n"
            "Por favor, intenta más tarde."
        )

        INSUFFICIENT_CREDITS = (
            "💸 **Créditos Insuficientes**\n\n"
            "No tienes suficientes créditos para esta operación.\n\n"
            "💡 Invita más amigos para obtener créditos."
        )

    class Success:
        OPERATION_COMPLETED = (
            "✅ **Operación Completada**\n\n"
            "Tu solicitud ha sido procesada exitosamente."
        )
```

**Step 3: Actualizar handlers_operations.py**

Reemplazar contenido manteniendo imports:
```python
"""
Handlers para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Créditos + Shop
"""

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from application.services.referral_service import ReferralService
from application.services.vpn_service import VpnService
from config import settings
from utils.logger import logger

from .keyboards_operations import OperationsKeyboards
from .messages_operations import OperationsMessages


class OperationsHandler:
    """Handler para operaciones del usuario."""

    def __init__(self, vpn_service: VpnService, referral_service: ReferralService):
        self.vpn_service = vpn_service
        self.referral_service = referral_service
        logger.info("⚙️ OperationsHandler inicializado")

    async def operations_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            credits = stats.referral_credits
            
            message = OperationsMessages.Menu.MAIN
            keyboard = OperationsKeyboards.operations_menu(credits=credits)

            if update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )
            elif update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Error en operations_menu: {e}")
            await self._send_error(update, OperationsMessages.Error.SYSTEM_ERROR)

    async def show_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            message = OperationsMessages.Credits.DISPLAY.format(credits=stats.referral_credits)
            keyboard = OperationsKeyboards.credits_menu(stats.referral_credits)
            
            await query.edit_message_text(
                text=message, reply_markup=keyboard, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error en show_credits: {e}")
            await query.edit_message_text(
                text=OperationsMessages.Error.SYSTEM_ERROR, parse_mode="Markdown"
            )

    async def show_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        message = OperationsMessages.Shop.MENU
        keyboard = OperationsKeyboards.shop_menu()
        
        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        from telegram_bot.common.keyboards import CommonKeyboards
        from telegram_bot.common.messages import CommonMessages
        
        is_admin = update.effective_user.id == int(settings.ADMIN_ID)
        
        await query.edit_message_text(
            text=CommonMessages.Menu.WELCOME_BACK,
            reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
            parse_mode="Markdown",
        )

    async def _send_error(self, update: Update, message: str):
        if update.message:
            await update.message.reply_text(text=message, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.edit_message_text(text=message, parse_mode="Markdown")


def get_operations_handlers(vpn_service: VpnService, referral_service: ReferralService):
    handler = OperationsHandler(vpn_service, referral_service)

    return [
        MessageHandler(filters.Regex("^⚙️ Operaciones$"), handler.operations_menu),
        CommandHandler("operaciones", handler.operations_menu),
    ]


def get_operations_callback_handlers(vpn_service: VpnService, referral_service: ReferralService):
    handler = OperationsHandler(vpn_service, referral_service)

    return [
        CallbackQueryHandler(handler.operations_menu, pattern="^operations_menu$"),
        CallbackQueryHandler(handler.show_credits, pattern="^credits_menu$"),
        CallbackQueryHandler(handler.show_shop, pattern="^shop_menu$"),
        CallbackQueryHandler(handler.back_to_main_menu, pattern="^main_menu$"),
    ]
```

**Step 4: Actualizar __init__.py**

```python
"""
Operations Feature - Sistema de Operaciones

Author: uSipipo Team
Version: 3.0.0 - Créditos + Shop
"""

from .handlers_operations import (
    OperationsHandler,
    get_operations_callback_handlers,
    get_operations_handlers,
)

__all__ = [
    "OperationsHandler",
    "get_operations_handlers",
    "get_operations_callback_handlers",
]
```

**Step 5: Commit**

```bash
git add telegram_bot/features/operations/
git commit -m "feat: redesign operations module with credits and shop menu (Issue #144)"
```

---

## Task 4: Actualizar Handler Initializer

**Files:**
- Modify: `telegram_bot/handlers/handler_initializer.py`

**Step 1: Actualizar imports y funciones**

Modificar para pasar `referral_service` a operations handlers:
```python
handlers.extend(get_operations_handlers(vpn_service, referral_service))
handlers.extend(get_operations_callback_handlers(vpn_service, referral_service))
```

**Step 2: Commit**

```bash
git add telegram_bot/handlers/handler_initializer.py
git commit -m "fix: update handler initializer for new operations module (Issue #142)"
```

---

## Task 5: Actualizar Buy GB para integración con Shop

**Files:**
- Modify: `telegram_bot/features/buy_gb/keyboards_buy_gb.py`

**Step 1: Agregar botón de volver a operaciones**

En los teclados de back, agregar opción de volver a operations_menu:
```python
@staticmethod
def back_to_operations() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Volver a Operaciones", callback_data="operations_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 2: Commit**

```bash
git add telegram_bot/features/buy_gb/
git commit -m "feat: add back to operations button in buy_gb keyboards (Issue #145)"
```

---

## Task 6: Actualizar mensajes de ayuda

**Files:**
- Modify: `telegram_bot/features/basic_commands/messages_basic.py`
- Modify: `telegram_bot/features/user_management/messages_user_management.py`

**Step 1: Actualizar referencias a "Comprar GB"**

Cambiar menciones de "Comprar GB" por "Operaciones" donde aplique.

**Step 2: Commit**

```bash
git add telegram_bot/features/basic_commands/ telegram_bot/features/user_management/
git commit -m "docs: update help messages for operations flow (Issue #142)"
```

---

## Task 7: Ejecutar Tests y Verificar

**Step 1: Ejecutar tests**

```bash
./venv/bin/pytest tests/ -v --tb=short
```

**Step 2: Verificar linting**

```bash
./venv/bin/python -m py_compile telegram_bot/features/operations/handlers_operations.py
./venv/bin/python -m py_compile telegram_bot/handlers/handler_initializer.py
```

**Step 3: Commit final**

```bash
git add -A
git commit -m "refactor: complete operations flow redesign (closes #142, #143, #144, #145, #146)"
```

---

## Verification Checklist

- [ ] Menú principal muestra "⚙️ Operaciones"
- [ ] Menú operaciones muestra Créditos, Shop, Referidos
- [ ] Menú Shop muestra Paquetes GB, Slots, Extras
- [ ] Créditos muestra canje por GB y Slots
- [ ] Módulo payments eliminado
- [ ] Tests pasan
- [ ] Sin errores LSP
