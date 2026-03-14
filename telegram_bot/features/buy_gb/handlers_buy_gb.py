"""
Handlers para compra de GB con Telegram Stars.

Author: uSipipo Team
Version: 2.0.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from application.services.data_package_service import DataPackageService
from utils.logger import logger

from .handlers_confirmation import ConfirmationMixin
from .handlers_packages import PackagesMixin
from .handlers_payment_crypto import PaymentCryptoMixin
from .handlers_payment_stars import PaymentStarsMixin
from .handlers_slots import SlotsMixin

__all__ = [
    "BuyGbHandler",
    "get_buy_gb_handlers",
    "get_buy_gb_callback_handlers",
    "get_buy_gb_payment_handlers",
]


class BuyGbHandler(
    PackagesMixin,
    SlotsMixin,
    PaymentStarsMixin,
    PaymentCryptoMixin,
    ConfirmationMixin,
):
    """Handler para compra de GB con Telegram Stars."""

    def __init__(self, data_package_service: DataPackageService):
        self.data_package_service = data_package_service
        logger.info("📦 BuyGbHandler inicializado")


def get_buy_gb_handlers(data_package_service: DataPackageService):
    """Obtiene los handlers principales de compra de GB."""
    handler = BuyGbHandler(data_package_service)

    return [
        MessageHandler(filters.Regex("^📦 Comprar GB$"), handler.show_packages),
        CommandHandler("buy", handler.show_packages),
        CommandHandler("packages", handler.show_packages),
    ]


def get_buy_gb_callback_handlers(data_package_service: DataPackageService):
    """Obtiene los handlers de callbacks para compra de GB."""
    handler = BuyGbHandler(data_package_service)

    return [
        CallbackQueryHandler(handler.show_packages, pattern="^buy_gb_menu$"),
        CallbackQueryHandler(handler.select_payment_method, pattern="^select_payment_"),
        CallbackQueryHandler(handler.pay_with_stars, pattern="^pay_stars_"),
        CallbackQueryHandler(handler.pay_with_crypto, pattern="^pay_crypto_"),
        CallbackQueryHandler(handler.view_data_summary, pattern="^view_data_summary$"),
        CallbackQueryHandler(handler.show_slots_menu, pattern="^buy_slots_menu$"),
        # Slots payment handlers
        CallbackQueryHandler(handler.select_slot_payment_method, pattern="^select_slot_payment_"),
        CallbackQueryHandler(handler.pay_slots_with_stars, pattern="^pay_slots_stars_"),
        CallbackQueryHandler(handler.pay_slots_with_crypto, pattern="^pay_slots_crypto_"),
    ]


def get_buy_gb_payment_handlers(data_package_service: DataPackageService):
    """Obtiene los handlers de pago para compra de GB."""
    handler = BuyGbHandler(data_package_service)

    return [
        PreCheckoutQueryHandler(handler.pre_checkout_callback),
        MessageHandler(filters.SUCCESSFUL_PAYMENT, handler.successful_payment),
    ]
