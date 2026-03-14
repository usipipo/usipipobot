"""
Handlers para visualización del estado de consumo.

Author: uSipipo Team
Version: 1.0.0 - Refactored from handlers_consumption.py
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.features.consumption.keyboards_consumption import ConsumptionKeyboards
from telegram_bot.features.consumption.messages_consumption import ConsumptionMessages
from utils.logger import logger
from utils.telegram_utils import TelegramUtils


class StatusMixin:
    """Mixin para visualización del estado de consumo."""

    async def view_my_consumption(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el consumo actual del usuario."""
        query = update.callback_query
        if query:
            await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            summary = await self.billing_service.get_current_consumption(user_id, user_id)

            if not summary:
                message = ConsumptionMessages.ConsumptionStatus.NO_ACTIVE_CYCLE
                keyboard = ConsumptionKeyboards.view_info_only()
            elif summary.is_active:
                days_remaining = max(0, 30 - summary.days_active)
                message = ConsumptionMessages.ConsumptionStatus.ACTIVE_CYCLE.format(
                    days_active=summary.days_active,
                    consumption_formatted=summary.formatted_consumption,
                    cost_formatted=summary.formatted_cost,
                    days_remaining=days_remaining,
                )
                keyboard = ConsumptionKeyboards.back_to_consumption_menu()
            else:
                message = ConsumptionMessages.ConsumptionStatus.CLOSED_CYCLE.format(
                    consumption_formatted=summary.formatted_consumption,
                    cost_formatted=summary.formatted_cost,
                )
                keyboard = ConsumptionKeyboards.consumption_main_menu(
                    has_active_cycle=False, has_pending_debt=True, can_activate=False
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
            logger.error(f"Error en view_my_consumption: {e}")
            await self._send_error_message(update, context)
