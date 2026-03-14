"""
Handlers para el módulo de tarifa por consumo (Pay-as-You-Go).

Author: uSipipo Team
Version: 2.0.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from application.services.consumption_billing_service import ConsumptionBillingService
from application.services.consumption_invoice_service import ConsumptionInvoiceService
from telegram_bot.features.consumption.handlers_activation import ActivationMixin
from telegram_bot.features.consumption.handlers_base import ConsumptionBaseHandler
from telegram_bot.features.consumption.handlers_cancellation import CancellationMixin
from telegram_bot.features.consumption.handlers_invoice import InvoiceMixin
from telegram_bot.features.consumption.handlers_menu import MenuMixin
from telegram_bot.features.consumption.handlers_status import StatusMixin

__all__ = [
    "ConsumptionHandler",
    "get_consumption_handlers",
    "get_consumption_callback_handlers",
]


class ConsumptionHandler(
    ConsumptionBaseHandler,
    MenuMixin,
    ActivationMixin,
    StatusMixin,
    InvoiceMixin,
    CancellationMixin,
):
    """Handler para la tarifa por consumo."""

    def __init__(
        self,
        billing_service: ConsumptionBillingService,
        invoice_service: ConsumptionInvoiceService,
    ):
        super().__init__(billing_service, invoice_service)


def get_consumption_handlers(
    billing_service: ConsumptionBillingService,
    invoice_service: ConsumptionInvoiceService,
):
    """Retorna los handlers para el módulo de consumo."""
    handler = ConsumptionHandler(billing_service, invoice_service)

    return [
        CommandHandler("consumption", handler.show_consumption_menu),
        CommandHandler("mi_consumo", handler.view_my_consumption),
    ]


def get_consumption_callback_handlers(
    billing_service: ConsumptionBillingService,
    invoice_service: ConsumptionInvoiceService,
):
    """Retorna los callback handlers para el módulo de consumo."""
    handler = ConsumptionHandler(billing_service, invoice_service)

    return [
        CallbackQueryHandler(handler.show_consumption_menu, pattern="^consumption_menu$"),
        CallbackQueryHandler(handler.start_activation, pattern="^consumption_activate$"),
        CallbackQueryHandler(handler.confirm_activation, pattern="^consumption_confirm_activate$"),
        CallbackQueryHandler(handler.view_my_consumption, pattern="^consumption_view_status$"),
        CallbackQueryHandler(
            handler.start_invoice_generation, pattern="^consumption_generate_invoice$"
        ),
        CallbackQueryHandler(handler.generate_invoice_stars, pattern="^consumption_pay_stars$"),
        CallbackQueryHandler(handler.generate_invoice_crypto, pattern="^consumption_pay_crypto$"),
        CallbackQueryHandler(handler.show_info, pattern="^consumption_info$"),
        CallbackQueryHandler(handler.start_cancellation, pattern="^consumption_cancel$"),
        CallbackQueryHandler(handler.confirm_cancellation, pattern="^consumption_confirm_cancel$"),
    ]
