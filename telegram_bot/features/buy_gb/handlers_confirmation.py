"""
Handlers para confirmación y entrega de compras.

Author: uSipipo Team
Version: 1.2.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import ContextTypes

from application.services.data_package_service import PACKAGE_OPTIONS, SLOT_OPTIONS
from utils.logger import logger

from .keyboards_buy_gb import BuyGbKeyboards
from .messages_buy_gb import BuyGbMessages


class ConfirmationMixin:
    """Mixin para confirmación y entrega de compras."""

    async def pre_checkout_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Valida el pre-checkout antes del pago."""
        query = update.pre_checkout_query
        if not query:
            return

        try:
            payload = query.invoice_payload
            parts = payload.split("_")

            # Handle Mini App payments (format: data_package_TYPE_USERID_TXID or key_slots_N_USERID_TXID)
            if payload.startswith("data_package_") or payload.startswith("key_slots_"):
                await query.answer(ok=True)
                logger.info(f"📦 Pre-checkout Mini App: {payload}")
                return

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
        """Procesa el pago exitoso y entrega el producto."""
        if not update.effective_user:
            return
        user_id = update.effective_user.id
        if not update.message or not update.message.successful_payment:
            return
        payment = update.message.successful_payment

        try:
            payload = payment.invoice_payload
            parts = payload.split("_")

            # Handle Mini App payments
            if payload.startswith("data_package_") or payload.startswith("key_slots_"):
                await self._handle_miniapp_payment(
                    update, context, user_id, payment, payload, parts
                )
                return

            # Handle regular bot payments
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

            package_result = await self.data_package_service.purchase_package(
                user_id=user_id,
                package_type=package_type_str,
                telegram_payment_id=telegram_payment_id,
                current_user_id=user_id,
            )
            package = package_result[0]

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

    async def _handle_miniapp_payment(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        payment,
        payload: str,
        parts: list,
    ):
        """
        Handle payments from Mini App users.
        
        Mini App payments use format: data_package_TYPE_USERID_TXID or key_slots_N_USERID_TXID
        """
        try:
            telegram_payment_id = payment.telegram_payment_charge_id

            if payload.startswith("data_package_"):
                # Format: data_package_TYPE_USERID_TXID
                # Extract package type (could be multi-part like "basic_premium")
                type_start = len("data_package_")
                remaining = payload[type_start:]
                remaining_parts = remaining.split("_")
                
                # Last two parts are user_id and transaction_id
                if len(remaining_parts) >= 3:
                    package_type_str = "_".join(remaining_parts[:-2])
                    
                    package_result = await self.data_package_service.purchase_package(
                        user_id=user_id,
                        package_type=package_type_str,
                        telegram_payment_id=telegram_payment_id,
                        current_user_id=user_id,
                    )
                    package = package_result[0]

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
                    expires_at = (
                        package.expires_at.strftime("%d/%m/%Y %H:%M")
                        if package.expires_at
                        else "N/A"
                    )

                    success_message = (
                        f"✅ *¡Pago desde Mini App Confirmado!*\n\n"
                        f"📦 Paquete: *{package_option.name if package_option else package_type_str}*\n"
                        f"💾 Datos: *{package_option.data_gb if package_option else 'N/A'} GB{bonus_text}*\n"
                        f"⭐ Stars: *{payment.total_amount}*\n"
                        f"📅 Expira: *{expires_at}*\n\n"
                        f"Tu paquete ha sido activado inmediatamente.\n"
                        f"Revisa tu sección de claves VPN."
                    )

                    if update.message:
                        await update.message.reply_text(
                            text=success_message,
                            parse_mode="Markdown",
                        )

                    logger.info(
                        f"📦 Mini App package purchased: {package_type_str} for user {user_id}"
                    )

            elif payload.startswith("key_slots_"):
                # Format: key_slots_N_USERID_TXID
                # Extract slots count (could be multi-digit)
                type_start = len("key_slots_")
                remaining = payload[type_start:]
                remaining_parts = remaining.split("_")
                
                if len(remaining_parts) >= 2:
                    slots = int(remaining_parts[0])

                    result = await self.data_package_service.purchase_key_slots(
                        user_id=user_id,
                        slots=slots,
                        telegram_payment_id=telegram_payment_id,
                        current_user_id=user_id,
                    )

                    success_message = (
                        f"✅ *¡Pago desde Mini App Confirmado!*\n\n"
                        f"🔑 Slots: *+{result['slots_added']} claves*\n"
                        f"🎯 Nuevo límite: *{result['new_max_keys']} claves*\n"
                        f"⭐ Stars: *{payment.total_amount}*\n\n"
                        f"Tu límite de claves ha sido aumentado.\n"
                        f"Puedes crear nuevas claves desde la Mini App."
                    )

                    if update.message:
                        await update.message.reply_text(
                            text=success_message,
                            parse_mode="Markdown",
                        )

                    logger.info(
                        f"🔑 Mini App slots purchased: +{slots} for user {user_id}"
                    )

        except Exception as e:
            logger.error(f"Error in _handle_miniapp_payment: {e}", exc_info=True)
            if update.message:
                await update.message.reply_text(
                    text=(
                        "⚠️ *Pago recibido pero hubo un error*\n\n"
                        "Tu pago fue procesado correctamente, pero hubo un problema "
                        "activando el producto. Contacta a soporte si el problema persiste."
                    ),
                    parse_mode="Markdown",
                )
