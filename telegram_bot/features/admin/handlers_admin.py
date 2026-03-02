"""
Handlers para panel administrativo de uSipipo.

Author: uSipipo Team
Version: 4.0.0 - Removed ticket system
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from application.services.admin_service import AdminService
from config import settings
from telegram_bot.common.base_handler import BaseConversationHandler
from telegram_bot.common.decorators import admin_required
from utils.logger import logger
from utils.spinner import SpinnerManager, admin_spinner_callback, with_spinner
from utils.telegram_utils import escape_markdown

from .keyboards_admin import AdminKeyboards
from .messages_admin import AdminMessages

ADMIN_MENU = 0
VIEWING_USERS = 1
VIEWING_USER_DETAILS = 2
VIEWING_KEYS = 3
VIEWING_KEY_DETAILS = 4
CONFIRMING_USER_DELETE = 5
CONFIRMING_KEY_DELETE = 6
VIEWING_SETTINGS = 7
VIEWING_MAINTENANCE = 8

USERS_PER_PAGE = 10
KEYS_PER_PAGE = 10


class AdminHandler(BaseConversationHandler):
    """Handler para funciones administrativas."""

    def __init__(self, admin_service: AdminService):
        super().__init__(admin_service, "AdminService")
        logger.info("🔧 AdminHandler inicializado")

    def _is_admin(self, user_id: int) -> bool:
        """Verifica si el usuario es administrador."""
        return str(user_id) == str(settings.ADMIN_ID)

    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú de administración."""
        user = update.effective_user
        if user is None:
            return ConversationHandler.END

        if not self._is_admin(user.id):
            await self._reply_message(
                update,
                "⚠️ Acceso denegado. Función solo para administradores.",
                parse_mode="Markdown",
                context=context,
            )
            return ConversationHandler.END

        await self._reply_message(
            update,
            text=AdminMessages.Menu.MAIN,
            reply_markup=AdminKeyboards.main_menu(),
            parse_mode="Markdown",
            context=context,
        )
        if context.user_data is not None:
            context.user_data.pop("users_page", None)
            context.user_data.pop("keys_page", None)
            context.user_data.pop("keys_filter", None)
        return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def show_users(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra lista de usuarios con paginación."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        page = 1
        if context.user_data is not None and context.user_data.get("users_page"):
            page = context.user_data["users_page"]

        try:
            result = await self.service.get_users_paginated(
                page=page, per_page=USERS_PER_PAGE, current_user_id=admin_id
            )
            users = result.get("users", [])
            total_pages = result.get("total_pages", 1)
            total_users = result.get("total_users", 0)

            # Validate and correct page number if out of bounds
            if page < 1:
                page = 1
            elif total_pages > 0 and page > total_pages:
                page = total_pages

            # Re-fetch if page was corrected and we got empty results due to invalid page
            if not users and page != result.get("page", page):
                result = await self.service.get_users_paginated(
                    page=page, per_page=USERS_PER_PAGE, current_user_id=admin_id
                )
                users = result.get("users", [])
                total_pages = result.get("total_pages", 1)

            if not users:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text=AdminMessages.Users.NO_USERS,
                    reply_markup=AdminKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
                return ADMIN_MENU

            message = (
                AdminMessages.Users.HEADER + f"📊 Total: {total_users} usuarios\n\n"
            )
            keyboard = AdminKeyboards.users_list_paginated(users, page, total_pages)

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            return VIEWING_USERS

        except Exception as e:
            await self._handle_error(update, context, e, "show_users")
            return ADMIN_MENU

    @admin_required
    async def users_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Navega entre páginas de usuarios."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return ADMIN_MENU
        page = int(query.data.split("_")[-1])
        if context.user_data is not None:
            context.user_data["users_page"] = page

        return await self._show_users_page(update, context, page)

    async def _show_users_page(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int
    ):
        """Muestra una página específica de usuarios."""
        query = update.callback_query
        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        try:
            result = await self.service.get_users_paginated(
                page=page, per_page=USERS_PER_PAGE, current_user_id=admin_id
            )
            users = result.get("users", [])
            total_pages = result.get("total_pages", 1)
            total_users = result.get("total_users", 0)

            # Validate and correct page number if out of bounds
            if page < 1:
                page = 1
            elif total_pages > 0 and page > total_pages:
                page = total_pages

            # Re-fetch if page was corrected and we got empty results due to invalid page
            if not users and page != result.get("page", page):
                result = await self.service.get_users_paginated(
                    page=page, per_page=USERS_PER_PAGE, current_user_id=admin_id
                )
                users = result.get("users", [])
                total_pages = result.get("total_pages", 1)

            if not users:
                await self._safe_edit_message(
                    query,
                    context,
                    text=AdminMessages.Users.NO_USERS,
                    reply_markup=AdminKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
                return ADMIN_MENU

            message = (
                AdminMessages.Users.HEADER + f"📊 Total: {total_users} usuarios\n\n"
            )
            keyboard = AdminKeyboards.users_list_paginated(users, page, total_pages)

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            return VIEWING_USERS

        except Exception as e:
            await self._handle_error(update, context, e, "_show_users_page")
            return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def show_user_details(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra detalles de un usuario específico."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        if query is None or query.data is None:
            return ADMIN_MENU
        user_id = int(query.data.split("_")[-1])

        try:
            user = await self.service.get_user_by_id(user_id)
            if not user:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text=AdminMessages.Error.USER_NOT_FOUND,
                    reply_markup=AdminKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
                return ADMIN_MENU

            keys = await self.service.get_user_keys(user_id)
            active_keys = [k for k in keys if k.is_active]

            created_at = user.get("created_at")
            if created_at:
                created_at = (
                    created_at.strftime("%Y-%m-%d %H:%M")
                    if hasattr(created_at, "strftime")
                    else str(created_at)[:16]
                )
            else:
                created_at = "N/A"

            message = AdminMessages.Users.USER_DETAILS.format(
                user_id=user.get("user_id", user_id),
                full_name=user.get("full_name", "N/A"),
                username=user.get("username", "N/A"),
                created_at=created_at,
                status=user.get("status", "N/A").upper(),
                balance=user.get("balance_stars", 0),
                total_deposited=user.get("total_deposited", 0),
                referral_credits=user.get("referral_credits", 0),
                keys_count=len(active_keys),
            )

            is_active = user.get("status", "").lower() == "active"

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.user_actions(user_id, is_active),
                parse_mode="Markdown",
            )
            if context.user_data is not None:
                context.user_data["viewing_user_id"] = user_id
            return VIEWING_USER_DETAILS

        except Exception as e:
            await self._handle_error(update, context, e, "show_user_details")
            return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def suspend_user(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Suspende un usuario."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return ADMIN_MENU
        user_id = int(query.data.split("_")[-1])

        try:
            result = await self.service.update_user_status(user_id, "suspended")

            if result.success:
                message = AdminMessages.Users.USER_SUSPENDED
            else:
                message = AdminMessages.Error.OPERATION_FAILED.format(
                    error=result.message
                )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_users(),
                parse_mode="Markdown",
            )
            return VIEWING_USERS

        except Exception as e:
            await self._handle_error(update, context, e, "suspend_user")
            return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def reactivate_user(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Reactiva un usuario."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return ADMIN_MENU
        user_id = int(query.data.split("_")[-1])

        try:
            result = await self.service.update_user_status(user_id, "active")

            if result.success:
                message = AdminMessages.Users.USER_REACTIVATED
            else:
                message = AdminMessages.Error.OPERATION_FAILED.format(
                    error=result.message
                )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_users(),
                parse_mode="Markdown",
            )
            return VIEWING_USERS

        except Exception as e:
            await self._handle_error(update, context, e, "reactivate_user")
            return ADMIN_MENU

    @admin_required
    async def confirm_delete_user(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra confirmación para eliminar usuario."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return ADMIN_MENU
        user_id = int(query.data.split("_")[-1])
        if context.user_data is not None:
            context.user_data["delete_user_id"] = user_id

        await self._safe_edit_message(
            query,
            context,
            text=AdminMessages.Users.CONFIRM_DELETE.format(user_id=user_id),
            reply_markup=AdminKeyboards.confirmation("delete_user", user_id),
            parse_mode="Markdown",
        )
        return CONFIRMING_USER_DELETE

    @admin_required
    @admin_spinner_callback
    async def execute_delete_user(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Ejecuta la eliminación de usuario."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return ADMIN_MENU
        user_id = int(query.data.split("_")[-1])
        if context.user_data is not None:
            context.user_data.pop("delete_user_id", None)

        try:
            result = await self.service.delete_user(user_id)

            if result.success:
                message = AdminMessages.Users.USER_DELETED
            else:
                message = AdminMessages.Error.OPERATION_FAILED.format(
                    error=result.message
                )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return ADMIN_MENU

        except Exception as e:
            await self._handle_error(update, context, e, "execute_delete_user")
            return ADMIN_MENU

    @admin_required
    async def cancel_user_action(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Cancela una acción de usuario."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if context.user_data is not None:
            context.user_data.pop("delete_user_id", None)

        await self._safe_edit_message(
            query,
            context,
            text=AdminMessages.Success.OPERATION_CANCELLED,
            reply_markup=AdminKeyboards.back_to_menu(),
            parse_mode="Markdown",
        )
        return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def show_keys(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra lista de llaves VPN con paginación."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        page = context.user_data.get("keys_page", 1) if context.user_data else 1
        key_filter = (
            context.user_data.get("keys_filter", "all") if context.user_data else "all"
        )

        try:
            result = await self._get_filtered_keys(admin_id, page, key_filter)
            keys = result.get("keys", [])
            total_pages = result.get("total_pages", 1)
            total_keys = result.get("total_keys", 0)

            if not keys:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text=AdminMessages.Keys.NO_KEYS,
                    reply_markup=AdminKeyboards.keys_filter_menu(),
                    parse_mode="Markdown",
                )
                return VIEWING_KEYS

            filter_text = (
                f"🔍 Filtro: {key_filter.upper()}\n" if key_filter != "all" else ""
            )
            message = (
                AdminMessages.Keys.HEADER
                + filter_text
                + f"📊 Total: {total_keys} llaves\n\n"
            )
            keyboard = AdminKeyboards.keys_list_paginated(
                keys, page, total_pages, key_filter
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            return VIEWING_KEYS

        except Exception as e:
            await self._handle_error(update, context, e, "show_keys")
            return ADMIN_MENU

    async def _get_filtered_keys(
        self, admin_id: int, page: int, key_filter: str
    ) -> Dict:
        """Obtiene llaves filtradas con paginación."""
        all_keys = await self.service.get_all_keys(current_user_id=admin_id)

        if key_filter != "all":
            all_keys = [
                k
                for k in all_keys
                if k.get("key_type", "").lower() == key_filter.lower()
            ]

        total_keys = len(all_keys)
        total_pages = max(1, (total_keys + KEYS_PER_PAGE - 1) // KEYS_PER_PAGE)
        offset = (page - 1) * KEYS_PER_PAGE
        keys = all_keys[offset : offset + KEYS_PER_PAGE]

        return {
            "keys": keys,
            "total_pages": total_pages,
            "total_keys": total_keys,
        }

    @admin_required
    async def keys_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Navega entre páginas de llaves."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return ADMIN_MENU
        page = int(query.data.split("_")[-1])
        if context.user_data is not None:
            context.user_data["keys_page"] = page

        return await self._show_keys_page(update, context, page)

    @admin_required
    async def keys_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Filtra llaves por tipo."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return ADMIN_MENU
        key_filter = query.data.split("_")[-1]
        if context.user_data is not None:
            context.user_data["keys_filter"] = key_filter
            context.user_data["keys_page"] = 1

        return await self._show_keys_page(update, context, 1)

    async def _show_keys_page(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int
    ):
        """Muestra una página específica de llaves."""
        query = update.callback_query

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id
        key_filter = (
            context.user_data.get("keys_filter", "all") if context.user_data else "all"
        )

        try:
            result = await self._get_filtered_keys(admin_id, page, key_filter)
            keys = result.get("keys", [])
            total_pages = result.get("total_pages", 1)
            total_keys = result.get("total_keys", 0)

            if not keys:
                await self._safe_edit_message(
                    query,
                    context,
                    text=AdminMessages.Keys.NO_KEYS,
                    reply_markup=AdminKeyboards.keys_filter_menu(),
                    parse_mode="Markdown",
                )
                return VIEWING_KEYS

            filter_text = (
                f"🔍 Filtro: {key_filter.upper()}\n" if key_filter != "all" else ""
            )
            message = (
                AdminMessages.Keys.HEADER
                + filter_text
                + f"📊 Total: {total_keys} llaves\n\n"
            )
            keyboard = AdminKeyboards.keys_list_paginated(
                keys, page, total_pages, key_filter
            )

            await self._safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
            return VIEWING_KEYS

        except Exception as e:
            await self._handle_error(update, context, e, "_show_keys_page")
            return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def show_key_details(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra detalles de una llave específica."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        if query is None or query.data is None:
            return ADMIN_MENU
        key_id = query.data.split("_")[-1]

        try:
            all_keys = await self.service.get_all_keys(current_user_id=admin_id)
            key = next(
                (k for k in all_keys if str(k.get("key_id", "")) == str(key_id)), None
            )

            if not key:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text=AdminMessages.Error.KEY_NOT_FOUND,
                    reply_markup=AdminKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
                return ADMIN_MENU

            usage_stats = await self.service.get_key_usage_stats(key_id)
            data_used_gb = round(usage_stats.get("data_used", 0) / (1024**3), 2)
            data_limit_gb = round(key.get("data_limit", 0) / (1024**3), 2)

            created_at = key.get("created_at")
            if created_at:
                created_at = (
                    created_at.strftime("%Y-%m-%d %H:%M")
                    if hasattr(created_at, "strftime")
                    else str(created_at)[:16]
                )
            else:
                created_at = "N/A"

            expires_at = key.get("expires_at")
            if expires_at:
                expires_at = (
                    expires_at.strftime("%Y-%m-%d %H:%M")
                    if hasattr(expires_at, "strftime")
                    else str(expires_at)[:16]
                )
            else:
                expires_at = "Sin expiración"

            message = AdminMessages.Keys.KEY_DETAILS.format(
                key_id=str(key_id)[:8],
                name=key.get("key_name", "N/A"),
                user_id=key.get("user_id", "N/A"),
                type=key.get("key_type", "N/A").upper(),
                server=key.get("server_status", "N/A"),
                usage=f"{data_used_gb}/{data_limit_gb}",
                status="Activa" if key.get("is_active") else "Inactiva",
                created_at=created_at,
                expires_at=expires_at,
            )

            is_active = key.get("is_active", False)

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.key_actions(key_id, is_active),
                parse_mode="Markdown",
            )
            if context.user_data is not None:
                context.user_data["viewing_key_id"] = key_id
            return VIEWING_KEY_DETAILS

        except Exception as e:
            await self._handle_error(update, context, e, "show_key_details")
            return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def suspend_key(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Suspende una llave VPN."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        if query is None or query.data is None:
            return ADMIN_MENU
        key_id = query.data.split("_")[-1]

        try:
            result = await self.service.toggle_key_status(key_id, active=False)

            if result.get("success"):
                message = AdminMessages.Keys.KEY_SUSPENDED
            else:
                error = result.get("error", "Error desconocido")
                message = AdminMessages.Error.OPERATION_FAILED.format(error=error)

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_keys(),
                parse_mode="Markdown",
            )
            return VIEWING_KEYS

        except Exception as e:
            await self._handle_error(update, context, e, "suspend_key")
            return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def reactivate_key(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Reactiva una llave VPN suspendida."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        if query is None or query.data is None:
            return ADMIN_MENU
        key_id = query.data.split("_")[-1]

        try:
            result = await self.service.toggle_key_status(key_id, active=True)

            if result.get("success"):
                message = AdminMessages.Keys.KEY_REACTIVATED
            else:
                error = result.get("error", "Error desconocido")
                message = AdminMessages.Error.OPERATION_FAILED.format(error=error)

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_keys(),
                parse_mode="Markdown",
            )
            return VIEWING_KEYS

        except Exception as e:
            await self._handle_error(update, context, e, "reactivate_key")
            return ADMIN_MENU

    @admin_required
    async def confirm_delete_key(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra confirmación para eliminar llave."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return ADMIN_MENU
        key_id = query.data.split("_")[-1]
        if context.user_data is not None:
            context.user_data["delete_key_id"] = key_id

        await self._safe_edit_message(
            query,
            context,
            text=AdminMessages.Keys.CONFIRM_DELETE.format(key_id=key_id[:8]),
            reply_markup=AdminKeyboards.confirmation("delete_key", key_id),
            parse_mode="Markdown",
        )
        return CONFIRMING_KEY_DELETE

    @admin_required
    @admin_spinner_callback
    async def execute_delete_key(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Ejecuta la eliminación de llave."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        if query is None or query.data is None:
            return ADMIN_MENU
        key_id = query.data.split("_")[-1]
        if context.user_data is not None:
            context.user_data.pop("delete_key_id", None)

        try:
            result = await self.service.delete_user_key_complete(key_id)

            if result.get("success"):
                message = AdminMessages.Keys.KEY_DELETED
            else:
                error = result.get("error", "Error desconocido")
                message = AdminMessages.Error.OPERATION_FAILED.format(error=error)

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_keys(),
                parse_mode="Markdown",
            )
            return VIEWING_KEYS

        except Exception as e:
            await self._handle_error(update, context, e, "execute_delete_key")
            return ADMIN_MENU

    @admin_required
    async def cancel_key_action(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Cancela una acción de llave."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if context.user_data is not None:
            context.user_data.pop("delete_key_id", None)

        await self._safe_edit_message(
            query,
            context,
            text=AdminMessages.Success.OPERATION_CANCELLED,
            reply_markup=AdminKeyboards.back_to_keys(),
            parse_mode="Markdown",
        )
        return VIEWING_KEYS

    @admin_required
    @admin_spinner_callback
    async def show_dashboard(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra dashboard con estadísticas completas."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        # Reset pagination when viewing dashboard to avoid stale page numbers
        if context.user_data is not None:
            context.user_data["users_page"] = 1

        try:
            stats = await self.service.get_dashboard_stats(current_user_id=admin_id)

            message = AdminMessages.Dashboard.FULL.format(
                total_users=stats.get("total_users", 0),
                active_users=stats.get("active_users", 0),
                total_keys=stats.get("total_keys", 0),
                active_keys=stats.get("active_keys", 0),
                wireguard_keys=stats.get("wireguard_keys", 0),
                outline_keys=stats.get("outline_keys", 0),
                total_revenue=stats.get("total_revenue", 0),
                new_users_today=stats.get("new_users_today", 0),
                keys_created_today=stats.get("keys_created_today", 0),
                server_status=stats.get("server_status_text", "N/A"),
                generated_at=stats.get("generated_at", "N/A"),
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.dashboard_actions(),
                parse_mode="Markdown",
            )
            return ADMIN_MENU

        except Exception as e:
            await self._handle_error(update, context, e, "show_dashboard")
            return ADMIN_MENU

    @with_spinner()
    async def logs_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra los logs del sistema."""
        user = update.effective_user
        if user is None or not self._is_admin(user.id):
            await self._reply_message(
                update,
                AdminMessages.Error.ACCESS_DENIED,
                parse_mode="Markdown",
                context=context,
            )
            return ConversationHandler.END

        try:
            logs_content = logger.get_last_logs(lines=30)

            if (
                "Error leyendo logs:" in logs_content
                or "El archivo de log aún no existe" in logs_content
            ):
                message = AdminMessages.Logs.NO_LOGS
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = AdminMessages.Logs.LOGS_DISPLAY.format(
                    logs_content=logs_content[-4000:],
                    timestamp=timestamp,
                )

            if update.message:
                await self._reply_message(update, message, parse_mode="Markdown")
            elif update.callback_query:
                await self._safe_answer_query(update.callback_query)
                await self._safe_edit_message(
                    update.callback_query,
                    context,
                    text=message,
                    reply_markup=AdminKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
            return ADMIN_MENU

        except Exception as e:
            error_message = AdminMessages.Logs.LOGS_ERROR.format(error=str(e))
            if update.message:
                await self._reply_message(update, error_message, parse_mode="Markdown")
            elif update.callback_query:
                await self._safe_answer_query(update.callback_query)
                await self._safe_edit_message(
                    update.callback_query,
                    context,
                    text=error_message,
                    reply_markup=AdminKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
            return ADMIN_MENU

    @admin_required
    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú de configuración."""
        query = update.callback_query
        await self._safe_answer_query(query)

        await self._safe_edit_message(
            query,
            context,
            text=AdminMessages.Settings.HEADER,
            reply_markup=AdminKeyboards.settings_menu(),
            parse_mode="Markdown",
        )
        return VIEWING_SETTINGS

    @admin_required
    @admin_spinner_callback
    async def show_server_settings(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra configuración de servidores."""
        query = update.callback_query
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return ADMIN_MENU
        admin_id = user.id

        try:
            server_status = await self.service.get_server_status()

            wg = server_status.get("wireguard", {})
            ol = server_status.get("outline", {})

            message = AdminMessages.Settings.SERVERS.format(
                wg_status="✅ Online" if wg.get("is_healthy") else "❌ Offline",
                wg_keys=wg.get("total_keys", 0),
                ol_status="✅ Online" if ol.get("is_healthy") else "❌ Offline",
                ol_keys=ol.get("total_keys", 0),
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_settings(),
                parse_mode="Markdown",
            )
            return VIEWING_SETTINGS

        except Exception as e:
            await self._handle_error(update, context, e, "show_server_settings")
            return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def show_limits_settings(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra configuración de límites."""
        query = update.callback_query
        await self._safe_answer_query(query)

        try:
            message = AdminMessages.Settings.LIMITS.format(
                max_keys=2,
                free_data=10,
                referral_data=1,
            )

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_settings(),
                parse_mode="Markdown",
            )
            return VIEWING_SETTINGS

        except Exception as e:
            await self._handle_error(update, context, e, "show_limits_settings")
            return ADMIN_MENU

    @admin_required
    async def show_maintenance(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el menú de mantenimiento."""
        query = update.callback_query
        await self._safe_answer_query(query)

        await self._safe_edit_message(
            query,
            context,
            text=AdminMessages.Maintenance.HEADER,
            reply_markup=AdminKeyboards.maintenance_menu(),
            parse_mode="Markdown",
        )
        return VIEWING_MAINTENANCE

    @admin_required
    @admin_spinner_callback
    async def clear_logs(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Limpia los logs del sistema."""
        query = update.callback_query
        await self._safe_answer_query(query)

        try:
            logger.clear_logs()
            message = AdminMessages.Maintenance.LOGS_CLEARED

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_maintenance(),
                parse_mode="Markdown",
            )
            return VIEWING_MAINTENANCE

        except Exception as e:
            await self._handle_error(update, context, e, "clear_logs")
            return ADMIN_MENU

    @admin_required
    @admin_spinner_callback
    async def backup_database(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Crea un backup de la base de datos."""
        query = update.callback_query
        await self._safe_answer_query(query)

        try:
            from datetime import datetime as dt

            filename = f"backup_{dt.now().strftime('%Y%m%d_%H%M%S')}.sql"
            message = AdminMessages.Maintenance.BACKUP_CREATED.format(filename=filename)

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message,
                reply_markup=AdminKeyboards.back_to_maintenance(),
                parse_mode="Markdown",
            )
            return VIEWING_MAINTENANCE

        except Exception as e:
            await self._handle_error(update, context, e, "backup_database")
            return ADMIN_MENU

    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Vuelve al menú principal de administración."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if context.user_data is not None:
            context.user_data.pop("users_page", None)
            context.user_data.pop("keys_page", None)
            context.user_data.pop("keys_filter", None)
            context.user_data.pop("viewing_user_id", None)
            context.user_data.pop("viewing_key_id", None)

        await self._safe_edit_message(
            query,
            context,
            text=AdminMessages.Menu.MAIN,
            reply_markup=AdminKeyboards.main_menu(),
            parse_mode="Markdown",
        )
        return ADMIN_MENU

    async def end_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finaliza la sesión administrativa."""
        if context.user_data is not None:
            context.user_data.clear()

        if update.message:
            await self._reply_message(
                update,
                "👋 Sesión administrativa finalizada.",
                reply_markup=AdminKeyboards.back_to_user_menu(),
            )
        elif update.callback_query:
            await self._safe_answer_query(update.callback_query)
            await self._safe_edit_message(
                update.callback_query,
                context,
                text="👋 Sesión administrativa finalizada.",
                reply_markup=AdminKeyboards.back_to_user_menu(),
            )
        return ConversationHandler.END


def get_admin_handlers(admin_service: AdminService):
    """Retorna los handlers administrativos."""
    handler = AdminHandler(admin_service)

    return [
        CommandHandler("admin", handler.admin_menu),
        CommandHandler("logs", handler.logs_handler),
    ]


def get_admin_callback_handlers(admin_service: AdminService):
    """Retorna los handlers de callbacks para administración."""
    handler = AdminHandler(admin_service)

    return [
        CallbackQueryHandler(handler.show_users, pattern="^admin_show_users$"),
        CallbackQueryHandler(handler.show_keys, pattern="^admin_show_keys$"),
        CallbackQueryHandler(handler.show_dashboard, pattern="^admin_server_status$"),
                CallbackQueryHandler(handler.logs_handler, pattern="^admin_logs$"),
        CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
        CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
        CallbackQueryHandler(handler.users_page, pattern=r"^users_page_\d+$"),
        CallbackQueryHandler(handler.show_user_details, pattern=r"^user_details_\d+$"),
        CallbackQueryHandler(handler.suspend_user, pattern=r"^user_suspend_\d+$"),
        CallbackQueryHandler(handler.reactivate_user, pattern=r"^user_reactivate_\d+$"),
        CallbackQueryHandler(handler.confirm_delete_user, pattern=r"^user_delete_\d+$"),
        CallbackQueryHandler(
            handler.execute_delete_user, pattern=r"^confirm_delete_user_\d+$"
        ),
        CallbackQueryHandler(
            handler.cancel_user_action, pattern=r"^cancel_delete_user$"
        ),
        CallbackQueryHandler(handler.keys_page, pattern=r"^keys_page_\d+$"),
        CallbackQueryHandler(handler.keys_filter, pattern=r"^keys_filter_\w+$"),
        CallbackQueryHandler(
            handler.show_key_details, pattern=r"^admin_key_details_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.suspend_key, pattern=r"^admin_key_suspend_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.reactivate_key, pattern=r"^admin_key_reactivate_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.confirm_delete_key, pattern=r"^admin_key_delete_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.execute_delete_key, pattern=r"^confirm_delete_key_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(handler.cancel_key_action, pattern=r"^cancel_delete_key$"),
        CallbackQueryHandler(handler.show_settings, pattern="^admin_settings$"),
        CallbackQueryHandler(handler.show_maintenance, pattern="^admin_maintenance$"),
        CallbackQueryHandler(
            handler.show_server_settings, pattern="^settings_servers$"
        ),
        CallbackQueryHandler(handler.show_limits_settings, pattern="^settings_limits$"),
        CallbackQueryHandler(handler.clear_logs, pattern="^clear_logs$"),
        CallbackQueryHandler(handler.backup_database, pattern="^backup_db$"),
    ]


def get_admin_conversation_handler(
    admin_service: AdminService, 
) -> ConversationHandler:
    """Retorna el ConversationHandler para administración."""
    handler = AdminHandler(admin_service)

    return ConversationHandler(
        entry_points=[CommandHandler("admin", handler.admin_menu)],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(handler.show_users, pattern="^admin_show_users$"),
                CallbackQueryHandler(handler.show_keys, pattern="^admin_show_keys$"),
                CallbackQueryHandler(
                    handler.show_dashboard, pattern="^admin_server_status$"
                ),
                                CallbackQueryHandler(handler.show_settings, pattern="^admin_settings$"),
                CallbackQueryHandler(
                    handler.show_maintenance, pattern="^admin_maintenance$"
                ),
                CallbackQueryHandler(handler.logs_handler, pattern="^admin_logs$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_USERS: [
                CallbackQueryHandler(handler.users_page, pattern=r"^users_page_\d+$"),
                CallbackQueryHandler(
                    handler.show_user_details, pattern=r"^user_details_\d+$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_USER_DETAILS: [
                CallbackQueryHandler(handler.show_users, pattern="^admin_show_users$"),
                CallbackQueryHandler(
                    handler.suspend_user, pattern=r"^user_suspend_\d+$"
                ),
                CallbackQueryHandler(
                    handler.reactivate_user, pattern=r"^user_reactivate_\d+$"
                ),
                CallbackQueryHandler(
                    handler.confirm_delete_user, pattern=r"^user_delete_\d+$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            CONFIRMING_USER_DELETE: [
                CallbackQueryHandler(
                    handler.execute_delete_user, pattern=r"^confirm_delete_user_\d+$"
                ),
                CallbackQueryHandler(
                    handler.cancel_user_action, pattern=r"^cancel_delete_user$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
            ],
            VIEWING_KEYS: [
                CallbackQueryHandler(handler.keys_page, pattern=r"^keys_page_\d+$"),
                CallbackQueryHandler(handler.keys_filter, pattern=r"^keys_filter_\w+$"),
                CallbackQueryHandler(
                    handler.show_key_details, pattern=r"^admin_key_details_[a-f0-9\-]+$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_KEY_DETAILS: [
                CallbackQueryHandler(handler.show_keys, pattern="^admin_show_keys$"),
                CallbackQueryHandler(
                    handler.suspend_key, pattern=r"^admin_key_suspend_[a-f0-9\-]+$"
                ),
                CallbackQueryHandler(
                    handler.reactivate_key,
                    pattern=r"^admin_key_reactivate_[a-f0-9\-]+$",
                ),
                CallbackQueryHandler(
                    handler.confirm_delete_key,
                    pattern=r"^admin_key_delete_[a-f0-9\-]+$",
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            CONFIRMING_KEY_DELETE: [
                CallbackQueryHandler(
                    handler.execute_delete_key,
                    pattern=r"^confirm_delete_key_[a-f0-9\-]+$",
                ),
                CallbackQueryHandler(
                    handler.cancel_key_action, pattern=r"^cancel_delete_key$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
            ],
            VIEWING_SETTINGS: [
                CallbackQueryHandler(
                    handler.show_server_settings, pattern="^settings_servers$"
                ),
                CallbackQueryHandler(
                    handler.show_limits_settings, pattern="^settings_limits$"
                ),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
            VIEWING_MAINTENANCE: [
                CallbackQueryHandler(handler.clear_logs, pattern="^clear_logs$"),
                CallbackQueryHandler(handler.backup_database, pattern="^backup_db$"),
                CallbackQueryHandler(handler.back_to_menu, pattern="^admin$"),
                CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", handler.end_admin),
            CallbackQueryHandler(handler.end_admin, pattern="^end_admin$"),
        ],
        per_message=False,
        per_chat=True,
        per_user=True,
        allow_reentry=True,
    )
