# Feature: Comando /referir y UI de canje de créditos - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar el comando `/referir` y la interfaz de usuario para el sistema de canje de créditos por referidos.

**Architecture:** Feature-based modular architecture. Crear nuevo módulo `referral` en `telegram_bot/features/` con handlers, keyboards y messages. Integrar con el `ReferralService` existente y registrar en `handler_initializer.py`.

**Tech Stack:** Python 3.10+, python-telegram-bot 20.x, existing ReferralService

---

## Contexto

El `ReferralService` ya existe con todos los métodos necesarios:
- `register_referral()` - Registra un nuevo referido
- `get_referral_stats()` - Obtiene estadísticas de referidos
- `redeem_credits_for_data()` - Canjea créditos por datos (1GB = 100 créditos)
- `redeem_credits_for_slot()` - Canjea créditos por slot (+1 slot = 500 créditos)

El entity `User` ya tiene los campos:
- `referral_code: Optional[str]`
- `referred_by: Optional[int]`
- `referral_credits: int`

Configuración en `config.py`:
- `REFERRAL_CREDITS_PER_REFERRAL: int = 100`
- `REFERRAL_BONUS_NEW_USER: int = 50`
- `REFERRAL_CREDITS_PER_GB: int = 100`
- `REFERRAL_CREDITS_PER_SLOT: int = 500`

---

### Task 1: Crear estructura del módulo referral

**Files:**
- Create: `telegram_bot/features/referral/__init__.py`
- Create: `telegram_bot/features/referral/messages_referral.py`
- Create: `telegram_bot/features/referral/keyboards_referral.py`

**Step 1: Crear __init__.py**

```python
"""
Feature de referidos para uSipipo.

Author: uSipipo Team
Version: 1.0.0
"""
```

**Step 2: Crear messages_referral.py**

```python
"""
Mensajes para el módulo de referidos.

Author: uSipipo Team
Version: 1.0.0
"""

from config import settings


class ReferralMessages:
    """Mensajes del sistema de referidos."""

    class Menu:
        HEADER = "🎁 *Sistema de Referidos*"
        
        @staticmethod
        def referral_info(code: str, credits: int, total_referrals: int, bot_username: str) -> str:
            return f"""
{ReferralMessages.Menu.HEADER}

📋 *Tu código de referido:* `{code}`

🔗 *Comparte este link:*
`https://t.me/{bot_username}?start={code}`

📊 *Tus estadísticas:*
• Créditos disponibles: *{credits}*
• Referidos exitosos: *{total_referrals}*

💡 *¿Cómo funciona?*
1. Comparte tu código con amigos
2. Cuando se registran, recibes *{settings.REFERRAL_CREDITS_PER_REFERRAL} créditos*
3. Ellos reciben *{settings.REFERRAL_BONUS_NEW_USER} créditos* de bienvenida
"""

    class Redeem:
        HEADER = "💳 *Canjear Créditos*"
        
        OPTIONS = f"""
{HEADER}

💰 *Opciones de canje:*

• 📦 *1 GB Extra* - 100 créditos
• 🔑 *+1 Slot de Clave* - 500 créditos

📊 Selecciona qué quieres canjear:
"""
        
        INSUFFICIENT_CREDITS = """
❌ *Créditos insuficientes*

No tienes suficientes créditos para este canje.
"""
        
        @staticmethod
        def insufficient_for_slot(required: int, current: int) -> str:
            return f"""
❌ *Créditos insuficientes*

Necesitas *{required} créditos* para +1 slot.
Tienes *{current} créditos*.
"""
        
        CONFIRM_DATA = """
✅ *Confirmar Canje*

Vas a canjear *{credits} créditos* por *{gb} GB* de datos extra.

¿Continuar?
"""
        
        CONFIRM_SLOT = """
✅ *Confirmar Canje*

Vas a canjear *{credits} créditos* por *+1 slot de clave*.

¿Continuar?
"""

    class Success:
        DATA_REDEEMED = """
✅ *¡Canje exitoso!*

📦 Has recibido *{gb} GB* de datos extra.
💰 Créditos restantes: *{remaining}*
"""
        
        SLOT_REDEEMED = """
✅ *¡Canje exitoso!*

