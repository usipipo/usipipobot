"""
Handlers para compra de slots de claves.

Author: uSipipo Team
Version: 1.2.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import ContextTypes

from application.services.data_package_service import PACKAGE_OPTIONS, SLOT_OPTIONS
from utils.logger import logger

from .keyboards_buy_gb import BuyGbKeyboards
from .messages_buy_gb import BuyGbMessages


class SlotsMixin:
    """Mixin para manejo de slots de claves."""

    async def show_slots_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú de compra de slots de claves."""
        query = update.callback_query
        if query:
            await query.answer()

        if not update.effective_user:
            return

        try:
            slots_list = BuyGbMessages.Slots.format_slots_list()
            message = BuyGbMessages.Slots.MENU.format(slots_list=slots_list)
            keyboard = BuyGbKeyboards.slots_menu()

            if query:
                await query.edit_message_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en show_slots_menu: {e}")
            error_message = BuyGbMessages.Error.SYSTEM_ERROR

            if query:
                await query.edit_message_text(
                    text=error_message,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
            elif update.message:
                await update.message.reply_text(
                    text=error_message,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )

    async def select_slot_payment_method(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra opciones de método de pago para slots."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

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

            # Calcular precio en USDT (tasa: 1 USDT = 120 Stars)
            usdt_amount = slot_option.stars / 120

            message = f"""💳 *Selecciona método de pago*

🔑 {slot_option.name}
⭐ Precio: {slot_option.stars} Stars
💰 Precio: ~{usdt_amount:.2f} USDT (BSC)

Elige cómo quieres pagar:"""

            keyboard = BuyGbKeyboards.slot_payment_method_selection(slots)

            await query.edit_message_text(
                text=message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error en select_slot_payment_method: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )
