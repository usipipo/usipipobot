# Centro de Administración Completo - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar el centro de administración 100% funcional con todas las características de gestión de usuarios, llaves VPN, tickets, configuración y mantenimiento.

**Architecture:** Clean Architecture / Hexagonal con separación de capas. Los handlers de Telegram consumen servicios de aplicación que a su vez usan repositorios de infraestructura. Cada funcionalidad administrativa se implementa con callbacks y estados de conversación.

**Tech Stack:** Python 3.11, python-telegram-bot, SQLAlchemy async, PostgreSQL, Pydantic

---

## Analysis Summary

### Current State (What exists)
- Menu admin básico con navegación
- Ver lista de usuarios (limitado a 20)
- Ver lista de llaves VPN (limitado a 20)  
- Estado del servidor básico
- Ver logs del sistema

### What's Missing (The gaps)
1. **Gestión de usuarios**: No hay detalles, acciones, paginación
2. **Gestión de llaves**: No hay detalles, acciones, paginación
3. **Tickets admin**: No conectado al menú admin
4. **Configuración**: No implementado
5. **Mantenimiento**: No implementado
6. **Dashboard métricas**: Parcialmente implementado

---

## Issues Breakdown

### Issue #1: Gestión Completa de Usuarios
- Ver detalles de usuario específico
- Suspender/reactivar usuarios
- Eliminar usuarios (con confirmación)
- Asignar roles (admin/user)
- Paginación de lista de usuarios
- Buscar usuarios

### Issue #2: Gestión Completa de Llaves VPN
- Ver detalles de llave específica
- Suspender/reactivar llaves
- Eliminar llaves (con confirmación)
- Ver uso de datos en tiempo real
- Paginación de lista de llaves
- Filtrar por tipo (WireGuard/Outline)

### Issue #3: Integración de Tickets Admin
- Conectar tickets al menú admin
- Ver todos los tickets abiertos
- Responder tickets
- Cerrar tickets
- Cambiar prioridad

### Issue #4: Sistema de Configuración
- Ver configuración actual
- Modificar límites de datos
- Configurar servidores VPN
- Gestión de administradores

### Issue #5: Sistema de Mantenimiento
- Reiniciar servicios VPN
- Limpiar caché/logs
- Crear backups de BD
- Modo mantenimiento (broadcast)

### Issue #6: Dashboard y Métricas
- Estadísticas completas
- Métricas de negocio
- Reportes de uso
- Gráficos de actividad

---

## Implementation Order

1. **Issue #1**: Gestión de Usuarios (fundacional)
2. **Issue #2**: Gestión de Llaves VPN (depende de #1)
3. **Issue #3**: Integración Tickets (independiente)
4. **Issue #6**: Dashboard Métricas (usa datos de #1 y #2)
5. **Issue #4**: Configuración (avanzado)
6. **Issue #5**: Mantenimiento (avanzado)

---

## Detailed Tasks

### Issue #1: Gestión Completa de Usuarios

#### Task 1.1: Implementar user_details handler
**Files:**
- Modify: `telegram_bot/features/admin/handlers_admin.py`
- Modify: `telegram_bot/features/admin/keyboards_admin.py`
- Modify: `telegram_bot/features/admin/messages_admin.py`

**Step 1: Add show_user_details handler**
```python
@admin_required
@admin_spinner_callback
async def show_user_details(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    spinner_message_id: int = None,
):
    query = update.callback_query
    await self._safe_answer_query(query)
    admin_id = update.effective_user.id
    
    user_id = int(query.data.split("_")[-1])
    
    try:
        user = await self.service.get_user_by_id(user_id)
        if not user:
            await SpinnerManager.replace_spinner_with_message(
                update, context, spinner_message_id,
                text=AdminMessages.Error.USER_NOT_FOUND,
                reply_markup=AdminKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return ADMIN_MENU
        
        keys = await self.service.get_user_keys(user_id)
        active_keys = [k for k in keys if k.is_active]
        
        message = AdminMessages.Users.USER_DETAILS.format(
            user_id=user.get('user_id'),
            full_name=user.get('full_name', 'N/A'),
            username=user.get('username', 'N/A'),
            created_at=user.get('created_at', 'N/A'),
            status=user.get('status', 'N/A'),
            balance=user.get('balance_stars', 0),
            total_deposited=user.get('total_deposited', 0),
            referral_credits=user.get('referral_credits', 0),
            keys_count=len(active_keys),
        )
        
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id,
            text=message,
            reply_markup=AdminKeyboards.user_actions(
                user_id, 
                user.get('status') == 'active'
            ),
            parse_mode="Markdown",
        )
        return VIEWING_USERS
        
    except Exception as e:
        await self._handle_error(update, context, e, "show_user_details")
        return ADMIN_MENU
```

