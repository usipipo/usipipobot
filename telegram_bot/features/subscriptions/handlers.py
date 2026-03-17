"""
Handlers para gestión de suscripciones Premium.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from application.services.common.container import get_service
from application.services.subscription_service import SubscriptionService
from config import settings
from utils.logger import logger

from .keyboards import SubscriptionKeyboards
from .messages import SubscriptionMessages

__all__ = [
    "SubscriptionHandler",
    "get_subscription_handlers",
    "get_subscription_callback_handlers",
]


class SubscriptionHandler:
    """Handler para gestión de suscripciones Premium."""

    def __init__(self, subscription_service: SubscriptionService):
        self.subscription_service = subscription_service
        logger.info("💎 SubscriptionHandler inicializado")

    async def show_subscriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show subscription menu."""
        user_id = update.effective_user.id

        try:
            # Check if user has active subscription
            is_premium = await self.subscription_service.is_premium_user(user_id, settings.ADMIN_ID)
            subscription = await self.subscription_service.get_user_subscription(
                user_id, settings.ADMIN_ID
            )

            if is_premium and subscription:
                days_remaining = subscription.days_remaining
                message = SubscriptionMessages.Menu.menu(
                    is_premium=True, days_remaining=days_remaining
                )
                keyboard = SubscriptionKeyboards.active_subscription()
            else:
                message = SubscriptionMessages.Menu.menu(is_premium=False)
                keyboard = SubscriptionKeyboards.subscription_menu()

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error showing subscriptions: {e}")
            error_msg = "❌ Error al cargar suscripciones. Inténtalo de nuevo."
            if update.callback_query:
                await update.callback_query.answer(error_msg, show_alert=True)
            else:
                await update.message.reply_text(error_msg)

    async def select_payment_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra opciones de método de pago para una suscripción."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        # Extraer plan_type de select_sub_payment_{plan_type}
        plan_type = query.data.replace("select_sub_payment_", "")

        try:
            plan_option = self.subscription_service.get_plan_option(plan_type)
            if not plan_option:
                await query.edit_message_text(
                    text="❌ Plan no válido",
                    reply_markup=SubscriptionKeyboards.subscription_menu(),
                    parse_mode="Markdown",
                )
                return

            message = SubscriptionMessages.Payment.select_method(
                plan_name=plan_option.name,
                stars=plan_option.stars,
                usdt=plan_option.usdt,
                duration=plan_option.duration_months * 30,
            )

            keyboard = SubscriptionKeyboards.sub_payment_method_selection(plan_type)

            await query.edit_message_text(
                text=message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error en select_payment_method: {e}")
            await query.edit_message_text(
                text="❌ Error al cargar métodos de pago",
                reply_markup=SubscriptionKeyboards.subscription_menu(),
                parse_mode="Markdown",
            )

    async def pay_with_stars(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa pago de suscripción con Telegram Stars."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        plan_type = query.data.replace("pay_sub_stars_", "")
        user_id = update.effective_user.id

        try:
            plan_option = self.subscription_service.get_plan_option(plan_type)
            if not plan_option:
                await query.answer("❌ Plan no válido", show_alert=True)
                return

            # Check for existing subscription
            is_premium = await self.subscription_service.is_premium_user(user_id, settings.ADMIN_ID)
            if is_premium:
                await query.answer(
                    "⚠️ Ya tienes una suscripción activa",
                    show_alert=True,
                )
                return

            # TODO: Implement Telegram Stars invoice
            # Por ahora, simulamos activación directa
            payment_id = f"sub_stars_{user_id}_{plan_type}"

            subscription = await self.subscription_service.activate_subscription(
                user_id=user_id,
                plan_type=plan_type,
                stars_paid=plan_option.stars,
                payment_id=payment_id,
                current_user_id=settings.ADMIN_ID,
            )

            expires_at = subscription.expires_at.strftime("%d/%m/%Y")
            message = SubscriptionMessages.Success.subscription_activated(
                plan_name=plan_option.name,
                stars=plan_option.stars,
                expires_at=expires_at,
            )

            await query.edit_message_text(
                text=message,
                reply_markup=SubscriptionKeyboards.subscription_status(),
                parse_mode="Markdown",
            )

            logger.info(
                f"💎 Subscription activated with Stars for user {user_id}: {plan_option.name}"
            )

        except ValueError as e:
            logger.warning(f"Subscription activation failed for user {user_id}: {e}")
            await query.answer(str(e), show_alert=True)
        except Exception as e:
            logger.error(f"Error in pay_with_stars: {e}")
            await query.answer("❌ Error al procesar pago", show_alert=True)

    async def pay_with_crypto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa pago de suscripción con Crypto (USDT/BSC)."""
        query = update.callback_query
        if not query or not query.data:
            return
        await query.answer()

        plan_type = query.data.replace("pay_sub_crypto_", "")
        user_id = update.effective_user.id

        try:
            plan_option = self.subscription_service.get_plan_option(plan_type)
            if not plan_option:
                await query.answer("❌ Plan no válido", show_alert=True)
                return

            # Check for existing subscription
            is_premium = await self.subscription_service.is_premium_user(user_id, settings.ADMIN_ID)
            if is_premium:
                await query.answer(
                    "⚠️ Ya tienes una suscripción activa",
                    show_alert=True,
                )
                return

            # TODO: Implement crypto payment flow (similar to buy_gb)
            # Por ahora, simulamos activación directa
            payment_id = f"sub_crypto_{user_id}_{plan_type}"

            subscription = await self.subscription_service.activate_subscription(
                user_id=user_id,
                plan_type=plan_type,
                stars_paid=plan_option.stars,
                payment_id=payment_id,
                current_user_id=settings.ADMIN_ID,
            )

            expires_at = subscription.expires_at.strftime("%d/%m/%Y")
            message = SubscriptionMessages.Success.subscription_activated(
                plan_name=plan_option.name,
                stars=plan_option.stars,
                expires_at=expires_at,
            )

            await query.edit_message_text(
                text=message,
                reply_markup=SubscriptionKeyboards.subscription_status(),
                parse_mode="Markdown",
            )

            logger.info(
                f"💎 Subscription activated with Crypto for user {user_id}: {plan_option.name}"
            )

        except ValueError as e:
            logger.warning(f"Subscription activation failed for user {user_id}: {e}")
            await query.answer(str(e), show_alert=True)
        except Exception as e:
            logger.error(f"Error in pay_with_crypto: {e}")
            await query.answer("❌ Error al procesar pago", show_alert=True)

    async def view_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View subscription status."""
        user_id = update.effective_user.id

        try:
            subscription = await self.subscription_service.get_user_subscription(
                user_id, settings.ADMIN_ID
            )

            if not subscription:
                await self.show_subscriptions(update, context)
                return

            plan_option = self.subscription_service.get_plan_option(subscription.plan_type.value)
            plan_name = plan_option.name if plan_option else subscription.plan_type.value
            expires_at = subscription.expires_at.strftime("%d/%m/%Y %H:%M")
            days_remaining = subscription.days_remaining

            message = SubscriptionMessages.SubscriptionInfo.active_subscription(
                plan_name=plan_name,
                expires_at=expires_at,
                days_remaining=days_remaining,
            )

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=message,
                    reply_markup=SubscriptionKeyboards.subscription_status(),
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    text=message,
                    reply_markup=SubscriptionKeyboards.subscription_status(),
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error viewing status: {e}")
            await update.callback_query.answer("❌ Error al ver estado", show_alert=True)


def get_subscription_handlers():
    """Get main subscription handlers."""
    subscription_service = get_service(SubscriptionService)
    handler = SubscriptionHandler(subscription_service)

    return [
        CommandHandler("premium", handler.show_subscriptions),
        CommandHandler("subscription", handler.show_subscriptions),
        CommandHandler("subscribe", handler.show_subscriptions),
    ]


def get_subscription_callback_handlers():
    """Get subscription callback handlers."""
    subscription_service = get_service(SubscriptionService)
    handler = SubscriptionHandler(subscription_service)

    return [
        CallbackQueryHandler(handler.show_subscriptions, pattern="^subscriptions$"),
        CallbackQueryHandler(handler.select_payment_method, pattern="^select_sub_payment_"),
        CallbackQueryHandler(handler.pay_with_stars, pattern="^pay_sub_stars_"),
        CallbackQueryHandler(handler.pay_with_crypto, pattern="^pay_sub_crypto_"),
        CallbackQueryHandler(handler.view_status, pattern="^sub_status$"),
    ]
