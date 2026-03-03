"""
Handlers para dashboard y logs en panel administrativo.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_admin.py
"""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.common.decorators import admin_required
from telegram_bot.features.admin.messages_admin import AdminMessages
from telegram_bot.features.admin.keyboards_admin import AdminKeyboards
from utils.spinner import SpinnerManager, admin_spinner_callback, with_spinner
from utils.logger import logger

ADMIN_MENU = 0


class DashboardAdminMixin:
    """Mixin para dashboard y logs en panel admin."""

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