**Step 2: Add suspend/reactivate user handlers**
```python
@admin_required
@admin_spinner_callback
async def suspend_user(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    spinner_message_id: int = None,
):
    query = update.callback_query
    await self._safe_answer_query(query)
    admin_id = update.effective_user.id
    
    user_id = int(query.data.split("_")[-1])
    
    try:
        result = await self.service.update_user_status(user_id, "suspended")
        
        if result.success:
            message = AdminMessages.Users.USER_BANNED
        else:
            message = AdminMessages.Error.OPERATION_FAILED.format(error=result.message)
        
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id,
            text=message,
            reply_markup=AdminKeyboards.back_to_menu(),
            parse_mode="Markdown",
        )
        return ADMIN_MENU
        
    except Exception as e:
        await self._handle_error(update, context, e, "suspend_user")
        return ADMIN_MENU

@admin_required
@admin_spinner_callback
async def reactivate_user(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    spinner_message_id: int = None,
):
    query = update.callback_query
    await self._safe_answer_query(query)
    admin_id = update.effective_user.id
    
    user_id = int(query.data.split("_")[-1])
    
    try:
        result = await self.service.update_user_status(user_id, "active")
        
        if result.success:
            message = AdminMessages.Users.USER_UNBANNED
        else:
            message = AdminMessages.Error.OPERATION_FAILED.format(error=result.message)
        
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id,
            text=message,
            reply_markup=AdminKeyboards.back_to_menu(),
            parse_mode="Markdown",
        )
        return ADMIN_MENU
        
    except Exception as e:
        await self._handle_error(update, context, e, "reactivate_user")
        return ADMIN_MENU
```

**Step 3: Add delete user with confirmation**
```python
@admin_required
async def confirm_delete_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await self._safe_answer_query(query)
    
    user_id = int(query.data.split("_")[-1])
    
    await self._safe_edit_message(
        query,
        context,
        text=AdminMessages.Users.CONFIRM_DELETE.format(user_id=user_id),
        reply_markup=AdminKeyboards.confirmation("delete_user", user_id),
        parse_mode="Markdown",
    )
    return CONFIRMING_DELETE

@admin_required
@admin_spinner_callback
async def execute_delete_user(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    spinner_message_id: int = None,
):
    query = update.callback_query
    await self._safe_answer_query(query)
    
    user_id = int(query.data.split("_")[-1])
    
    try:
        result = await self.service.delete_user(user_id)
        
        if result.success:
            message = AdminMessages.Users.USER_DELETED
        else:
            message = AdminMessages.Error.OPERATION_FAILED.format(error=result.message)
        
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id,
            text=message,
            reply_markup=AdminKeyboards.back_to_menu(),
            parse_mode="Markdown",
        )
        return ADMIN_MENU
        
    except Exception as e:
        await self._handle_error(update, context, e, "execute_delete_user")
        return ADMIN_MENU
```

**Step 4: Update keyboards with pagination**
```python
@staticmethod
def users_list_paginated(users: List[dict], page: int, total_pages: int) -> InlineKeyboardMarkup:
    keyboard = []
    
    for user in users:
        status_icon = "✅" if user.get('status') == 'active' else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status_icon} {user.get('full_name', 'N/A')} ({user.get('user_id')})",
                callback_data=f"user_details_{user.get('user_id')}"
            )
        ])
    
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"users_page_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("➡️ Siguiente", callback_data=f"users_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔙 Menú Admin", callback_data="admin")])
    
    return InlineKeyboardMarkup(keyboard)
```

**Step 5: Register handlers in conversation handler**
Add patterns to `get_admin_conversation_handler()` for all new callbacks.

**Step 6: Test with pytest**
```bash
pytest tests/telegram_bot/features/admin/ -v
```

**Step 7: Commit**
```bash
git add -A && git commit -m "feat(admin): complete user management with actions and pagination"
```

---

### Issue #2: Gestión Completa de Llaves VPN

#### Task 2.1: Implementar key_details handler
**Files:**
- Modify: `telegram_bot/features/admin/handlers_admin.py`
- Modify: `telegram_bot/features/admin/keyboards_admin.py`
- Modify: `telegram_bot/features/admin/messages_admin.py`
- Modify: `application/services/admin_service.py`

**Step 1: Add show_key_details handler**
```python
@admin_required
@admin_spinner_callback
async def show_key_details(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    spinner_message_id: int = None,
):
    query = update.callback_query
    await self._safe_answer_query(query)
    admin_id = update.effective_user.id
    
    key_id = query.data.split("_")[-1]
    
    try:
        keys = await self.service.get_all_keys(current_user_id=admin_id)
        key = next((k for k in keys if k.get('key_id') == key_id), None)
        
        if not key:
            await SpinnerManager.replace_spinner_with_message(
                update, context, spinner_message_id,
                text=AdminMessages.Error.KEY_NOT_FOUND,
                reply_markup=AdminKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return ADMIN_MENU
        
        usage_stats = await self.service.get_key_usage_stats(key_id)
        data_used_gb = round(usage_stats.get('data_used', 0) / (1024**3), 2)
        data_limit_gb = round(key.get('data_limit', 0) / (1024**3), 2)
        
        message = AdminMessages.Keys.KEY_DETAILS.format(
            key_id=key_id[:8],
            name=key.get('key_name', 'N/A'),
            user_id=key.get('user_id'),
            type=key.get('key_type', 'N/A'),
            server=key.get('server_status', 'N/A'),
            usage=f"{data_used_gb}/{data_limit_gb}",
            status="Activa" if key.get('is_active') else "Inactiva",
            created_at=key.get('created_at', 'N/A'),
            expires_at=key.get('expires_at', 'N/A'),
        )
        
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id,
            text=message,
            reply_markup=AdminKeyboards.key_actions(key_id, key.get('is_active')),
            parse_mode="Markdown",
        )
        return VIEWING_KEYS
        
    except Exception as e:
        await self._handle_error(update, context, e, "show_key_details")
        return ADMIN_MENU
```

**Step 2: Add suspend/reactivate key handlers**
Similar structure to user handlers.

**Step 3: Add delete key with confirmation**
Similar structure to user delete.

**Step 4: Update keyboards with key type filter**
```python
@staticmethod
def keys_filter_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🔑 Todas", callback_data="keys_filter_all"),
            InlineKeyboardButton("⚡ WireGuard", callback_data="keys_filter_wireguard"),
            InlineKeyboardButton("🔵 Outline", callback_data="keys_filter_outline"),
        ],
        [InlineKeyboardButton("🔙 Menú Admin", callback_data="admin")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

**Step 5: Register all new handlers**

**Step 6: Test with pytest**

**Step 7: Commit**
```bash
git add -A && git commit -m "feat(admin): complete VPN key management with actions and filtering"
```

---

### Issue #3: Integración de Tickets Admin

#### Task 3.1: Conectar tickets al menú admin
**Files:**
- Modify: `telegram_bot/features/admin/handlers_admin.py`
- Modify: `telegram_bot/features/admin/keyboards_admin.py`
- No changes needed to ticket handlers (already implemented)

**Step 1: Add admin_tickets callback to main menu**
The callback `admin_tickets` already exists in the keyboard. Need to ensure the handler is registered.

**Step 2: Verify ticket handler registration**
Check that `admin_tickets` pattern is handled by `TicketHandler.admin_list_tickets`.

**Step 3: Add back to admin menu from tickets**
Modify `TicketKeyboards` to include "Back to Admin" option.

**Step 4: Test the flow**

**Step 5: Commit**
```bash
git add -A && git commit -m "feat(admin): integrate ticket management into admin center"
```

---

### Issue #4: Sistema de Configuración

#### Task 4.1: Implementar settings handlers
**Files:**
- Modify: `telegram_bot/features/admin/handlers_admin.py`
- Modify: `telegram_bot/features/admin/keyboards_admin.py`
- Modify: `telegram_bot/features/admin/messages_admin.py`
- Modify: `application/services/admin_service.py`

**Step 1: Add show_settings handler**
```python
@admin_required
async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await self._safe_answer_query(query)
    
    await self._safe_edit_message(
        query,
        context,
        text=AdminMessages.Settings.HEADER,
        reply_markup=AdminKeyboards.settings_menu(),
        parse_mode="Markdown",
    )
    return ADMIN_MENU
```

**Step 2: Add server settings handler**
```python
@admin_required
@admin_spinner_callback
async def show_server_settings(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    spinner_message_id: int = None,
):
    query = update.callback_query
    await self._safe_answer_query(query)
    admin_id = update.effective_user.id
    
    try:
        server_status = await self.service.get_server_status()
        
        wg = server_status.get('wireguard', {})
        ol = server_status.get('outline', {})
        
        message = AdminMessages.Settings.SERVERS.format(
            wg_status="✅ Online" if wg.get('is_healthy') else "❌ Offline",
            wg_keys=wg.get('total_keys', 0),
            ol_status="✅ Online" if ol.get('is_healthy') else "❌ Offline",
            ol_keys=ol.get('total_keys', 0),
        )
        
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id,
            text=message,
            reply_markup=AdminKeyboards.back_to_settings(),
            parse_mode="Markdown",
        )
        return ADMIN_MENU
        
    except Exception as e:
        await self._handle_error(update, context, e, "show_server_settings")
        return ADMIN_MENU
```

**Step 3: Add limits settings handler**

**Step 4: Add admin management handler**

**Step 5: Register all handlers**

**Step 6: Test**

**Step 7: Commit**
```bash
git add -A && git commit -m "feat(admin): add configuration system"
```

---

### Issue #5: Sistema de Mantenimiento

#### Task 5.1: Implementar maintenance handlers
**Files:**
- Modify: `telegram_bot/features/admin/handlers_admin.py`
- Modify: `telegram_bot/features/admin/keyboards_admin.py`
- Modify: `telegram_bot/features/admin/messages_admin.py`
- Create: `infrastructure/jobs/maintenance_service.py`

**Step 1: Add show_maintenance handler**
```python
@admin_required
async def show_maintenance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await self._safe_answer_query(query)
    
    await self._safe_edit_message(
        query,
        context,
        text=AdminMessages.Maintenance.HEADER,
        reply_markup=AdminKeyboards.maintenance_menu(),
        parse_mode="Markdown",
    )
    return ADMIN_MENU
```

**Step 2: Add restart services handler**
```python
@admin_required
@admin_spinner_callback
async def restart_vpn_services(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    spinner_message_id: int = None,
):
    query = update.callback_query
    await self._safe_answer_query(query)
    admin_id = update.effective_user.id
    
    try:
        results = await self.service.restart_vpn_services()
        
        message = AdminMessages.Maintenance.RESTART_RESULTS.format(
            wireguard="✅" if results.get('wireguard') else "❌",
            outline="✅" if results.get('outline') else "❌",
        )
        
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id,
            text=message,
            reply_markup=AdminKeyboards.back_to_maintenance(),
            parse_mode="Markdown",
        )
        return ADMIN_MENU
        
    except Exception as e:
        await self._handle_error(update, context, e, "restart_vpn_services")
        return ADMIN_MENU