🔑 Ahora puedes crear *+1 clave adicional*.
💰 Créditos restantes: *{remaining}*
"""

    class Error:
        USER_NOT_FOUND = "❌ Usuario no encontrado."
        SYSTEM_ERROR = "❌ Error del sistema. Intenta nuevamente."
        INSUFFICIENT_CREDITS = "❌ No tienes suficientes créditos."
        INVALID_ACTION = "❌ Acción inválida."

    class Info:
        @staticmethod
        def credits_required_for_gb() -> int:
            return settings.REFERRAL_CREDITS_PER_GB
        
        @staticmethod
        def credits_required_for_slot() -> int:
            return settings.REFERRAL_CREDITS_PER_SLOT
```

**Step 3: Crear keyboards_referral.py**

```python
"""
Teclados para el módulo de referidos.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings


class ReferralKeyboards:
    """Teclados para el sistema de referidos."""

    @staticmethod
    def main_menu(credits: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("💳 Canjear Créditos", callback_data="referral_redeem_menu"),
            ],
            [
                InlineKeyboardButton("📋 Copiar Código", callback_data="referral_copy_code"),
                InlineKeyboardButton("🔄 Actualizar", callback_data="referral_refresh"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def redeem_menu(credits: int) -> InlineKeyboardMarkup:
        keyboard = []
        
        can_redeem_data = credits >= settings.REFERRAL_CREDITS_PER_GB
        can_redeem_slot = credits >= settings.REFERRAL_CREDITS_PER_SLOT
        
        if can_redeem_data:
            keyboard.append([
                InlineKeyboardButton(
                    f"📦 1 GB Extra ({settings.REFERRAL_CREDITS_PER_GB} cr.)",
                    callback_data="referral_redeem_data"
                )
            ])
        
        if can_redeem_slot:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔑 +1 Slot ({settings.REFERRAL_CREDITS_PER_SLOT} cr.)",
                    callback_data="referral_redeem_slot"
                )
            ])
        
        if not can_redeem_data and not can_redeem_slot:
            keyboard.append([
                InlineKeyboardButton("❌ Sin créditos suficientes", callback_data="referral_noop")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Volver", callback_data="referral_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_redeem_data(credits: int, gb: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data="referral_confirm_data"),
                InlineKeyboardButton("❌ Cancelar", callback_data="referral_redeem_menu"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_redeem_slot(credits: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data="referral_confirm_slot"),
                InlineKeyboardButton("❌ Cancelar", callback_data="referral_redeem_menu"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def success_back() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("💳 Canjear Más", callback_data="referral_redeem_menu"),
                InlineKeyboardButton("📋 Mi Código", callback_data="referral_menu"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
```

**Step 4: Commit**

```bash
git add telegram_bot/features/referral/
git commit -m "feat(referral): add messages and keyboards for referral feature"
```

---

### Task 2: Crear handlers del módulo referral

**Files:**
- Create: `telegram_bot/features/referral/handlers_referral.py`

**Step 1: Crear handlers_referral.py**

```python
"""
Handlers para el sistema de referidos.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from application.services.referral_service import ReferralService
from config import settings
from utils.logger import logger

from .keyboards_referral import ReferralKeyboards
from .messages_referral import ReferralMessages


class ReferralHandler:
    """Handler para el sistema de referidos."""

    def __init__(self, referral_service: ReferralService):
        self.referral_service = referral_service
        logger.info("🎁 ReferralHandler inicializado")

    async def show_referral_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el menú principal de referidos."""
        user_id = update.effective_user.id
        query = update.callback_query

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            
            message = ReferralMessages.Menu.referral_info(
                code=stats.referral_code,
                credits=stats.referral_credits,
                total_referrals=stats.total_referrals,
                bot_username=settings.BOT_USERNAME,
            )
            
            keyboard = ReferralKeyboards.main_menu(stats.referral_credits)

            if query:
                await query.answer()
                await query.edit_message_text(
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error en show_referral_menu: {e}")
            error_msg = ReferralMessages.Error.SYSTEM_ERROR
            
            if query:
                await query.answer()
                await query.edit_message_text(text=error_msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(text=error_msg, parse_mode="Markdown")

    async def show_redeem_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el menú de canje de créditos."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            
            message = ReferralMessages.Redeem.OPTIONS
            keyboard = ReferralKeyboards.redeem_menu(stats.referral_credits)

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en show_redeem_menu: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def confirm_redeem_data(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra confirmación para canjear créditos por datos."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            
            if stats.referral_credits < settings.REFERRAL_CREDITS_PER_GB:
                message = ReferralMessages.Redeem.INSUFFICIENT_CREDITS
                keyboard = ReferralKeyboards.redeem_menu(stats.referral_credits)
            else:
                gb = stats.referral_credits // settings.REFERRAL_CREDITS_PER_GB
                credits_to_spend = gb * settings.REFERRAL_CREDITS_PER_GB
                
                message = ReferralMessages.Redeem.CONFIRM_DATA.format(
                    credits=credits_to_spend,
                    gb=gb,
                )
                keyboard = ReferralKeyboards.confirm_redeem_data(
                    credits=credits_to_spend,
                    gb=gb,
                )
                
                context.user_data["redeem_gb"] = gb
                context.user_data["redeem_credits"] = credits_to_spend

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en confirm_redeem_data: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def confirm_redeem_slot(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra confirmación para canjear créditos por slot."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            
            if stats.referral_credits < settings.REFERRAL_CREDITS_PER_SLOT:
                message = ReferralMessages.Redeem.insufficient_for_slot(
                    required=settings.REFERRAL_CREDITS_PER_SLOT,
                    current=stats.referral_credits,
                )
                keyboard = ReferralKeyboards.redeem_menu(stats.referral_credits)
            else:
                message = ReferralMessages.Redeem.CONFIRM_SLOT
                keyboard = ReferralKeyboards.confirm_redeem_slot(
                    credits=settings.REFERRAL_CREDITS_PER_SLOT
                )

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en confirm_redeem_slot: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def execute_redeem_data(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Ejecuta el canje de créditos por datos."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        gb = context.user_data.get("redeem_gb", 1)
        credits = context.user_data.get("redeem_credits", settings.REFERRAL_CREDITS_PER_GB)

        try:
            result = await self.referral_service.redeem_credits_for_data(
                user_id=user_id,
                credits=credits,
                current_user_id=user_id,
            )

            if result.get("success"):
                message = ReferralMessages.Success.DATA_REDEEMED.format(
                    gb=result.get("gb_added", gb),
                    remaining=result.get("remaining_credits", 0),
                )
                keyboard = ReferralKeyboards.success_back()
                
                context.user_data.pop("redeem_gb", None)
                context.user_data.pop("redeem_credits", None)
            else:
                message = ReferralMessages.Error.INSUFFICIENT_CREDITS
                keyboard = ReferralKeyboards.redeem_menu(0)

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en execute_redeem_data: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def execute_redeem_slot(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Ejecuta el canje de créditos por slot."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id

        try:
            result = await self.referral_service.redeem_credits_for_slot(
                user_id=user_id,
                current_user_id=user_id,
            )

            if result.get("success"):
                message = ReferralMessages.Success.SLOT_REDEEMED.format(
                    remaining=result.get("remaining_credits", 0),
                )
                keyboard = ReferralKeyboards.success_back()
            else:
                error = result.get("error", "unknown")
                if error == "insufficient_credits":
                    message = ReferralMessages.Redeem.insufficient_for_slot(
                        required=result.get("required", settings.REFERRAL_CREDITS_PER_SLOT),
                        current=result.get("current", 0),
                    )
                else:
                    message = ReferralMessages.Error.SYSTEM_ERROR
                keyboard = ReferralKeyboards.redeem_menu(result.get("current", 0))

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en execute_redeem_slot: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )


def get_referral_handlers(referral_service: ReferralService):
    """Retorna los handlers de comandos de referidos."""
    handler = ReferralHandler(referral_service)

    return [
        CommandHandler("referir", handler.show_referral_menu),
    ]


def get_referral_callback_handlers(referral_service: ReferralService):
    """Retorna los handlers de callbacks para referidos."""
    handler = ReferralHandler(referral_service)

    return [
        CallbackQueryHandler(handler.show_referral_menu, pattern="^referral_menu$"),
        CallbackQueryHandler(handler.show_referral_menu, pattern="^referral_refresh$"),
        CallbackQueryHandler(handler.show_redeem_menu, pattern="^referral_redeem_menu$"),
        CallbackQueryHandler(handler.confirm_redeem_data, pattern="^referral_redeem_data$"),
        CallbackQueryHandler(handler.confirm_redeem_slot, pattern="^referral_redeem_slot$"),
        CallbackQueryHandler(handler.execute_redeem_data, pattern="^referral_confirm_data$"),
        CallbackQueryHandler(handler.execute_redeem_slot, pattern="^referral_confirm_slot$"),
    ]
```

**Step 2: Commit**

```bash
git add telegram_bot/features/referral/handlers_referral.py
git commit -m "feat(referral): add handlers for /referir command and credit redemption"
```

---

### Task 3: Registrar handlers en handler_initializer.py

**Files:**
- Modify: `telegram_bot/handlers/handler_initializer.py`

**Step 1: Agregar imports**

Añadir después de línea 18:
```python
from application.services.referral_service import ReferralService
```

Añadir después de línea 52:
```python
from telegram_bot.features.referral.handlers_referral import (
    get_referral_callback_handlers,
    get_referral_handlers,
)
```

**Step 2: Agregar función _get_referral_handlers**

Añadir después de `_get_admin_handlers` (después de línea 63):
```python
def _get_referral_handlers(container) -> List[BaseHandler]:
    """Initialize and return referral handlers."""
    referral_service = container.resolve(ReferralService)
    handlers = []
    handlers.extend(get_referral_handlers(referral_service))
    handlers.extend(get_referral_callback_handlers(referral_service))
    logger.info("✅ Handlers de referidos configurados")
    return handlers
```

**Step 3: Agregar llamada en initialize_handlers**

En la función `initialize_handlers`, añadir después de `handlers.extend(_get_admin_handlers(container))`:
```python
handlers.extend(_get_referral_handlers(container))
```

**Step 4: Commit**

```bash
git add telegram_bot/handlers/handler_initializer.py
git commit -m "feat(handlers): register referral handlers in initializer"
```

---

### Task 4: Registrar ReferralService en el container

**Files:**
- Modify: `application/services/common/container.py`

**Step 1: Verificar si ReferralService está registrado**

Buscar si ya existe el registro de `ReferralService` en el container.

**Step 2: Agregar registro si no existe**

Añadir import:
```python
from application.services.referral_service import ReferralService
```

Añadir en `get_container()`:
```python
container.register(ReferralService)
```

**Step 3: Commit**

```bash
git add application/services/common/container.py
git commit -m "feat(container): register ReferralService in DI container"
```

---

### Task 5: Agregar botón de referidos al menú de operaciones

**Files:**
- Modify: `telegram_bot/features/operations/keyboards_operations.py`
- Modify: `telegram_bot/features/operations/handlers_operations.py`

**Step 1: Ver keyboards_operations.py y agregar botón**

Añadir botón "🎁 Referidos" en el menú de operaciones.

**Step 2: Agregar callback handler**

En handlers_operations.py, añadir manejo del callback `referral_menu`.

**Step 3: Commit**

```bash
git add telegram_bot/features/operations/
git commit -m "feat(operations): add referral button to operations menu"
```

---

### Task 6: Integrar referral en registro de usuarios (opcional)

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py`

**Step 1: Modificar start_handler para aceptar código de referido**

El link de referido será: `https://t.me/bot_username?start=REFERRAL_CODE`

Modificar `start_handler` para:
1. Verificar si hay parámetro `start` en el contexto
2. Si existe, intentar registrar como referido
3. Mostrar mensaje de bienvenida con créditos bonificados

**Step 2: Commit**

```bash
git add telegram_bot/features/user_management/handlers_user_management.py
git commit -m "feat(user-management): integrate referral code on user registration"
```

---

### Task 7: Ejecutar tests

**Step 1: Ejecutar tests existentes**

```bash
pytest -v
```

**Step 2: Verificar que no hay errores de import**

```bash
python -c "from telegram_bot.features.referral.handlers_referral import ReferralHandler; print('OK')"
```

**Step 3: Verificar linting (si está configurado)**

```bash
flake8 telegram_bot/features/referral/ --max-line-length=100
```

---

## Checklist Final

- [ ] `/referir` muestra el código de referido y estadísticas
- [ ] Link para compartir es correcto (`https://t.me/{bot_username}?start={code}`)
- [ ] Menú de canje muestra opciones según créditos disponibles
- [ ] Canje de 1GB funciona correctamente (descuenta 100 créditos)
- [ ] Canje de +1 slot funciona correctamente (descuenta 500 créditos)
- [ ] Mensajes de error para créditos insuficientes
- [ ] Navegación entre menús funciona correctamente
- [ ] Handler registrado en handler_initializer.py
- [ ] ReferralService registrado en container
- [ ] Tests pasan correctamente
