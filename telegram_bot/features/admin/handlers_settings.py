"""
Handlers para configuración y mantenimiento en panel administrativo.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_admin.py
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.common.decorators import admin_required
from telegram_bot.features.admin.messages_admin import AdminMessages
from telegram_bot.features.admin.keyboards_admin import AdminKeyboards
from utils.spinner import SpinnerManager, admin_spinner_callback
from utils.logger import logger

ADMIN_MENU = 0
VIEWING_SETTINGS = 7
VIEWING_MAINTENANCE = 8


class SettingsAdminMixin:
    """Mixin para configuración y mantenimiento en panel admin."""

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
