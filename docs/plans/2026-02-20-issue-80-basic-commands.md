# Issue 80: Implementar Ayuda y Comandos Básicos - Plan de Implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar sistema de ayuda y comandos básicos del bot, reemplazando comandos obsoletos por comandos más intuitivos.

**Architecture:** Feature-based modular architecture. Crear nuevo módulo `basic_commands` para `/start` y `/help`, renombrar comandos existentes en sus respectivos módulos, y añadir comando `/data` en `buy_gb`.

**Tech Stack:** Python 3.x, python-telegram-bot, Clean Architecture

---

## Task 1: Crear módulo basic_commands con /help

**Files:**
- Create: `telegram_bot/features/basic_commands/__init__.py`
- Create: `telegram_bot/features/basic_commands/messages_basic.py`
- Create: `telegram_bot/features/basic_commands/handlers_basic.py`

**Step 1: Crear __init__.py**

```python
"""
Comandos básicos del bot: /start, /help

Author: uSipipo Team
Version: 1.0.0
"""

from .handlers_basic import get_basic_handlers, get_basic_callback_handlers

__all__ = ["get_basic_handlers", "get_basic_callback_handlers"]
```

**Step 2: Crear messages_basic.py**

```python
"""
Mensajes para comandos básicos del bot.

Author: uSipipo Team
Version: 1.0.0
"""


class BasicMessages:
    """Mensajes para comandos básicos."""

    HELP_TEXT = (
        "📋 *Comandos disponibles:*\n\n"
        "/start - Iniciar bot\n"
        "/help - Mostrar ayuda\n"
        "/keys - Ver mis claves\n"
        "/newkey - Crear nueva clave\n"
        "/buy - Comprar GB\n"
        "/data - Ver consumo\n"
    )

    WELCOME_NEW_USER = (
        "🎉 *¡Bienvenido a uSipipo!*\n\n"
        "Tu VPN personal está lista para usar.\n\n"
        "🎁 *Plan Free:*\n"
        "• 10 GB de datos\n"
        "• 2 claves VPN\n\n"
        "📱 Usa el menú para gestionar tu VPN.\n\n"
        "¿Necesitas ayuda? Usa /help"
    )

    WELCOME_RETURNING = (
        "👋 *¡Bienvenido de vuelta!*\n\n"
        "Usa el menú para gestionar tu VPN.\n"
    )
```

**Step 3: Crear handlers_basic.py**

```python
"""
Handlers para comandos básicos del bot.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.logger import logger
from .messages_basic import BasicMessages
from telegram_bot.keyboards import MainMenuKeyboard
from config import settings
from application.services.vpn_service import VpnService


class BasicHandler:
    """Handler para comandos básicos."""

    def __init__(self, vpn_service: VpnService):
        self.vpn_service = vpn_service
        logger.info("📋 BasicHandler inicializado")

    async def help_handler(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
        """Muestra la lista de comandos disponibles."""
        logger.info(f"📋 /help ejecutado por usuario {update.effective_user.id}")
        
        await update.message.reply_text(
            text=BasicMessages.HELP_TEXT,
            parse_mode="Markdown"
        )


def get_basic_handlers(vpn_service: VpnService):
    """Retorna los handlers de comandos básicos."""
    handler = BasicHandler(vpn_service)

    return [
        CommandHandler("help", handler.help_handler),
    ]


def get_basic_callback_handlers(vpn_service: VpnService):
    """Retorna los handlers de callbacks para comandos básicos."""
    return []
```

**Step 4: Commit**

```bash
git add telegram_bot/features/basic_commands/
git commit -m "feat(basic_commands): add /help command module"
```

---

## Task 2: Renombrar /mykeys a /keys en key_management

**Files:**
- Modify: `telegram_bot/features/key_management/handlers_key_management.py:431-434`

**Step 1: Actualizar get_key_management_handlers**

Modificar la función `get_key_management_handlers` para usar `/keys`:

```python
def get_key_management_handlers(vpn_service: VpnService):
    """
    Retorna los handlers de gestión de llaves.
    
    Args:
        vpn_service: Servicio de VPN
        
    Returns:
        list: Lista de handlers
    """
    handler = KeyManagementHandler(vpn_service)
    
    return [
        MessageHandler(filters.Regex("^🛡️ Mis Llaves$"), handler.show_key_submenu),
        CommandHandler("keys", handler.show_key_submenu),
    ]
```

**Step 2: Commit**

```bash
git add telegram_bot/features/key_management/handlers_key_management.py
git commit -m "feat(key_management): rename /mykeys to /keys command"
```

---

## Task 3: Renombrar /newkeys a /newkey en vpn_keys

**Files:**
- Modify: `telegram_bot/features/vpn_keys/handlers_vpn_keys.py:198-201`

**Step 1: Actualizar entry_points en ConversationHandler**

Modificar el `ConversationHandler` en `get_vpn_keys_handler`:

```python
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Crear Nueva$"), handler.start_creation),
            CallbackQueryHandler(handler.start_creation, pattern="^create_key$"),
            CommandHandler("newkey", handler.start_creation)
        ],
```

**Step 2: Commit**

```bash
git add telegram_bot/features/vpn_keys/handlers_vpn_keys.py
git commit -m "feat(vpn_keys): rename /newkeys to /newkey command"
```

---

## Task 4: Renombrar /buygb a /buy en buy_gb

**Files:**
- Modify: `telegram_bot/features/buy_gb/handlers_buy_gb.py:245-252`

**Step 1: Actualizar get_buy_gb_handlers**

