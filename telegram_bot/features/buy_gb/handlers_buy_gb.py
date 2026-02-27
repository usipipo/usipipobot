"""
Handlers para compra de GB con Telegram Stars.

Author: uSipipo Team
Version: 1.1.0
"""

import os

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
from config import settings
from telegram_bot.features.user_management.keyboards_user_management import (
    UserManagementKeyboards,
)
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

        if not update.effective_user:
            return

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
            elif update.message:
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
            elif update.message:
                await update.message.reply_text(
                    text=error_message,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )

    async def buy_package(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    async def select_payment_method(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra opciones de método de pago para un paquete."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

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

            message = BuyGbMessages.Payment.SELECT_METHOD.format(
                package_name=package_option.name,
                gb_amount=package_option.data_gb,
                stars_price=package_option.stars,
                crypto_price=package_option.data_gb / 10,  # 1 USDT = 10 GB
            )

            keyboard = BuyGbKeyboards.payment_method_selection(package_type_str)

            await query.edit_message_text(
                text=message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error en select_payment_method: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

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
            logger.error(f"Error en pay_with_stars: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

    async def pay_with_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia pago con crypto usando TronDealer."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        if not update.effective_user:
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

            from application.services.common.container import get_service
            from application.services.crypto_payment_service import CryptoPaymentService
            from application.services.wallet_management_service import (
                WalletManagementService,
            )

            wallet_service = get_service(WalletManagementService)
            payment_service = get_service(CryptoPaymentService)

            wallet = await wallet_service.assign_wallet(
                user_id, label=f"user-{user_id}"
            )

            if not wallet:
                await query.edit_message_text(
                    text="❌ Error al asignar billetera. Intente nuevamente.",
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
                return

            usdt_amount = package_option.data_gb / 10

            order = await payment_service.create_order(
                user_id=user_id,
                package_type=package_option.package_type.value,
                amount_usdt=usdt_amount,
                wallet_address=wallet.address,
            )

            expires_minutes = 30

            # Generar QR de pago
            from utils.qr_generator import QrGenerator
            qr_filename = f"payment_{order.id}"
            qr_path = QrGenerator.generate_payment_qr(
                wallet_address=wallet.address,
                amount=usdt_amount,
                filename=qr_filename
            )

            message = f"""💰 *Pago con USDT - BSC*

Paquete: *{package_option.name}*
Cantidad: *{package_option.data_gb} GB*
Monto a pagar: *{usdt_amount} USDT*

📋 Wallet:
`{wallet.address}`

⏱️ Tiempo límite: *{expires_minutes} minutos*

⚠️ *Importante:*
• Escanea el QR con tu wallet o copia la dirección
• Envíe exactamente *{usdt_amount} USDT* (red BSC/BEP20)
• Espere al menos *15 confirmaciones* de la red
• No cierre esta pantalla hasta que el pago sea confirmado

✅ Una vez realizado el pago, el sistema detectará automáticamente la transacción."""

            if qr_path and os.path.exists(qr_path):
                # Enviar mensaje con QR
                await query.delete_message()
                with open(qr_path, "rb") as photo:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=message,
                        reply_markup=BuyGbKeyboards.back_to_packages(),
                        parse_mode="Markdown",
                    )
            else:
                await query.edit_message_text(
                    text=message,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )

            logger.info(
                f"💰 Crypto payment initiated: {package_option.name} ({usdt_amount} USDT) "
                f"for user {user_id}, wallet {wallet.address}, order {order.id}"
            )

        except Exception as e:
            logger.error(f"Error en pay_with_crypto: {e}", exc_info=True)
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
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

            # Calcular precio en USDT (aproximación: 1 USDT = 10 Stars)
            usdt_amount = slot_option.stars / 10

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

    async def pay_slots_with_stars(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
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
                title=BuyGbMessages.Slots.INVOICE_TITLE.format(
                    slots_name=slot_option.name
                ),
                description=BuyGbMessages.Slots.INVOICE_DESCRIPTION.format(slots=slots),
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(f"+{slots} Claves", slot_option.stars)],
            )

            logger.info(
                f"🔑 Invoice enviado: {slot_option.name} para usuario {user_id}"
            )

        except Exception as e:
            logger.error(f"Error en pay_slots_with_stars: {e}")
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

    async def pay_slots_with_crypto(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Inicia pago de slots con crypto usando TronDealer."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        if not update.effective_user:
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

            from application.services.common.container import get_service
            from application.services.crypto_payment_service import CryptoPaymentService
            from application.services.wallet_management_service import (
                WalletManagementService,
            )

            wallet_service = get_service(WalletManagementService)
            payment_service = get_service(CryptoPaymentService)

            wallet = await wallet_service.assign_wallet(
                user_id, label=f"user-{user_id}"
            )

            if not wallet:
                await query.edit_message_text(
                    text="❌ Error al asignar billetera. Intente nuevamente.",
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
                return

            # Calcular monto en USDT (aproximación: 1 USDT = 10 Stars)
            usdt_amount = slot_option.stars / 10

            # Crear orden de tipo "slots" para diferenciar de paquetes
            order = await payment_service.create_order(
                user_id=user_id,
                package_type=f"slots_{slots}",  # Formato especial para slots
                amount_usdt=usdt_amount,
                wallet_address=wallet.address,
            )

            expires_minutes = 30

            # Generar QR de pago
            from utils.qr_generator import QrGenerator
            qr_filename = f"payment_slots_{order.id}"
            qr_path = QrGenerator.generate_payment_qr(
                wallet_address=wallet.address,
                amount=usdt_amount,
                filename=qr_filename
            )

            message = f"""💰 *Pago de Slots con USDT - BSC*

🔑 Producto: *{slot_option.name}*
⭐ Precio original: {slot_option.stars} Stars
💰 Monto a pagar: *{usdt_amount:.2f} USDT*

📋 Wallet:
`{wallet.address}`

⏱️ Tiempo límite: *{expires_minutes} minutos*

⚠️ *Importante:*
• Escanea el QR con tu wallet o copia la dirección
• Envíe exactamente *{usdt_amount:.2f} USDT* (red BSC/BEP20)
• Espere al menos *15 confirmaciones* de la red
• No cierre esta pantalla hasta que el pago sea confirmado

✅ Una vez realizado el pago, el sistema detectará automáticamente la transacción y agregará las claves a tu cuenta."""

            if qr_path and os.path.exists(qr_path):
                # Enviar mensaje con QR
                await query.delete_message()
                with open(qr_path, "rb") as photo:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=message,
                        reply_markup=BuyGbKeyboards.back_to_packages(),
                        parse_mode="Markdown",
                    )
            else:
                await query.edit_message_text(
                    text=message,
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )

            logger.info(
                f"💰 Crypto payment for slots initiated: {slot_option.name} ({usdt_amount} USDT) "
                f"for user {user_id}, wallet {wallet.address}, order {order.id}"
            )

        except Exception as e:
            logger.error(f"Error en pay_slots_with_crypto: {e}", exc_info=True)
            await query.edit_message_text(
                text=BuyGbMessages.Error.SYSTEM_ERROR,
                reply_markup=BuyGbKeyboards.back_to_packages(),
                parse_mode="Markdown",
            )

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

    async def pre_checkout_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.pre_checkout_query
        if not query:
            return

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
        if not update.effective_user:
            return
        user_id = update.effective_user.id
        if not update.message or not update.message.successful_payment:
            return
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

                if update.message:
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
                if update.message:
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

            if update.message:
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
            if update.message:
                await update.message.reply_text(
                    text=BuyGbMessages.Error.PAYMENT_FAILED, parse_mode="Markdown"
                )

    async def view_data_summary(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return
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
        if not update.effective_user:
            return
        user_id = update.effective_user.id
        logger.info(f"💾 /data ejecutado por usuario {user_id}")

        query = update.callback_query
        is_callback = query is not None
        if is_callback and query:
            await query.answer()

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

            is_admin_menu = user_id == int(settings.ADMIN_ID)
            keyboard = UserManagementKeyboards.main_menu(is_admin=is_admin_menu)

            if is_callback and query:
                await query.edit_message_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en data_handler: {e}")
            error_msg = BuyGbMessages.Error.SYSTEM_ERROR
            if is_callback and query:
                await query.edit_message_text(text=error_msg, parse_mode="Markdown")
            elif update.message:
                await update.message.reply_text(text=error_msg, parse_mode="Markdown")


def get_buy_gb_handlers(data_package_service: DataPackageService):
    handler = BuyGbHandler(data_package_service)

    return [
        MessageHandler(filters.Regex("^📦 Comprar GB$"), handler.show_packages),
        CommandHandler("buy", handler.show_packages),
        CommandHandler("packages", handler.show_packages),
    ]


def get_buy_gb_callback_handlers(data_package_service: DataPackageService):
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
    handler = BuyGbHandler(data_package_service)

    return [
        PreCheckoutQueryHandler(handler.pre_checkout_callback),
        MessageHandler(filters.SUCCESSFUL_PAYMENT, handler.successful_payment),
    ]
