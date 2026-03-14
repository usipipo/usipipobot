"""
Handlers para pagos con Telegram Stars.

Author: uSipipo Team
Version: 1.2.0 - Refactored into mixins
"""

from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes

from application.services.data_package_service import PACKAGE_OPTIONS, SLOT_OPTIONS
from utils.logger import logger

from .keyboards_buy_gb import BuyGbKeyboards
from .messages_buy_gb import BuyGbMessages


class PaymentStarsMixin:
    """Mixin para procesamiento de pagos con Telegram Stars."""

    async def pay_with_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa pago con Telegram Stars."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        if not update.effective_user or not update.effective_chat:
            return
        user_id = update.effective_user.id
        package_type_str = query.data.split("_")[-1]

        try:
            package_option = None
            for pkg in PACKAGE_OPTIONS:
                if pkg.package_type.value == package_type_str:
                    package_option = pkg
                    break

            if not package_option:
                await query.edit_message_text(
                    text=BuyGbMessages.Error.INVALID_PACKAGE,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
                return

            payload = f"data_package_{package_type_str}_{user_id}"

            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=BuyGbMessages.Payment.INVOICE_TITLE.format(package_name=package_option.name),
                description=BuyGbMessages.Payment.INVOICE_DESCRIPTION.format(
                    gb_amount=package_option.data_gb
                ),
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(f"{package_option.data_gb} GB", package_option.stars)],
            )

            logger.info(f"📦 Invoice enviado: {package_option.name} para usuario {user_id}")

        except Exception as e:
            logger.error(f"Error en pay_with_stars: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

    async def pay_slots_with_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa pago de slots con Telegram Stars."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        if not update.effective_user or not update.effective_chat:
            return
        user_id = update.effective_user.id
        slots_str = query.data.split("_")[-1]
        slots = int(slots_str)

        try:
            slot_option = None
            for slot in SLOT_OPTIONS:
                if slot.slots == slots:
                    slot_option = slot
                    break

            if not slot_option:
                await query.edit_message_text(
                    text=BuyGbMessages.Error.SYSTEM_ERROR,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
                return

            payload = f"key_slots_{slots}_{user_id}"

            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=BuyGbMessages.Slots.INVOICE_TITLE.format(slots_name=slot_option.name),
                description=BuyGbMessages.Slots.INVOICE_DESCRIPTION.format(slots=slots),
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(f"+{slots} Claves", slot_option.stars)],
            )

            logger.info(f"🔑 Invoice enviado: {slot_option.name} para usuario {user_id}")

        except Exception as e:
            logger.error(f"Error en pay_slots_with_stars: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

    async def buy_package(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa la compra de un paquete (deprecated, usa pay_with_stars)."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        if not update.effective_user or not update.effective_chat:
            return
        user_id = update.effective_user.id
        package_type_str = query.data.split("_")[-1]

        try:
            package_option = None
            for pkg in PACKAGE_OPTIONS:
                if pkg.package_type.value == package_type_str:
                    package_option = pkg
                    break

            if not package_option:
                await query.edit_message_text(
                    text=BuyGbMessages.Error.INVALID_PACKAGE,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
                return

            payload = f"data_package_{package_type_str}_{user_id}"

            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title=BuyGbMessages.Payment.INVOICE_TITLE.format(package_name=package_option.name),
                description=BuyGbMessages.Payment.INVOICE_DESCRIPTION.format(
                    gb_amount=package_option.data_gb
                ),
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(f"{package_option.data_gb} GB", package_option.stars)],
            )

            logger.info(f"📦 Invoice enviado: {package_option.name} para usuario {user_id}")

        except Exception as e:
            logger.error(f"Error en buy_package: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )
