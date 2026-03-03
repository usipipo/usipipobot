"""
Handlers para listado de usuarios en panel administrativo.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_admin.py
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.common.decorators import admin_required
from telegram_bot.features.admin.messages_admin import AdminMessages
from telegram_bot.features.admin.keyboards_admin import AdminKeyboards
from utils.spinner import SpinnerManager, admin_spinner_callback

ADMIN_MENU = 0
VIEWING_USERS = 1
USERS_PER_PAGE = 10


class UsersListMixin:
    """Mixin para listado de usuarios en panel admin."""

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

            if page < 1:
                page = 1
            elif total_pages > 0 and page > total_pages:
                page = total_pages

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

            if page < 1:
                page = 1
            elif total_pages > 0 and page > total_pages:
                page = total_pages

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
