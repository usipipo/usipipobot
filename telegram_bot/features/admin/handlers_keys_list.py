"""
Handlers para listado de claves VPN en panel administrativo.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_admin.py
"""

from typing import Dict

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.common.decorators import admin_required
from telegram_bot.features.admin.handlers_keys_actions import VIEWING_KEY_DETAILS
from telegram_bot.features.admin.keyboards_admin import AdminKeyboards
from telegram_bot.features.admin.messages_admin import AdminMessages
from utils.spinner import SpinnerManager, admin_spinner_callback

ADMIN_MENU = 0
VIEWING_KEYS = 3
KEYS_PER_PAGE = 10


class KeysListMixin:
    """Mixin para listado de claves en panel admin."""

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
