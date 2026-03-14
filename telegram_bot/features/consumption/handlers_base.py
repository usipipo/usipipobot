"""
Clase base para handlers de consumo.

Author: uSipipo Team
Version: 1.0.0 - Refactored from handlers_consumption.py
"""

from telegram import Update
from telegram.ext import ContextTypes

from application.services.consumption_billing_service import ConsumptionBillingService
from application.services.consumption_invoice_service import ConsumptionInvoiceService
from telegram_bot.features.consumption.keyboards_consumption import ConsumptionKeyboards
from telegram_bot.features.consumption.messages_consumption import ConsumptionMessages
from utils.logger import logger
from utils.telegram_utils import TelegramUtils


class ConsumptionBaseHandler:
    """Clase base para handlers de consumo."""

    def __init__(
        self,
        billing_service: ConsumptionBillingService,
        invoice_service: ConsumptionInvoiceService,
    ):
        self.billing_service = billing_service
        self.invoice_service = invoice_service
        logger.info("⚡ ConsumptionHandler inicializado")

    async def _send_error_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Envía mensaje de error genérico."""
        keyboard = ConsumptionKeyboards.back_to_consumption_menu()

        if update.callback_query:
            await TelegramUtils.safe_edit_message(
                update.callback_query,
                context,
                text=ConsumptionMessages.Error.GENERIC,
                reply_markup=keyboard,
            )
        elif update.message:
            await update.message.reply_text(
                text=ConsumptionMessages.Error.GENERIC, reply_markup=keyboard
            )