```python
def get_buy_gb_handlers(data_package_service: DataPackageService):
    handler = BuyGbHandler(data_package_service)
    
    return [
        MessageHandler(filters.Regex("^📦 Comprar GB$"), handler.show_packages),
        CommandHandler("buy", handler.show_packages),
        CommandHandler("packages", handler.show_packages),
    ]
```

**Step 2: Commit**

```bash
git add telegram_bot/features/buy_gb/handlers_buy_gb.py
git commit -m "feat(buy_gb): rename /buygb to /buy command"
```

---

## Task 5: Implementar comando /data

**Files:**
- Modify: `telegram_bot/features/buy_gb/messages_buy_gb.py`
- Modify: `telegram_bot/features/buy_gb/handlers_buy_gb.py`

**Step 1: Añadir mensaje DATA_COMMAND en messages_buy_gb.py**

Añadir después de la clase existente:

```python
    class Data:
        """Mensajes para comando /data."""

        HEADER = "💾 *Mis Datos*\n"

        DATA_INFO = (
            "📊 *Resumen de consumo:*\n\n"
            "📦 Paquetes activos: {active_packages}\n"
            "📥 Total disponible: {total_gb:.2f} GB\n"
            "📤 Datos usados: {used_gb:.2f} GB\n"
            "📥 Datos restantes: {remaining_gb:.2f} GB\n"
        )

        NO_DATA = (
            "💾 *Mis Datos*\n\n"
            "No tienes paquetes de datos activos.\n\n"
            "Usa /buy para adquirir más datos."
        )
```

**Step 2: Añadir data_handler en handlers_buy_gb.py**

Añadir método a la clase `BuyGbHandler`:

```python
    async def data_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el consumo de datos del usuario."""
        user_id = update.effective_user.id
        logger.info(f"💾 /data ejecutado por usuario {user_id}")

        try:
            summary = await self.data_package_service.get_user_data_summary(
                user_id=user_id,
                current_user_id=user_id
            )

            if summary["active_packages"] == 0:
                message = BuyGbMessages.Data.NO_DATA
            else:
                message = BuyGbMessages.Data.HEADER + BuyGbMessages.Data.DATA_INFO.format(
                    active_packages=summary["active_packages"],
                    total_gb=summary["total_limit_gb"],
                    used_gb=summary["total_used_gb"],
                    remaining_gb=summary["remaining_gb"]
                )

            await update.message.reply_text(
                text=message,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error en data_handler: {e}")
            await update.message.reply_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown"
            )
```

**Step 3: Añadir CommandHandler en get_buy_gb_handlers**

```python
def get_buy_gb_handlers(data_package_service: DataPackageService):
    handler = BuyGbHandler(data_package_service)
    
    return [
        MessageHandler(filters.Regex("^📦 Comprar GB$"), handler.show_packages),
        CommandHandler("buy", handler.show_packages),
        CommandHandler("packages", handler.show_packages),
        CommandHandler("data", handler.data_handler),
    ]
```

**Step 4: Commit**

```bash
git add telegram_bot/features/buy_gb/
git commit -m "feat(buy_gb): add /data command for data usage"
```

---

## Task 6: Actualizar handler_initializer.py

**Files:**
- Modify: `telegram_bot/handlers/handler_initializer.py`

**Step 1: Añadir import de basic_commands**

Añadir después de línea 35:

```python
from telegram_bot.features.basic_commands.handlers_basic import (
    get_basic_handlers, get_basic_callback_handlers
)
```

**Step 2: Añadir handlers de basic_commands en _get_core_handlers**

Añadir después de la inicialización de handlers:

```python
    handlers.extend(get_basic_handlers(vpn_service))
    handlers.extend(get_basic_callback_handlers(vpn_service))
    logger.info("Basic commands handlers configured")
```

**Step 3: Commit**

```bash
git add telegram_bot/handlers/handler_initializer.py
git commit -m "feat(handlers): integrate basic_commands module"
```

---

## Task 7: Verificar tests

**Step 1: Ejecutar tests existentes**

```bash
pytest -v
```

Expected: Todos los tests pasan

**Step 2: Si hay fallos, revisar y corregir**

---

## Task 8: Commit final y verificar

**Step 1: Verificar estado de cambios**

```bash
git status
git diff --stat
```

**Step 2: Commit final si hay cambios pendientes**

```bash
git add -A
git commit -m "feat(issue-80): implement basic commands (/help, /keys, /newkey, /buy, /data)"
```

---

## Resumen de Cambios

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `basic_commands/__init__.py` | Crear | Nuevo módulo |
| `basic_commands/messages_basic.py` | Crear | Mensajes de ayuda |
| `basic_commands/handlers_basic.py` | Crear | Handler /help |
| `key_management/handlers_*.py` | Modificar | /mykeys → /keys |
| `vpn_keys/handlers_*.py` | Modificar | /newkeys → /newkey |
| `buy_gb/handlers_*.py` | Modificar | /buygb → /buy, añadir /data |
| `buy_gb/messages_*.py` | Modificar | Mensajes para /data |
| `handler_initializer.py` | Modificar | Integrar basic_commands |

## Criterios de Aceptación

- [ ] `/help` muestra lista de comandos
- [ ] `/keys` lista claves del usuario
- [ ] `/newkey` permite crear nueva clave
- [ ] `/buy` muestra paquetes disponibles
- [ ] `/data` muestra consumo de datos
- [ ] Comandos obsoletos eliminados
- [ ] Tests pasando
