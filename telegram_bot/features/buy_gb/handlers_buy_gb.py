"""
Handlers para compra de GB con Telegram Stars.

Author: uSipipo Team
Version: 1.1.0
"""

from datetime import datetime, timezone

from telegram import LabeledPrice, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from application.services.data_package_service import (
    PACKAGE_OPTIONS,
    SLOT_OPTIONS,
    DataPackageService,
)
from domain.entities.data_package import PackageType
from utils.logger import logger

from .keyboards_buy_gb import BuyGbKeyboards
from .messages_buy_gb import BuyGbMessages


class BuyGbHandler:
    """Handler para compra de GB con Telegram Stars."""

    def __init__(self, data_package_service: DataPackageService):
        self.data_package_service = data_package_service
        logger.info("📦 BuyGbHandler inicializado")

    async def show_packages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query:
            await query.answer()

        user_id = update.effective_user.id

        try:
            packages_list = BuyGbMessages.Menu.format_packages_list()
            message = BuyGbMessages.Menu.PACKAGES_LIST.format(
                packages_list=packages_list
            )
            keyboard = BuyGbKeyboards.packages_menu()

            if query:
                await query.edit_message_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en show_packages: {e}")
            error_message = BuyGbMessages.Error.SYSTEM_ERROR

            if query:
                await query.edit_message_text(
                    text=error_message,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    text=error_message,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )

    async def buy_package(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

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
                title=BuyGbMessages.Payment.INVOICE_TITLE.format(
                    package_name=package_option.name
                ),
                description=BuyGbMessages.Payment.INVOICE_DESCRIPTION.format(
                    gb_amount=package_option.data_gb
                ),
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[
                    LabeledPrice(f"{package_option.data_gb} GB", package_option.stars)
                ],
            )

            logger.info(
                f"📦 Invoice enviado: {package_option.name} para usuario {user_id}"
            )

        except Exception as e:
            logger.error(f"Error en buy_package: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

    async def show_slots_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()

        try:
            slots_list = BuyGbMessages.Slots.format_slots_list()
            message = BuyGbMessages.Slots.MENU.format(slots_list=slots_list)
            keyboard = BuyGbKeyboards.slots_menu()

            await query.edit_message_text(
                text=message, reply_markup=keyboard, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error en show_slots_menu: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

    async def buy_slots(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

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
                title=BuyGbMessages.Slots.INVOICE_TITLE.format(
                    slots_name=slot_option.name
                ),
                description=BuyGbMessages.Slots.INVOICE_DESCRIPTION.format(slots=slots),
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(f"+{slots} Claves", slot_option.stars)],
            )

            logger.info(f"🔑 Invoice enviado: {slot_option.name} para usuario {user_id}")

        except Exception as e:
            logger.error(f"Error en buy_slots: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

    async def pre_checkout_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.pre_checkout_query

        try:
            payload = query.invoice_payload
            parts = payload.split("_")

            if len(parts) >= 3 and parts[0] == "key" and parts[1] == "slots":
                slots = int(parts[2])
                user_id = int(parts[3])

                slot_option = None
                for slot in SLOT_OPTIONS:
                    if slot.slots == slots:
                        slot_option = slot
                        break

                if not slot_option:
                    await query.answer(ok=False, error_message="Slots no encontrados")
                    return

                if query.total_amount != slot_option.stars:
                    await query.answer(ok=False, error_message="Monto incorrecto")
                    return

                await query.answer(ok=True)
                logger.info(
                    f"🔑 Pre-checkout exitoso: +{slots} slots para usuario {user_id}"
                )
                return

            if len(parts) != 4 or parts[0] != "data" or parts[1] != "package":
                await query.answer(ok=False, error_message="Payload invalido")
                return

            package_type_str = parts[2]
            user_id = int(parts[3])

            package_option = None
            for pkg in PACKAGE_OPTIONS:
                if pkg.package_type.value == package_type_str:
                    package_option = pkg
                    break

            if not package_option:
                await query.answer(ok=False, error_message="Paquete no encontrado")
                return

            if query.total_amount != package_option.stars:
                await query.answer(ok=False, error_message="Monto incorrecto")
                return

            await query.answer(ok=True)
            logger.info(
                f"📦 Pre-checkout exitoso: {package_option.name} para usuario {user_id}"
            )

        except Exception as e:
            logger.error(f"Error en pre_checkout_callback: {e}")
            await query.answer(ok=False, error_message="Error procesando pago")

    async def successful_payment(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        user_id = update.effective_user.id
        payment = update.message.successful_payment

        try:
            payload = payment.invoice_payload
            parts = payload.split("_")

            if len(parts) >= 3 and parts[0] == "key" and parts[1] == "slots":
                slots = int(parts[2])
                telegram_payment_id = payment.telegram_payment_charge_id

                result = await self.data_package_service.purchase_key_slots(
                    user_id=user_id,
                    slots=slots,
                    telegram_payment_id=telegram_payment_id,
                    current_user_id=user_id,
                )

                success_message = BuyGbMessages.Slots.CONFIRMATION.format(
                    slots_added=result["slots_added"],
                    new_max_keys=result["new_max_keys"],
                    stars=result["stars_paid"],
                )

                await update.message.reply_text(
                    text=success_message,
                    reply_markup=BuyGbKeyboards.slots_success(),
                    parse_mode="Markdown",
                )

                logger.info(
                    f"🔑 Slots comprados exitosamente: +{slots} para usuario {user_id}"
                )
                return

            if len(parts) != 4:
                logger.error(f"Payload invalido: {payload}")
                await update.message.reply_text(
                    text=BuyGbMessages.Error.PAYMENT_FAILED, parse_mode="Markdown"
                )
                return

            package_type_str = parts[2]
            telegram_payment_id = payment.telegram_payment_charge_id

            package = await self.data_package_service.purchase_package(
                user_id=user_id,
                package_type=package_type_str,
                telegram_payment_id=telegram_payment_id,
                current_user_id=user_id,
            )

            package_option = None
            for pkg in PACKAGE_OPTIONS:
                if pkg.package_type.value == package_type_str:
                    package_option = pkg
                    break

            bonus_text = (
                f" (+{package_option.bonus_percent}% bonus)"
                if package_option and package_option.bonus_percent > 0
                else ""
            )
            expires_at = package.expires_at.strftime("%d/%m/%Y %H:%M")

            success_message = BuyGbMessages.Payment.CONFIRMATION.format(
                package_name=(
                    package_option.name if package_option else package_type_str
                ),
                gb_amount=package_option.data_gb if package_option else "N/A",
                bonus_text=bonus_text,
                stars=payment.total_amount,
                expires_at=expires_at,
            )

            await update.message.reply_text(
                text=success_message,
                reply_markup=BuyGbKeyboards.payment_success(),
                parse_mode="Markdown",
            )

            logger.info(
                f"📦 Paquete comprado exitosamente: {package_type_str} para usuario {user_id}"
            )

        except Exception as e:
            logger.error(f"Error en successful_payment: {e}")
            await update.message.reply_text(
                text=BuyGbMessages.Error.PAYMENT_FAILED, parse_mode="Markdown"
            )

    async def view_data_summary(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        try:
            summary = await self.data_package_service.get_user_data_summary(
                user_id=user_id, current_user_id=user_id
            )

            message = BuyGbMessages.Info.DATA_SUMMARY.format(
                active_packages=summary["active_packages"],
                total_gb=summary["total_limit_gb"],
                used_gb=summary["total_used_gb"],
                remaining_gb=summary["remaining_gb"],
            )

            await query.edit_message_text(
                text=message,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en view_data_summary: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

    async def data_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el consumo de datos del usuario."""
        user_id = update.effective_user.id
        logger.info(f"💾 /data ejecutado por usuario {user_id}")

        try:
            summary = await self.data_package_service.get_user_data_summary(
                user_id=user_id, current_user_id=user_id
            )

            if (
                summary["active_packages"] == 0
                and summary["free_plan"]["remaining_gb"] <= 0
            ):
                message = BuyGbMessages.Data.NO_DATA
            else:
                message = BuyGbMessages.Data.DATA_INFO(summary)

            await update.message.reply_text(text=message, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error en data_handler: {e}")
            await update.message.reply_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR, parse_mode="Markdown"
            )


def get_buy_gb_handlers(data_package_service: DataPackageService):
    handler = BuyGbHandler(data_package_service)

    return [
        MessageHandler(filters.Regex("^📦 Comprar GB$"), handler.show_packages),
        CommandHandler("buy", handler.show_packages),
        CommandHandler("packages", handler.show_packages),
        CommandHandler("data", handler.data_handler),
    ]


def get_buy_gb_callback_handlers(data_package_service: DataPackageService):
    handler = BuyGbHandler(data_package_service)

    return [
        CallbackQueryHandler(handler.show_packages, pattern="^buy_gb_menu$"),
        CallbackQueryHandler(handler.buy_package, pattern="^buy_package_"),
        CallbackQueryHandler(handler.view_data_summary, pattern="^view_data_summary$"),
        CallbackQueryHandler(handler.show_slots_menu, pattern="^buy_slots_menu$"),
        CallbackQueryHandler(handler.buy_slots, pattern="^buy_slots_"),
    ]


def get_buy_gb_payment_handlers(data_package_service: DataPackageService):
    handler = BuyGbHandler(data_package_service)

    return [
        PreCheckoutQueryHandler(handler.pre_checkout_callback),
        MessageHandler(filters.SUCCESSFUL_PAYMENT, handler.successful_payment),
    ]
