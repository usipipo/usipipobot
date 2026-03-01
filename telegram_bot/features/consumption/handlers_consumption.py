"""
Handlers para el módulo de tarifa por consumo (Pay-as-You-Go).

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from application.services.consumption_billing_service import (
    ConsumptionBillingService,
)
from application.services.consumption_invoice_service import (
    ConsumptionInvoiceService,
    PaymentMethod,
)
from domain.entities.consumption_invoice import ConsumptionInvoice
from telegram_bot.features.consumption.keyboards_consumption import (
    ConsumptionKeyboards,
)
from telegram_bot.features.consumption.messages_consumption import (
    ConsumptionMessages,
)
from utils.logger import logger
from utils.telegram_utils import TelegramUtils


class ConsumptionHandler:
    """Handler para la tarifa por consumo."""

    def __init__(
        self,
        billing_service: ConsumptionBillingService,
        invoice_service: ConsumptionInvoiceService,
    ):
        self.billing_service = billing_service
        self.invoice_service = invoice_service
        logger.info("⚡ ConsumptionHandler inicializado")

    async def show_consumption_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el menú principal de tarifa por consumo."""
        query = update.callback_query
        if query:
            await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            # Obtener estado del usuario
            summary = await self.billing_service.get_current_consumption(
                user_id, user_id
            )

            has_active_cycle = summary is not None and summary.is_active
            has_pending_debt = (
                summary is not None and not summary.is_active
                and summary.billing_id is not None
            )
            can_activate, _ = await self.billing_service.can_activate_consumption(
                user_id, user_id
            )

            # Determinar mensaje de estado
            if has_pending_debt:
                status_text = ConsumptionMessages.Menu.STATUS_DEBT
            elif has_active_cycle:
                status_text = ConsumptionMessages.Menu.STATUS_ACTIVE
            else:
                status_text = ConsumptionMessages.Menu.STATUS_INACTIVE

            message = ConsumptionMessages.Menu.MAIN_MENU.format(
                status_text=status_text
            )

            keyboard = ConsumptionKeyboards.consumption_main_menu(
                has_active_cycle=has_active_cycle,
                has_pending_debt=has_pending_debt,
                can_activate=can_activate
            )

            if query:
                await TelegramUtils.safe_edit_message(
                    query, context, text=message, reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en show_consumption_menu: {e}")
            await self._send_error_message(update, context)

    async def start_activation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Inicia el flujo de activación del modo consumo."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            # Verificar que puede activar
            can_activate, error_msg = await self.billing_service.can_activate_consumption(
                user_id, user_id
            )

            if not can_activate:
                message = ConsumptionMessages.Activation.CANNOT_ACTIVATE.format(
                    reason=error_msg or "No cumples los requisitos"
                )
                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )
                return

            # Mostrar advertencia y términos
            message = (
                ConsumptionMessages.Activation.WARNING_HEADER + "\n\n" +
                ConsumptionMessages.Activation.get_terms_and_conditions() + "\n\n" +
                ConsumptionMessages.Activation.get_price_example() + "\n\n" +
                ConsumptionMessages.Activation.CONFIRMATION_PROMPT
            )

            await query.edit_message_text(
                text=message,
                reply_markup=ConsumptionKeyboards.activation_confirmation(),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error en start_activation: {e}")
            await self._send_error_message(update, context)

    async def confirm_activation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Confirma la activación del modo consumo."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            result = await self.billing_service.activate_consumption_mode(
                user_id, user_id
            )

            if result.success:
                await query.edit_message_text(
                    text=ConsumptionMessages.Activation.get_success_message(),
                    reply_markup=ConsumptionKeyboards.activation_success(),
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Usuario {user_id} activó modo consumo")
            else:
                message = ConsumptionMessages.Activation.CANNOT_ACTIVATE.format(
                    reason=result.error_message or "Error desconocido"
                )
                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en confirm_activation: {e}")
            await self._send_error_message(update, context)

    async def view_my_consumption(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el consumo actual del usuario."""
        query = update.callback_query
        if query:
            await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            summary = await self.billing_service.get_current_consumption(
                user_id, user_id
            )

            if not summary:
                # No tiene ciclo activo
                message = ConsumptionMessages.ConsumptionStatus.NO_ACTIVE_CYCLE
                keyboard = ConsumptionKeyboards.view_info_only()
            elif summary.is_active:
                # Ciclo activo
                days_remaining = max(0, 30 - summary.days_active)
                message = ConsumptionMessages.ConsumptionStatus.ACTIVE_CYCLE.format(
                    days_active=summary.days_active,
                    consumption_formatted=summary.formatted_consumption,
                    cost_formatted=summary.formatted_cost,
                    days_remaining=days_remaining
                )
                keyboard = ConsumptionKeyboards.back_to_consumption_menu()
            else:
                # Ciclo cerrado (deuda)
                message = ConsumptionMessages.ConsumptionStatus.CLOSED_CYCLE.format(
                    consumption_formatted=summary.formatted_consumption,
                    cost_formatted=summary.formatted_cost
                )
                keyboard = ConsumptionKeyboards.consumption_main_menu(
                    has_active_cycle=False,
                    has_pending_debt=True,
                    can_activate=False
                )

            if query:
                await TelegramUtils.safe_edit_message(
                    query, context, text=message, reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en view_my_consumption: {e}")
            await self._send_error_message(update, context)

    async def start_invoice_generation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Inicia la generación de factura (selección de método de pago)."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            # Verificar que puede generar factura
            can_generate, error_msg = await self.invoice_service.can_generate_invoice(
                user_id, user_id
            )

            if not can_generate:
                await query.edit_message_text(
                    text=ConsumptionMessages.Error.INVOICE_GENERATION.format(
                        reason=error_msg or "No puedes generar factura"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )
                return

            # Obtener resumen de consumo
            summary = await self.billing_service.get_current_consumption(user_id, user_id)

            if not summary:
                await query.edit_message_text(
                    text=ConsumptionMessages.Error.INVOICE_GENERATION.format(
                        reason="No se encontró información de consumo"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )
                return

            # Mostrar selección de método de pago
            message = ConsumptionMessages.Invoice.SELECT_PAYMENT_METHOD.format(
                consumption_formatted=summary.formatted_consumption,
                cost_formatted=summary.formatted_cost
            )

            await query.edit_message_text(
                text=message,
                reply_markup=ConsumptionKeyboards.payment_method_selection(
                    consumption_formatted=summary.formatted_consumption,
                    cost_formatted=summary.formatted_cost
                ),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error en start_invoice_generation: {e}")
            await self._send_error_message(update, context)

    async def generate_invoice_stars(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Genera factura para pago con Telegram Stars."""
        await self._generate_invoice(update, context, PaymentMethod.STARS)

    async def generate_invoice_crypto(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Genera factura para pago con Crypto."""
        query = update.callback_query
        if query:
            await query.answer("Preparando wallet de pago...")

        # Para crypto necesitamos obtener una wallet
        from application.services.wallet_management_service import (
            WalletManagementService,
        )
        from application.services.common.container import get_service

        try:
            wallet_service = get_service(WalletManagementService)
            if not update.effective_user:
                return

            user_id = update.effective_user.id

            # Obtener usuario para el servicio de wallet
            from domain.interfaces.iuser_repository import IUserRepository
            from application.services.common.container import get_service

            user_repo = get_service(IUserRepository)
            user = await user_repo.get_by_id(user_id, user_id)

            if not user:
                if query:
                    await query.edit_message_text(
                        text="❌ Usuario no encontrado.",
                        reply_markup=ConsumptionKeyboards.back_to_consumption_menu()
                    )
                return

            wallet = await wallet_service.get_or_create_wallet(user)

            if not wallet:
                if query:
                    await query.edit_message_text(
                        text="❌ Error al preparar la wallet de pago. Intenta nuevamente.",
                        reply_markup=ConsumptionKeyboards.back_to_consumption_menu()
                    )
                return

            await self._generate_invoice(
                update, context, PaymentMethod.CRYPTO, wallet.address
            )

        except Exception as e:
            logger.error(f"Error obteniendo wallet: {e}")
            if query:
                await query.edit_message_text(
                    text="❌ Error al preparar el pago. Intenta nuevamente.",
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu()
                )

    async def _generate_invoice(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        payment_method: PaymentMethod,
        wallet_address: str = "N/A"
    ):
        """Genera la factura con el método de pago seleccionado."""
        query = update.callback_query
        if not query:
            return

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            result = await self.invoice_service.generate_invoice(
                user_id=user_id,
                payment_method=payment_method,
                wallet_address=wallet_address,
                current_user_id=user_id
            )

            if not result.success or not result.invoice:
                await query.edit_message_text(
                    text=ConsumptionMessages.Error.INVOICE_GENERATION.format(
                        reason=result.error_message or "Error desconocido"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )
                return

            invoice = result.invoice
            summary = await self.billing_service.get_current_consumption(user_id, user_id)

            # Mostrar instrucciones según método de pago
            if payment_method == PaymentMethod.STARS:
                # Crear invoice de Telegram
                await self._send_stars_invoice(update, context, invoice, summary)
            else:
                # Mostrar instrucciones de pago crypto
                message = ConsumptionMessages.Invoice.CRYPTO_PAYMENT.format(
                    consumption_formatted=summary.formatted_consumption if summary else "N/A",
                    cost_formatted=invoice.get_formatted_amount(),
                    wallet_address=wallet_address,
                    time_remaining=invoice.time_remaining_formatted
                )
                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en _generate_invoice: {e}")
            await self._send_error_message(update, context)

    async def _send_stars_invoice(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        invoice: ConsumptionInvoice,
        summary
    ):
        """Envía el invoice de Telegram Stars."""
        query = update.callback_query
        if not query or not update.effective_chat:
            return

        try:
            from telegram import LabeledPrice

            stars_amount = invoice.get_stars_amount()

            payload = f"consumption_invoice_{invoice.id}_{invoice.user_id}"

            await context.bot.send_invoice(
                chat_id=update.effective_chat.id,
                title="Pago de Tarifa por Consumo",
                description=f"Consumo: {summary.formatted_consumption if summary else 'N/A'}",
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice("Consumo VPN", stars_amount)]
            )

            # Borrar mensaje anterior
            await query.delete_message()

        except Exception as e:
            logger.error(f"Error enviando invoice de Stars: {e}")
            await query.edit_message_text(
                text="❌ Error al generar el pago con Stars. Intenta con Crypto.",
                reply_markup=ConsumptionKeyboards.back_to_consumption_menu()
            )

    async def show_info(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra información sobre el modo consumo."""
        query = update.callback_query
        if query:
            await query.answer()

        message = (
            ConsumptionMessages.Activation.get_terms_and_conditions() + "\n\n" +
            ConsumptionMessages.Activation.get_price_example()
        )

        if query:
            await query.edit_message_text(
                text=message,
                reply_markup=ConsumptionKeyboards.view_info_only(),
                parse_mode="Markdown"
            )
        elif update.message:
            await update.message.reply_text(
                text=message,
                reply_markup=ConsumptionKeyboards.view_info_only(),
                parse_mode="Markdown"
            )

    async def start_cancellation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Inicia el flujo de cancelación del modo consumo."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            # Verificar que puede cancelar
            can_cancel, error_msg = await self.billing_service.can_cancel_consumption(
                user_id, user_id
            )

            if not can_cancel:
                await query.edit_message_text(
                    text=ConsumptionMessages.Cancellation.CANNOT_CANCEL.format(
                        reason=error_msg or "No puedes cancelar el modo consumo"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )
                return

            # Obtener resumen de consumo actual
            summary = await self.billing_service.get_current_consumption(
                user_id, user_id
            )

            if not summary:
                await query.edit_message_text(
                    text=ConsumptionMessages.Cancellation.CANNOT_CANCEL.format(
                        reason="No se pudo obtener tu información de consumo"
                    ),
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )
                return

            # Mostrar confirmación con resumen
            message = (
                ConsumptionMessages.Cancellation.CONFIRMATION_HEADER + "\n\n" +
                ConsumptionMessages.Cancellation.get_cancellation_summary(
                    days_active=summary.days_active,
                    consumption_formatted=summary.formatted_consumption,
                    cost_formatted=summary.formatted_cost
                )
            )

            await query.edit_message_text(
                text=message,
                reply_markup=ConsumptionKeyboards.cancellation_confirmation(),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error en start_cancellation: {e}")
            await self._send_error_message(update, context)

    async def confirm_cancellation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Confirma la cancelación del modo consumo."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        if not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            result = await self.billing_service.cancel_consumption_mode(
                user_id, user_id
            )

            if result.success:
                # Formatear consumo y costo para el mensaje
                from decimal import Decimal
                if result.mb_consumed < Decimal("1024"):
                    consumption_formatted = f"{result.mb_consumed:.2f} MB"
                else:
                    gb_consumed = result.mb_consumed / Decimal("1024")
                    consumption_formatted = f"{gb_consumed:.2f} GB"

                cost_formatted = f"${result.total_cost_usd:.2f} USD"

                # Mensaje diferenciado según haya deuda o no
                if result.had_debt:
                    # Hay deuda - mostrar mensaje con resumen y bloqueo
                    message = ConsumptionMessages.Cancellation.SUCCESS + "\n\n" + \
                        f"📊 **Resumen del ciclo cancelado:**\n" + \
                        f"📅 Días activos: {result.days_active}/30\n" + \
                        f"📈 Consumo: {consumption_formatted}\n" + \
                        f"💰 Costo: {cost_formatted}"
                else:
                    # No hay deuda - mensaje simplificado sin bloqueo
                    message = (
                        "✅ **Modo Consumo Cancelado**\n\n"
                        "Se ha cerrado tu ciclo de consumo.\n"
                        "Como no realizaste ningún consumo, no hay nada que pagar.\n\n"
                        "🔓 **Tus claves VPN siguen activas** y puedes seguir navegando "
                        "con tu plan gratuito."
                    )

                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.cancel_success_keyboard(),
                    parse_mode="Markdown"
                )
                logger.info(f"✅ Usuario {user_id} canceló modo consumo (had_debt={result.had_debt})")
            else:
                message = ConsumptionMessages.Cancellation.CANNOT_CANCEL.format(
                    reason=result.error_message or "Error desconocido"
                )
                await query.edit_message_text(
                    text=message,
                    reply_markup=ConsumptionKeyboards.back_to_consumption_menu(),
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en confirm_cancellation: {e}")
            await self._send_error_message(update, context)

    async def _send_error_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Envía mensaje de error genérico."""
        keyboard = ConsumptionKeyboards.back_to_consumption_menu()

        if update.callback_query:
            await TelegramUtils.safe_edit_message(
                update.callback_query, context,
                text=ConsumptionMessages.Error.GENERIC,
                reply_markup=keyboard
            )
        elif update.message:
            await update.message.reply_text(
                text=ConsumptionMessages.Error.GENERIC,
                reply_markup=keyboard
            )


def get_consumption_handlers(
    billing_service: ConsumptionBillingService,
    invoice_service: ConsumptionInvoiceService
):
    """Retorna los handlers para el módulo de consumo."""
    handler = ConsumptionHandler(billing_service, invoice_service)

    return [
        CommandHandler("consumption", handler.show_consumption_menu),
        CommandHandler("mi_consumo", handler.view_my_consumption),
    ]


def get_consumption_callback_handlers(
    billing_service: ConsumptionBillingService,
    invoice_service: ConsumptionInvoiceService
):
    """Retorna los callback handlers para el módulo de consumo."""
    handler = ConsumptionHandler(billing_service, invoice_service)

    return [
        CallbackQueryHandler(
            handler.show_consumption_menu, pattern="^consumption_menu$"
        ),
        CallbackQueryHandler(
            handler.start_activation, pattern="^consumption_activate$"
        ),
        CallbackQueryHandler(
            handler.confirm_activation, pattern="^consumption_confirm_activate$"
        ),
        CallbackQueryHandler(
            handler.view_my_consumption, pattern="^consumption_view_status$"
        ),
        CallbackQueryHandler(
            handler.start_invoice_generation,
            pattern="^consumption_generate_invoice$"
        ),
        CallbackQueryHandler(
            handler.generate_invoice_stars, pattern="^consumption_pay_stars$"
        ),
        CallbackQueryHandler(
            handler.generate_invoice_crypto, pattern="^consumption_pay_crypto$"
        ),
        CallbackQueryHandler(
            handler.show_info, pattern="^consumption_info$"
        ),
        CallbackQueryHandler(
            handler.start_cancellation, pattern="^consumption_cancel$"
        ),
        CallbackQueryHandler(
            handler.confirm_cancellation, pattern="^consumption_confirm_cancel$"
        ),
    ]
