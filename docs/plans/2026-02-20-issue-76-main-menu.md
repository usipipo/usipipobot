# Issue 76: Implementar Menú Principal Simplificado

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Crear un menú principal simplificado para el bot de Telegram con las opciones esenciales: Mis Claves VPN, Nueva Clave, Comprar GB, Mis Datos, y Ayuda.

**Architecture:** Se creará un nuevo módulo de teclado dedicado al menú principal en `telegram_bot/keyboards/main_menu.py` que será utilizado por el handler de /start. El diseño sigue el patrón existente de keyboards en el proyecto.

**Tech Stack:** Python, python-telegram-bot, Pydantic

---

## Análisis del Issue

El issue #76 solicita un menú principal simplificado con las siguientes opciones:
1. 🔑 Mis Claves VPN - Ver y gestionar claves
2. ➕ Nueva Clave - Crear nueva clave VPN
3. 📦 Comprar GB - Ver paquetes y comprar
4. 💾 Mis Datos - Ver consumo
5. ❓ Ayuda - Información básica

**Tareas del Issue:**
- [x] Crear telegram_bot/keyboards/main_menu.py
- [ ] Actualizar handler de /start
- [ ] Implementar navegación básica
- [ ] Agregar mensajes de bienvenida

---

## Análisis del Proyecto

### Estructura Actual de Keyboards
- `telegram_bot/common/keyboards.py` - Teclados comunes (252-282 tiene main_menu)
- `telegram_bot/features/*/keyboards_*.py` - Teclados específicos por feature

### Handler de /start
- Ubicación: `telegram_bot/features/user_management/handlers_user_management.py:40-91`
- Usa `UserManagementKeyboards.main_menu(is_admin=is_admin)`

### Navegación Actual
- Pattern: callback_data="main_menu" para volver al menú principal
- Handler: `CallbackQueryHandler(handler.back_to_main_menu, pattern="^main_menu$")`

---

## Plan de Implementación

### Task 1: Crear nuevo módulo de teclado principal

**Files:**
- Create: `telegram_bot/keyboards/__init__.py`
- Create: `telegram_bot/keyboards/main_menu.py`

**Step 1: Crear directorio y __init__.py**

```bash
mkdir -p telegram_bot/keyboards
touch telegram_bot/keyboards/__init__.py
```

**Step 2: Escribir el contenido de main_menu.py**

```python
"""
Menú principal del bot uSipipo.

Author: uSipipo Team
Version: 1.0.0 - Main Menu Module
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenuKeyboard:
    """Teclado del menú principal simplificado."""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """
        Genera el menú principal simplificado.
        
        Opciones:
        - Mis Claves VPN: Ver y gestionar claves
        - Nueva Clave: Crear nueva clave VPN
        - Comprar GB: Ver paquetes y comprar
        - Mis Datos: Ver consumo
        - Ayuda: Información básica
        
        Returns:
            InlineKeyboardMarkup: Teclado del menú principal
        """
        keyboard = [
            [
                InlineKeyboardButton("🔑 Mis Claves VPN", callback_data="show_keys"),
                InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key")
            ],
            [
                InlineKeyboardButton("📦 Comprar GB", callback_data="buy_data"),
                InlineKeyboardButton("💾 Mis Datos", callback_data="show_usage")
            ],
            [
                InlineKeyboardButton("❓ Ayuda", callback_data="help")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def main_menu_with_admin(admin_id: int, current_user_id: int) -> InlineKeyboardMarkup:
        """
        Genera el menú principal con opción de admin si corresponde.
        
        Args:
            admin_id: ID del administrador
            current_user_id: ID del usuario actual
            
        Returns:
            InlineKeyboardMarkup: Teclado del menú principal
        """
        keyboard = MainMenuKeyboard.main_menu()
        
        # Agregar opción de admin si es el administrador
        if str(current_user_id) == str(admin_id):
            keyboard.keyboard.insert(0, [
                InlineKeyboardButton("🔧 Admin", callback_data="admin_panel")
            ])
        
        return keyboard
```

**Step 3: Escribir __init__.py**

```python
"""
Keyboards del bot uSipipo.

Author: uSipipo Team
Version: 1.0.0
"""

from .main_menu import MainMenuKeyboard

__all__ = ["MainMenuKeyboard"]
```

**Step 4: Commit**

```bash
git add telegram_bot/keyboards/
git commit -m "feat: add main menu keyboard module"
```

---

### Task 2: Actualizar mensajes de bienvenida

**Files:**
- Modify: `telegram_bot/features/user_management/messages_user_management.py`

**Step 1: Agregar mensajes de bienvenida para el nuevo menú**

Leer el archivo actual y agregar:

