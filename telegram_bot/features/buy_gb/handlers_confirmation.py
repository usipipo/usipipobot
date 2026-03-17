"""
Handlers para confirmación y entrega de compras.

Author: uSipipo Team
Version: 1.2.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import ContextTypes

from application.services.common.container import get_service
from application.services.data_package_service import PACKAGE_OPTIONS, SLOT_OPTIONS
from config import settings
from utils.logger import logger

from .keyboards_buy_gb import BuyGbKeyboards
from .messages_buy_gb import BuyGbMessages


class ConfirmationMixin:
    """Mixin para confirmación y entrega de compras."""

    async def pre_checkout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                logger.info(f"🔑 Pre-checkout exitoso: +{slots} slots para usuario {user_id}")
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
            logger.info(f"📦 Pre-checkout exitoso: {package_option.name} para usuario {user_id}")

        except Exception as e:
            logger.error(f"Error en pre_checkout_callback: {e}")
            await query.answer(ok=False, error_message="Error procesando pago")

    async def successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

            # DETECT Mini App payments (prefix: miniapp_*)
            if payload.startswith("miniapp_"):
                logger.info(f"📱 Mini App payment detected: {payload} for user {user_id}")
                await self._handle_miniapp_successful_payment(
                    update, context, user_id, payment, payload
                )
                return

            # Handle old Mini App payments (backward compatibility)
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

                logger.info(f"🔑 Slots comprados exitosamente: +{slots} para usuario {user_id}")
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
                package_name=(package_option.name if package_option else package_type_str),
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
        Handle payments from Mini App users (backward compatibility).

        Mini App payments use format: data_package_TYPE_USERID_TXID or key_slots_N_USERID_TXID
        """
        try:
            telegram_payment_id = payment.telegram_payment_charge_id

            if payload.startswith("data_package_"):
                # Format: data_package_TYPE_USERID_TXID
                # Example: data_package_basic_12345_tx_abc123
                type_start = len("data_package_")
                remaining = payload[type_start:]
                remaining_parts = remaining.split("_")

                # Last 3 parts are: {user_id}_{tx_prefix}_{tx_value}
                # Everything before is the package type
                if len(remaining_parts) >= 4:
                    # tx_id is the last two parts joined (tx_abc123)
                    # user_id is third from last
                    # type is everything before user_id
                    _ = int(remaining_parts[-3])  # parsed_user_id (validated via user_id param)
                    package_type_str = "_".join(remaining_parts[:-3])

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
                # Example: key_slots_5_12345_tx_def456
                type_start = len("key_slots_")
                remaining = payload[type_start:]
                remaining_parts = remaining.split("_")

                # Format: {slots}_{user_id}_{tx_prefix}_{tx_value}
                if len(remaining_parts) >= 4:
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

                    logger.info(f"🔑 Mini App slots purchased: +{slots} for user {user_id}")

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

    async def _handle_miniapp_successful_payment(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        payment,
        payload: str,
    ):
        """
        Handle successful payment from Mini App.

        For Mini App payments, we process the payment normally
        (create package, add slots, activate subscription).
        The Mini App will detect completion via polling.

        Send confirmation message with Mini App link.

        Args:
            update: Telegram update object
            context: Telegram context object
            user_id: User ID from effective_user
            payment: SuccessfulPayment object
            payload: Invoice payload string with format:
                - miniapp_data_package_{type}_{user_id}_{tx_id}
                - miniapp_key_slots_{slots}_{user_id}_{tx_id}
                - miniapp_subscription_{plan}_{user_id}_{tx_id}
        """
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            # Parse payload to determine product type

            if payload.startswith("miniapp_data_package_"):
                # Handle package purchase
                # Format: miniapp_data_package_{type}_{user_id}_{tx_id}
                # Example: miniapp_data_package_basic_12345_tx_abc123
                type_start = len("miniapp_data_package_")
                remaining = payload[type_start:]
                remaining_parts = remaining.split("_")

                # Last two parts are user_id and tx_id (tx_id may have underscores)
                # We need to extract: type, user_id, tx_id
                # Format: {type}_{user_id}_{tx_prefix}_{tx_value}
                if len(remaining_parts) >= 4:
                    # tx_id is the last two parts joined (tx_abc123)
                    tx_id = f"{remaining_parts[-2]}_{remaining_parts[-1]}"
                    # user_id is third from last (validated via user_id parameter)
                    _ = int(remaining_parts[-3])
                    # type is everything before user_id
                    package_type_str = "_".join(remaining_parts[:-3])

                    telegram_payment_id = f"miniapp_{tx_id}"

                    # Process package purchase (normal flow)
                    package, bonus_breakdown = await self.data_package_service.purchase_package(
                        user_id=user_id,
                        package_type=package_type_str,
                        telegram_payment_id=telegram_payment_id,
                        current_user_id=user_id,
                    )

                    logger.info(
                        f"✅ Mini App package purchased: {package_type_str} for user {user_id}"
                    )

            elif payload.startswith("miniapp_key_slots_"):
                # Handle slots purchase
                # Format: miniapp_key_slots_{slots}_{user_id}_{tx_id}
                # Example: miniapp_key_slots_5_12345_tx_def456
                type_start = len("miniapp_key_slots_")
                remaining = payload[type_start:]
                remaining_parts = remaining.split("_")

                # Format: {slots}_{user_id}_{tx_prefix}_{tx_value}
                if len(remaining_parts) >= 4:
                    slots = int(remaining_parts[0])
                    # tx_id is the last two parts joined (tx_def456)
                    tx_id = f"{remaining_parts[-2]}_{remaining_parts[-1]}"

                    telegram_payment_id = f"miniapp_{tx_id}"

                    # Process slots purchase (normal flow)
                    await self.data_package_service.purchase_key_slots(
                        user_id=user_id,
                        slots=slots,
                        telegram_payment_id=telegram_payment_id,
                        current_user_id=user_id,
                    )

                    logger.info(f"✅ Mini App slots purchased: +{slots} for user {user_id}")

            elif payload.startswith("miniapp_subscription_"):
                # Handle subscription purchase
                # Format: miniapp_subscription_{plan}_{user_id}_{tx_id}
                # Example: miniapp_subscription_one_month_12345_tx_ghi789
                from application.services.subscription_service import SubscriptionService

                type_start = len("miniapp_subscription_")
                remaining = payload[type_start:]
                remaining_parts = remaining.split("_")

                # Format: {plan}_{user_id}_{tx_prefix}_{tx_value}
                # Plan could be multi-part like "one_month"
                if len(remaining_parts) >= 4:
                    # tx_id is the last two parts joined (tx_ghi789)
                    tx_id = f"{remaining_parts[-2]}_{remaining_parts[-1]}"
                    # user_id is third from last (validated via user_id parameter)
                    _ = int(remaining_parts[-3])
                    # plan is everything before user_id
                    plan_type = "_".join(remaining_parts[:-3])

                    payment_id = f"miniapp_{tx_id}"

                    # Get subscription service
                    subscription_service = get_service(SubscriptionService)

                    # Get plan details
                    plan_option = subscription_service.get_plan_option(plan_type)

                    # Activate subscription
                    await subscription_service.activate_subscription(
                        user_id=user_id,
                        plan_type=plan_type,
                        stars_paid=plan_option.stars if plan_option else 0,
                        payment_id=payment_id,
                        current_user_id=user_id,
                    )

                    logger.info(
                        f"✅ Mini App subscription activated: {plan_type} for user {user_id}"
                    )

            # Send confirmation message with Mini App link
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🚀 Abrir Mini App", url=f"https://t.me/{settings.BOT_USERNAME}/app"
                        )
                    ]
                ]
            )

            await update.message.reply_text(
                text=(
                    "✅ *¡Pago Recibido!*\n\n"
                    "Tu pago ha sido procesado exitosamente.\n\n"
                    "📱 _Abre la Mini App para ver tu producto activado._"
                ),
                parse_mode="Markdown",
                reply_markup=keyboard,
            )

            logger.info(f"📬 Sent confirmation to user {user_id} for Mini App payment")

        except Exception as e:
            logger.error(f"Error in _handle_miniapp_successful_payment: {e}", exc_info=True)
            # Still send confirmation - payment was successful
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            await update.message.reply_text(
                text=(
                    "✅ *Pago Procesado*\n\n"
                    "Tu pago fue exitoso. Abre la Mini App para ver los detalles."
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🚀 Abrir Mini App", url=f"https://t.me/{settings.BOT_USERNAME}/app"
                            )
                        ]
                    ]
                ),
            )
