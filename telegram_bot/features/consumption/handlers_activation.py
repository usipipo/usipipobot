"""
Handlers para activación del modo consumo.

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


class ActivationMixin:
    """Mixin para activación del modo consumo."""

    async def start_activation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Inicia el flujo de activación del modo consumo."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            can_activate, error_msg = await self.billing_service.can_activate_consumption(
                user_id, user_id
            )

            if not can_activate:
                message = ConsumptionMessages.Activation.CANNOT_ACTIVATE.format(
                    reason=error_msg or "No cumples los requisitos"
                )
                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )
                return

            message = (
                ConsumptionMessages.Activation.WARNING_HEADER + "\n\n" +
                ConsumptionMessages.Activation.get_terms_and_conditions() + "\n\n" +
                ConsumptionMessages.Activation.get_price_example() + "\n\n" +
                ConsumptionMessages.Activation.CONFIRMATION_PROMPT
            )

            await query.edit_message_text(
                text=message,
                reply_markup=ConsumptionKeyboards.activation_confirmation(),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error en start_activation: {e}")
            await self._send_error_message(update, context)

    async def confirm_activation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Confirma la activación del modo consumo."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            result = await self.billing_service.activate_consumption_mode(
                user_id, user_id
            )

            if result.success:
                await query.edit_message_text(
                    text=ConsumptionMessages.Activation.get_success_message(),
                    reply_markup=ConsumptionKeyboards.activation_success(),
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Usuario {user_id} activó modo consumo")
            else:
                message = ConsumptionMessages.Activation.CANNOT_ACTIVATE.format(
                    reason=result.error_message or "Error desconocido"
                )
                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en confirm_activation: {e}")
            await self._send_error_message(update, context)
