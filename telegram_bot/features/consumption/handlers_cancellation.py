"""
Handlers para cancelación del modo consumo.

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


class CancellationMixin:
    """Mixin para cancelación del modo consumo."""

    async def start_cancellation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Inicia el flujo de cancelación del modo consumo."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            can_cancel, error_msg = await self.billing_service.can_cancel_consumption(
                user_id, user_id
            )

            if not can_cancel:
                await query.edit_message_text(
                    text=ConsumptionMessages.Cancellation.CANNOT_CANCEL.format(
                        reason=error_msg or "No puedes cancelar el modo consumo"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown",
                )
                return

            summary = await self.billing_service.get_current_consumption(
                user_id, user_id
            )

            if not summary:
                await query.edit_message_text(
                    text=ConsumptionMessages.Cancellation.CANNOT_CANCEL.format(
                        reason="No se pudo obtener tu información de consumo"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown",
                )
                return

            message = (
                ConsumptionMessages.Cancellation.CONFIRMATION_HEADER
                + "\n\n"
                + ConsumptionMessages.Cancellation.get_cancellation_summary(
                    days_active=summary.days_active,
                    consumption_formatted=summary.formatted_consumption,
                    cost_formatted=summary.formatted_cost,
                )
            )

            await query.edit_message_text(
                text=message,
                reply_markup=ConsumptionKeyboards.cancellation_confirmation(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en start_cancellation: {e}")
            await self._send_error_message(update, context)

    async def confirm_cancellation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Confirma la cancelación del modo consumo."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            result = await self.billing_service.cancel_consumption_mode(
                user_id, user_id
            )

            if result.success:
                from decimal import Decimal

                if result.mb_consumed < Decimal("1024"):
                    consumption_formatted = f"{result.mb_consumed:.2f} MB"
                else:
                    gb_consumed = result.mb_consumed / Decimal("1024")
                    consumption_formatted = f"{gb_consumed:.2f} GB"

                cost_formatted = f"${result.total_cost_usd:.2f} USD"

                if result.had_debt:
                    message = (
                        ConsumptionMessages.Cancellation.SUCCESS
                        + "\n\n"
                        + f"📊 **Resumen del ciclo cancelado:**\n"
                        + f"📅 Días activos: {result.days_active}/30\n"
                        + f"📈 Consumo: {consumption_formatted}\n"
                        + f"💰 Costo: {cost_formatted}"
                    )
                else:
                    message = (
                        "✅ **Modo Consumo Cancelado**\n\n"
                        "Se ha cerrado tu ciclo de consumo.\n"
                        "Como no realizaste ningún consumo, no hay nada que pagar.\n\n"
                        "🔓 **Tus claves VPN siguen activas** y puedes seguir navegando "
                        "con tu plan gratuito."
                    )

                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.cancel_success_keyboard(),
                    parse_mode="Markdown",
                )
                logger.info(
                    f"✅ Usuario {user_id} canceló modo consumo (had_debt={result.had_debt})"
                )
            else:
                message = ConsumptionMessages.Cancellation.CANNOT_CANCEL.format(
                    reason=result.error_message or "Error desconocido"
                )
                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error en confirm_cancellation: {e}")
            await self._send_error_message(update, context)