```

**Step 3: Add clear cache handler**

**Step 4: Add create backup handler**

**Step 5: Add maintenance mode handler**

**Step 6: Register all handlers**

**Step 7: Test**

**Step 8: Commit**
```bash
git add -A && git commit -m "feat(admin): add maintenance system"
```

---

### Issue #6: Dashboard y Métricas

#### Task 6.1: Implementar dashboard completo
**Files:**
- Modify: `telegram_bot/features/admin/handlers_admin.py`
- Modify: `telegram_bot/features/admin/keyboards_admin.py`
- Modify: `telegram_bot/features/admin/messages_admin.py`
- Modify: `application/services/admin_service.py`

**Step 1: Enhance show_server_status with dashboard**
```python
@admin_required
@admin_spinner_callback
async def show_dashboard(
    self,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    spinner_message_id: int = None,
):
    query = update.callback_query
    await self._safe_answer_query(query)
    admin_id = update.effective_user.id
    
    try:
        stats = await self.service.get_dashboard_stats(current_user_id=admin_id)
        
        message = AdminMessages.Dashboard.FULL.format(
            total_users=stats.get('total_users', 0),
            active_users=stats.get('active_users', 0),
            total_keys=stats.get('total_keys', 0),
            active_keys=stats.get('active_keys', 0),
            wireguard_keys=stats.get('wireguard_keys', 0),
            outline_keys=stats.get('outline_keys', 0),
            total_revenue=stats.get('total_revenue', 0),
            new_users_today=stats.get('new_users_today', 0),
            keys_created_today=stats.get('keys_created_today', 0),
            server_status=stats.get('server_status_text', 'N/A'),
            generated_at=stats.get('generated_at', 'N/A'),
        )
        
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id,
            text=message,
            reply_markup=AdminKeyboards.dashboard_actions(),
            parse_mode="Markdown",
        )
        return ADMIN_MENU
        
    except Exception as e:
        await self._handle_error(update, context, e, "show_dashboard")
        return ADMIN_MENU
```

**Step 2: Add messages for dashboard**
```python
class Dashboard:
    FULL = (
        "📊 **Dashboard de Administración**\n\n"
        "👥 **Usuarios:**\n"
        "  • Total: {total_users}\n"
        "  • Activos: {active_users}\n"
        "  • Nuevos hoy: {new_users_today}\n\n"
        "🔑 **Llaves VPN:**\n"
        "  • Total: {total_keys}\n"
        "  • Activas: {active_keys}\n"
        "  • Creadas hoy: {keys_created_today}\n"
        "  • WireGuard: {wireguard_keys}\n"
        "  • Outline: {outline_keys}\n\n"
        "💰 **Ingresos:**\n"
        "  • Total: {total_revenue} ⭐\n\n"
        "🖥️ **Servidores:** {server_status}\n\n"
        "_Actualizado: {generated_at}_"
    )
```

**Step 3: Add export stats handler**

**Step 4: Register handlers**

**Step 5: Test**

**Step 6: Commit**
```bash
git add -A && git commit -m "feat(admin): add complete dashboard with metrics"
```

---

## Final Integration

### After all issues are complete:

**Step 1: Run full test suite**
```bash
pytest tests/ -v --cov=.
```

**Step 2: Check code style**
```bash
flake8 . && black --check .
```

**Step 3: Manual testing**
- Test all admin flows
- Test pagination
- Test confirmations
- Test error handling

**Step 4: Final commit**
```bash
git add -A && git commit -m "feat(admin): complete admin center implementation"
```

**Step 5: Push to develop**
```bash
git push origin develop
```

---

## File Summary

| File | Changes |
|------|---------|
| `telegram_bot/features/admin/handlers_admin.py` | Add 25+ new handlers |
| `telegram_bot/features/admin/keyboards_admin.py` | Add 10+ new keyboards |
| `telegram_bot/features/admin/messages_admin.py` | Add 5+ message classes |
| `application/services/admin_service.py` | Add helper methods |
| `domain/entities/admin.py` | No changes needed |
| `domain/interfaces/iadmin_service.py` | Add interface methods |
| `infrastructure/jobs/maintenance_service.py` | Create new file |
