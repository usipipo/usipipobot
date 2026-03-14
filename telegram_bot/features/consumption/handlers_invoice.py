"""
Handlers para facturación y pagos de consumo.

Author: uSipipo Team
Version: 1.0.0 - Refactored from handlers_consumption.py
"""

from telegram import Update
from telegram.ext import ContextTypes

from application.services.consumption_invoice_service import PaymentMethod
from domain.entities.consumption_invoice import ConsumptionInvoice
from telegram_bot.features.consumption.keyboards_consumption import ConsumptionKeyboards
from telegram_bot.features.consumption.messages_consumption import ConsumptionMessages
from utils.logger import logger


class InvoiceMixin:
    """Mixin para facturación y pagos de consumo."""

    async def start_invoice_generation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia la generación de factura (selección de método de pago)."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            can_generate, error_msg = await self.invoice_service.can_generate_invoice(
                user_id, user_id
            )

            if not can_generate:
                await query.edit_message_text(
                    text=ConsumptionMessages.Error.INVOICE_GENERATION.format(
                        reason=error_msg or "No puedes generar factura"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown",
                )
                return

            summary = await self.billing_service.get_current_consumption(user_id, user_id)

            if not summary:
                await query.edit_message_text(
                    text=ConsumptionMessages.Error.INVOICE_GENERATION.format(
                        reason="No se encontró información de consumo"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown",
                )
                return

            message = ConsumptionMessages.Invoice.SELECT_PAYMENT_METHOD.format(
                consumption_formatted=summary.formatted_consumption,
                cost_formatted=summary.formatted_cost,
            )

            await query.edit_message_text(
                text=message,
                reply_markup=ConsumptionKeyboards.payment_method_selection(
                    consumption_formatted=summary.formatted_consumption,
                    cost_formatted=summary.formatted_cost,
                ),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en start_invoice_generation: {e}")
            await self._send_error_message(update, context)

    async def generate_invoice_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera factura para pago con Telegram Stars."""
        await self._generate_invoice(update, context, PaymentMethod.STARS)

    async def generate_invoice_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera factura para pago con Crypto."""
        query = update.callback_query
        if query:
            await query.answer("Preparando wallet de pago...")

        from application.services.common.container import get_service
        from application.services.wallet_management_service import WalletManagementService

        try:
            wallet_service = get_service(WalletManagementService)
            if not update.effective_user:
                return

            user_id = update.effective_user.id

            from domain.interfaces.iuser_repository import IUserRepository

            user_repo = get_service(IUserRepository)
            user = await user_repo.get_by_id(user_id, user_id)

            if not user:
                if query:
                    await query.edit_message_text(
                        text="❌ Usuario no encontrado.",
                        reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    )
                return

            wallet = await wallet_service.get_or_create_wallet(user)

            if not wallet:
                if query:
                    await query.edit_message_text(
                        text="❌ Error al preparar la wallet de pago. Intenta nuevamente.",
                        reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    )
                return

            await self._generate_invoice(update, context, PaymentMethod.CRYPTO, wallet.address)

        except Exception as e:
            logger.error(f"Error obteniendo wallet: {e}")
            if query:
                await query.edit_message_text(
                    text="❌ Error al preparar el pago. Intenta nuevamente.",
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                )

    async def _generate_invoice(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        payment_method: PaymentMethod,
        wallet_address: str = "N/A",
    ):
        """Genera la factura con el método de pago seleccionado."""
        query = update.callback_query
        if not query:
            return

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            result = await self.invoice_service.generate_invoice(
                user_id=user_id,
                payment_method=payment_method,
                wallet_address=wallet_address,
                current_user_id=user_id,
            )

            if not result.success or not result.invoice:
                await query.edit_message_text(
                    text=ConsumptionMessages.Error.INVOICE_GENERATION.format(
                        reason=result.error_message or "Error desconocido"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown",
                )
                return

            invoice = result.invoice
            summary = await self.billing_service.get_current_consumption(user_id, user_id)

            if payment_method == PaymentMethod.STARS:
                await self._send_stars_invoice(update, context, invoice, summary)
            else:
                message = ConsumptionMessages.Invoice.CRYPTO_PAYMENT.format(
                    consumption_formatted=(summary.formatted_consumption if summary else "N/A"),
                    cost_formatted=invoice.get_formatted_amount(),
                    wallet_address=wallet_address,
                    time_remaining=invoice.time_remaining_formatted,
                )
                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error en _generate_invoice: {e}")
            await self._send_error_message(update, context)

    async def _send_stars_invoice(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        invoice: ConsumptionInvoice,
        summary,
    ):
        """Envía el invoice de Telegram Stars."""
        query = update.callback_query
        if not query or not update.effective_chat:
            return

        try:
            from telegram import LabeledPrice

            stars_amount = invoice.get_stars_amount()
            payload = f"consumption_invoice_{invoice.id}_{invoice.user_id}"

            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title="Pago de Tarifa por Consumo",
                description=f"Consumo: {summary.formatted_consumption if summary else 'N/A'}",
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice("Consumo VPN", stars_amount)],
            )

            await query.delete_message()

        except Exception as e:
            logger.error(f"Error enviando invoice de Stars: {e}")
            await query.edit_message_text(
                text="❌ Error al generar el pago con Stars. Intenta con Crypto.",
                reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
            )
