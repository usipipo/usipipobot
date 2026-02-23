# Fix Botón "Mis Datos" No Responde Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Solucionar el bug donde el botón "💾 Mis Datos" no responde al hacer clic desde el menú principal

**Architecture:** Hacer que UserManagementHandler herede de BaseHandler y usar métodos helper actualizados para manejar correctamente callback queries

**Tech Stack:** Python, python-telegram-bot, Clean Architecture

---

## Task 1: Hacer que UserManagementHandler herede de BaseHandler

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py:35`

**Step 1: Actualizar la clase UserManagementHandler para heredar de BaseHandler**

Cambiar:
```python
class UserManagementHandler:
```

Por:
```python
from telegram_bot.common.base_handler import BaseHandler

class UserManagementHandler(BaseHandler):
```

**Step 2: Actualizar el constructor para llamar a super().__init__()**

Modificar el constructor actual (líneas 38-52):
```python
def __init__(
    self,
    vpn_service: VpnService,
    user_profile_service: Optional[UserProfileService] = None,
):
    super().__init__(vpn_service, "VpnService")
    self.vpn_service = vpn_service
    self.user_profile_service = user_profile_service
    logger.info("👤 UserManagementHandler inicializado")
```

**Step 3: Verificar que el archivo importa BaseHandler**

Agregar import al inicio del archivo:
```python
from telegram_bot.common.base_handler import BaseHandler
```

---

## Task 2: Actualizar status_handler para usar _reply_message

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py:220-306`

**Step 1: Actualizar la firma del método para recibir context**

Cambiar:
```python
async def status_handler(
    self,
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
    admin_service: Optional[AdminService] = None,
):
```

Por:
```python
async def status_handler(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    admin_service: Optional[AdminService] = None,
):
```

**Step 2: Actualizar la lógica de respuesta usando _reply_message**

Reemplazar el bloque de respuesta (líneas 273-292):
```python
# Determinar si es admin para el menú
is_admin_menu = telegram_id == int(settings.ADMIN_ID)

# Verificar si hay mensaje para responder
if update.message:
    await update.message.reply_text(
        text=text,
        reply_markup=UserManagementKeyboards.main_menu(
            is_admin=is_admin_menu
        ),
        parse_mode="Markdown",
    )
elif update.callback_query:
    await update.callback_query.message.edit_text(
        text=text,
        reply_markup=UserManagementKeyboards.main_menu(
            is_admin=is_admin_menu
        ),
        parse_mode="Markdown",
    )
```

Por:
```python
is_admin_menu = telegram_id == int(settings.ADMIN_ID)
await self._reply_message(
    update,
    text=text,
    reply_markup=UserManagementKeyboards.main_menu(is_admin=is_admin_menu),
    parse_mode="Markdown",
    context=context,
)
```

**Step 3: Actualizar el manejo de errores para usar _reply_message**

Reemplazar el bloque de error (líneas 294-306):
```python
except (AttributeError, ValueError, KeyError) as e:
    logger.error(f"❌ Error en status_handler para usuario {telegram_id}: {e}")
    if update.message:
        await update.message.reply_text(
            text=UserManagementMessages.Error.STATUS_FAILED,
            reply_markup=UserManagementKeyboards.main_menu(),
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            text=UserManagementMessages.Error.STATUS_FAILED,
            reply_markup=UserManagementKeyboards.main_menu(),
        )
```

Por:
```python
except (AttributeError, ValueError, KeyError) as e:
    logger.error(f"❌ Error en status_handler para usuario {telegram_id}: {e}")
    await self._reply_message(
        update,
        text=UserManagementMessages.Error.STATUS_FAILED,
        reply_markup=UserManagementKeyboards.main_menu(),
        parse_mode="Markdown",
        context=context,
    )
```

---

## Task 3: Actualizar main_menu_callback para pasar context a status_handler

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py:180-185`

**Step 1: Actualizar la llamada a status_handler en show_usage callback**

Cambiar:
```python
elif callback_data == "show_usage":
    from telegram_bot.features.user_management.handlers_user_management import (
        UserManagementHandler,
    )

    await self.status_handler(update, _context)
```

Por:
```python
elif callback_data == "show_usage":
    await self.status_handler(update, _context)
```

**Step 2: Agregar logging para debugging**

Agregar antes de la llamada a status_handler:
```python
elif callback_data == "show_usage":
    logger.info(f"📊 Mostrando estado para usuario {user_id}")
    await self.status_handler(update, _context)
```

---

## Task 4: Actualizar info_handler para usar _reply_message

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py:308-411`

**Step 1: Actualizar la firma del método**

Cambiar `_context` por `context`:
```python
async def info_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
```

**Step 2: Actualizar respuestas usando _reply_message**

Reemplazar:
```python
await message.reply_text(
    text=text,
    reply_markup=UserManagementKeyboards.main_menu(is_admin=is_admin_menu),
    parse_mode="Markdown",
)
```

Por:
```python
await self._reply_message(
    update,
    text=text,
    reply_markup=UserManagementKeyboards.main_menu(is_admin=is_admin_menu),
    parse_mode="Markdown",
    context=context,
)
```

**Step 3: Actualizar manejo de errores**

Similar a status_handler, usar _reply_message en los bloques de error.

---

## Task 5: Actualizar history_handler para usar _reply_message

**Files:**
- Modify: `telegram_bot/features/user_management/handlers_user_management.py:413-477`

**Step 1: Actualizar la firma del método**

Cambiar `_context` por `context`.

**Step 2: Actualizar todas las respuestas usando _reply_message**

Similar a los handlers anteriores.

---

## Task 6: Verificar y ejecutar tests

**Step 1: Ejecutar tests existentes**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

**Step 2: Verificar que no hay errores de importación**

Run: `python -c "from telegram_bot.features.user_management.handlers_user_management import UserManagementHandler; print('OK')"`
Expected: OK

**Step 3: Verificar linting**

Run: `flake8 telegram_bot/features/user_management/ --max-line-length=100`

---

## Task 7: Commit y crear PR

**Step 1: Commit de los cambios**

```bash
git add telegram_bot/features/user_management/handlers_user_management.py
git commit -m "fix: Mis Datos button not responding from main menu

Problem: When user clicks '💾 Mis Datos' button from main menu,
nothing happens. The callback is not handled correctly.

Root cause: UserManagementHandler doesn't inherit from BaseHandler
and status_handler doesn't use the updated _reply_message helper
that properly handles callback queries.

Solution:
- Make UserManagementHandler inherit from BaseHandler
- Update status_handler, info_handler, history_handler to use _reply_message
- Remove dead code in show_usage callback handler
- Add logging for debugging

Similar issue was fixed in commit 9105b3c for admin panel.

Fixes #147"
```

**Step 2: Push to origin**

```bash
git push origin develop
```

---

## Verification Checklist

- [ ] UserManagementHandler inherits from BaseHandler
- [ ] status_handler uses _reply_message with context parameter
- [ ] info_handler uses _reply_message with context parameter
- [ ] history_handler uses _reply_message with context parameter
- [ ] Dead code removed from show_usage callback
- [ ] All tests pass
- [ ] No linting errors
- [ ] Bot responds correctly to "Mis Datos" button click
