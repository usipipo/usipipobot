"""
Handlers para pagos con Crypto (USDT/BSC).

Author: uSipipo Team
Version: 1.2.0 - Refactored into mixins
"""

import os

from telegram import Update
from telegram.ext import ContextTypes

from application.services.data_package_service import PACKAGE_OPTIONS, SLOT_OPTIONS
from utils.logger import logger
from utils.telegram_utils import TelegramUtils

from .keyboards_buy_gb import BuyGbKeyboards
from .messages_buy_gb import BuyGbMessages


class PaymentCryptoMixin:
    """Mixin para procesamiento de pagos con Crypto."""

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
            from application.services.wallet_management_service import WalletManagementService

            wallet_service = get_service(WalletManagementService)
            payment_service = get_service(CryptoPaymentService)

            wallet = await wallet_service.assign_wallet(user_id, label=f"user-{user_id}")

            if not wallet:
                await query.edit_message_text(
                    text="❌ Error al asignar billetera. Intente nuevamente.",
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
                return

            # Tasa: 1 USDT = 120 Stars
            usdt_amount = package_option.stars / 120

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
                wallet_address=wallet.address, amount=usdt_amount, filename=qr_filename
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
                if update.effective_chat:
                    with open(qr_path, "rb") as photo:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=photo,
                            caption=message,
                            reply_markup=BuyGbKeyboards.back_to_packages(),
                            parse_mode="Markdown",
                        )
            else:
                await TelegramUtils.safe_edit_message(
                    query,
                    context,
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

    async def pay_slots_with_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            from application.services.wallet_management_service import WalletManagementService
            from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository

            wallet_service = get_service(WalletManagementService)
            payment_service = get_service(CryptoPaymentService)
            user_repo = get_service(PostgresUserRepository)

            user = await user_repo.get_by_id(user_id, current_user_id=user_id)
            if not user:
                await query.edit_message_text(
                    text="❌ Error: Usuario no encontrado.",
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
                return

            wallet = await wallet_service.get_or_create_wallet(user)

            if not wallet:
                await query.edit_message_text(
                    text="❌ Error al asignar billetera. Intente nuevamente.",
                    reply_markup=BuyGbKeyboards.back_to_packages(),
                    parse_mode="Markdown",
                )
                return

            # Calcular monto en USDT (tasa: 1 USDT = 120 Stars)
            usdt_amount = slot_option.stars / 120

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
                wallet_address=wallet.address, amount=usdt_amount, filename=qr_filename
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
                if update.effective_chat:
                    with open(qr_path, "rb") as photo:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=photo,
                            caption=message,
                            reply_markup=BuyGbKeyboards.back_to_packages(),
                            parse_mode="Markdown",
                        )
            else:
                await TelegramUtils.safe_edit_message(
                    query,
                    context,
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
