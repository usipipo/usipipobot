"""
Handlers para acciones de usuarios en panel administrativo.

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
VIEWING_USERS = 1
VIEWING_USER_DETAILS = 2
CONFIRMING_USER_DELETE = 5


class UsersActionsMixin:
    """Mixin para acciones de usuarios en panel admin."""

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