```python
class WelcomeMessages:
    """Mensajes de bienvenida del menú principal."""
    
    NEW_USER_SIMPLIFIED = (
        "🎉 *¡Bienvenido a uSipipo!*\n\n"
        "Tu VPN personal está lista para usar.\n\n"
        "📱 *Usa el menú de abajo para:*\n"
        "• Ver tus claves VPN activas\n"
        "• Crear nuevas claves\n"
        "• Comprar más datos\n"
        "• Ver tu consumo\n\n"
        "¿Necesitas ayuda? Presiona el botón ❓"
    )
    
    RETURNING_USER_SIMPLIFIED = (
        "👋 *¡Bienvenido de vuelta!*\n\n"
        "Usa el menú de abajo para gestionar tu VPN:\n"
    )
```

**Step 2: Commit**

```bash
git add telegram_bot/features/user_management/messages_user_management.py
git commit -m "feat: add simplified welcome messages"
```

---

### Task 3: Actualizar handler de /start

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py:40-98`

**Step 1: Modificar el start_handler para usar el nuevo teclado**

Cambiar en la línea 89:
```python
# Antes:
reply_markup=UserManagementKeyboards.main_menu(is_admin=is_admin),

# Después:
from telegram_bot.keyboards import MainMenuKeyboard
reply_markup=MainMenuKeyboard.main_menu_with_admin(
    admin_id=int(settings.ADMIN_ID),
    current_user_id=user.id
)
```

También actualizar las líneas 96-98 para usar el nuevo teclado:
```python
# En el bloque de error:
reply_markup=MainMenuKeyboard.main_menu()
```

**Step 2: Commit**

```bash
git add telegram_bot/features/user_management/handlers_user_management.py
git commit -m "feat: update start handler to use simplified main menu"
```

---

### Task 4: Implementar callbacks de navegación

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py`

**Step 1: Agregar método para manejar callback del menú principal**

Agregar nuevo método en UserManagementHandler:

```python
async def handle_main_menu_callback(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja los callbacks del menú principal.
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = update.effective_user.id
    
    if callback_data == "show_keys":
        # Delegar a VpnKeysHandler
        from telegram_bot.features.vpn_keys.handlers_vpn_keys import VpnKeysHandler
        # ... (implementar redirección)
        
    elif callback_data == "create_key":
        # Delegar a creación de clave
        pass
        
    elif callback_data == "buy_data":
        # Delegar a PaymentsHandler
        from telegram_bot.features.payments.handlers_payments import PaymentsHandler
        # ... (implementar redirección)
        
    elif callback_data == "show_usage":
        # Mostrar consumo de datos
        pass
        
    elif callback_data == "help":
        # Mostrar ayuda
        await query.edit_message_text(
            text=UserManagementMessages.HELP_TEXT,
            reply_markup=MainMenuKeyboard.main_menu()
        )
```

**Step 2: Registrar los nuevos callback handlers**

En el archivo de inicialización de handlers, agregar:

```python
CallbackQueryHandler(handler.handle_main_menu_callback, pattern="^(show_keys|create_key|buy_data|show_usage|help|admin_panel)$")
```

**Step 3: Commit**

```bash
git add telegram_bot/features/user_management/handlers_user_management.py
git commit -m "feat: add main menu callback handlers"
```

---

### Task 5: Actualizar navegación existente

**Files:**
- Modify: `telegram_bot/common/keyboards.py:252-282`
- Modify: `telegram_bot/features/user_management/keyboards_user_management.py:15-45`

**Step 1: Actualizar el método main_menu en CommonKeyboards**

Mantener backwards compatibility agregando una versión simplificada o referenciando al nuevo módulo.

**Step 2: Commit**

```bash
git add telegram_bot/common/keyboards.py telegram_bot/features/user_management/keyboards_user_management.py
git commit -m "refactor: update existing keyboards for consistency"
```

---

### Task 6: Verificar integración completa

**Step 1: Probar el flujo completo**

```bash
# Iniciar el bot y verificar:
# 1. Comando /start muestra el nuevo menú
# 2. Todos los botones responden
# 3. La navegación vuelve al menú principal
# 4. El botón de admin aparece solo para admin
```

**Step 2: Ejecutar tests existentes**

```bash
pytest tests/ -v
```

**Step 3: Commit final**

```bash
git commit -m "fix: complete main menu integration"
```

---

## Criterios de Aceptación

- [ ] Menú se muestra al iniciar con /start
- [ ] Todos los botones responden (show_keys, create_key, buy_data, show_usage, help)
- [ ] Botón de Admin aparece solo para el administrador
- [ ] Navegación vuelve al menú principal correctamente
- [ ] Tests existentes pasan
- [ ] No hay regresiones en funcionalidad existente
