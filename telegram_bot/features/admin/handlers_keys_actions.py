"""
Handlers para acciones de claves VPN en panel administrativo.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_admin.py
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.common.decorators import admin_required
from telegram_bot.features.admin.keyboards_admin import AdminKeyboards
from telegram_bot.features.admin.messages_admin import AdminMessages
from utils.spinner import SpinnerManager, admin_spinner_callback

ADMIN_MENU = 0
VIEWING_KEYS = 3
VIEWING_KEY_DETAILS = 4
CONFIRMING_KEY_DELETE = 6
KEYS_PER_PAGE = 10


class KeysActionsMixin:
    """Mixin para acciones de claves en panel admin."""

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
    async def confirm_delete_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    async def cancel_key_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
