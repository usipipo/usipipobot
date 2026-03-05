"""
Handlers para menú principal de consumo.

Author: uSipipo Team
Version: 1.0.0 - Refactored from handlers_consumption.py
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.features.consumption.keyboards_consumption import (
    ConsumptionKeyboards,
)
from telegram_bot.features.consumption.messages_consumption import (
    ConsumptionMessages,
)
from utils.logger import logger
from utils.telegram_utils import TelegramUtils


class MenuMixin:
    """Mixin para menú principal de consumo."""

    async def show_consumption_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el menú principal de tarifa por consumo."""
        query = update.callback_query
        if query:
            await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            summary = await self.billing_service.get_current_consumption(
                user_id, user_id
            )

            has_active_cycle = summary is not None and summary.is_active
            has_pending_debt = (
                summary is not None
                and not summary.is_active
                and summary.billing_id is not None
            )
            can_activate, _ = await self.billing_service.can_activate_consumption(
                user_id, user_id
            )

            if has_pending_debt:
                status_text = ConsumptionMessages.Menu.STATUS_DEBT
            elif has_active_cycle:
                status_text = ConsumptionMessages.Menu.STATUS_ACTIVE
            else:
                status_text = ConsumptionMessages.Menu.STATUS_INACTIVE

            message = ConsumptionMessages.Menu.MAIN_MENU.format(status_text=status_text)

            keyboard = ConsumptionKeyboards.consumption_main_menu(
                has_active_cycle=has_active_cycle,
                has_pending_debt=has_pending_debt,
                can_activate=can_activate,
            )

            if query:
                await TelegramUtils.safe_edit_message(
                    query,
                    context,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en show_consumption_menu: {e}")
            await self._send_error_message(update, context)

    async def show_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra información sobre el modo consumo."""
        query = update.callback_query
        if query:
            await query.answer()

        message = (
            ConsumptionMessages.Activation.get_terms_and_conditions()
            + "\n\n"
            + ConsumptionMessages.Activation.get_price_example()
        )

        if query:
            await query.edit_message_text(
                text=message,
                reply_markup=ConsumptionKeyboards.view_info_only(),
                parse_mode="Markdown",
            )
        elif update.message:
            await update.message.reply_text(
                text=message,
                reply_markup=ConsumptionKeyboards.view_info_only(),
                parse_mode="Markdown",
            )
