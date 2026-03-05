"""
Handlers para panel administrativo de uSipipo.

Author: uSipipo Team
Version: 5.0.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from application.services.admin_service import AdminService
from config import settings
from telegram_bot.common.base_handler import BaseConversationHandler
from utils.logger import logger

from .handlers_dashboard import DashboardAdminMixin
from .handlers_keys_actions import (
    CONFIRMING_KEY_DELETE,
    KEYS_PER_PAGE,
    VIEWING_KEY_DETAILS,
    KeysActionsMixin,
)
from .handlers_keys_list import VIEWING_KEYS, KeysListMixin
from .handlers_settings import VIEWING_MAINTENANCE, VIEWING_SETTINGS, SettingsAdminMixin
from .handlers_tickets_actions import REPLYING_TO_TICKET, TicketsActionsMixin
from .handlers_tickets_list import VIEWING_TICKETS, TicketsListMixin
from .handlers_users_actions import (
    CONFIRMING_USER_DELETE,
    VIEWING_USER_DETAILS,
    UsersActionsMixin,
)

# Importar estados para re-exportar
from .handlers_users_list import (
    ADMIN_MENU,
    USERS_PER_PAGE,
    VIEWING_USERS,
    UsersListMixin,
)
from .keyboards_admin import AdminKeyboards
from .messages_admin import AdminMessages

__all__ = [
    "AdminHandler",
    "ADMIN_MENU",
    "VIEWING_USERS",
    "VIEWING_USER_DETAILS",
    "VIEWING_KEYS",
    "VIEWING_KEY_DETAILS",
    "CONFIRMING_USER_DELETE",
    "CONFIRMING_KEY_DELETE",
    "VIEWING_SETTINGS",
    "VIEWING_MAINTENANCE",
    "VIEWING_TICKETS",
    "REPLYING_TO_TICKET",
]


class AdminHandler(
    BaseConversationHandler,
    UsersListMixin,
    UsersActionsMixin,
    KeysListMixin,
    KeysActionsMixin,
    DashboardAdminMixin,
    SettingsAdminMixin,
    TicketsListMixin,
    TicketsActionsMixin,
):
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
