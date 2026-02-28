"""
Handlers para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Creditos + Shop
"""

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from application.services.referral_service import ReferralService
from application.services.vpn_service import VpnService
from config import settings
from utils.logger import logger

from .keyboards_operations import OperationsKeyboards
from .messages_operations import OperationsMessages


class OperationsHandler:
    """Handler para operaciones del usuario."""

    def __init__(self, vpn_service: VpnService, referral_service: ReferralService):
        self.vpn_service = vpn_service
        self.referral_service = referral_service
        logger.info("⚙️ OperationsHandler inicializado")

    async def operations_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return
        user_id = update.effective_user.id

        logger.info(f"⚙️ User {user_id} opened operations menu")

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            credits = stats.referral_credits

            message = OperationsMessages.Menu.MAIN
            keyboard = OperationsKeyboards.operations_menu(credits=credits)

            if update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )
            elif update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Error en operations_menu: {e}")
            await self._send_error(update, OperationsMessages.Error.SYSTEM_ERROR)

    async def show_credits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.callback_query or not update.effective_user:
            return
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        logger.info(f"⚙️ User {user_id} viewing credits")

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            logger.debug(f"⚙️ User {user_id} has {stats.referral_credits} credits")

            message = OperationsMessages.Credits.DISPLAY.format(
                credits=stats.referral_credits
            )
            keyboard = OperationsKeyboards.credits_menu(stats.referral_credits)

            await query.edit_message_text(
                text=message, reply_markup=keyboard, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error en show_credits: {e}")
            await query.edit_message_text(
                text=OperationsMessages.Error.SYSTEM_ERROR, parse_mode="Markdown"
            )

    async def show_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.callback_query:
            return
        query = update.callback_query
        await query.answer()

        logger.info("⚙️ User opened shop menu")

        message = OperationsMessages.Shop.MENU
        keyboard = OperationsKeyboards.shop_menu()

        await query.edit_message_text(
            text=message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def redeem_credits_for_data(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Canjear creditos por datos - redirige a referral handler."""
        if not update.callback_query:
            return
        from telegram_bot.features.referral.handlers_referral import ReferralHandler

        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id if update.effective_user else None
        logger.debug(f"⚙️ Redirecting user {user_id} to data redemption")

        referral_handler = ReferralHandler(self.referral_service)
        await referral_handler.confirm_redeem_data(update, context)

    async def redeem_credits_for_slot(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Canjear creditos por slot - redirige a referral handler."""
        if not update.callback_query:
            return
        from telegram_bot.features.referral.handlers_referral import ReferralHandler

        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id if update.effective_user else None
        logger.debug(f"⚙️ Redirecting user {user_id} to slot redemption")

        referral_handler = ReferralHandler(self.referral_service)
        await referral_handler.confirm_redeem_slot(update, context)

    async def show_buy_slots_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Mostrar menu de compra de slots con Telegram Stars."""
        if not update.callback_query:
            return
        from application.services.common.container import get_container
        from application.services.data_package_service import DataPackageService
        from telegram_bot.features.buy_gb.handlers_buy_gb import BuyGbHandler

        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id if update.effective_user else None
        logger.info(f"⚙️ User {user_id} navigating to slots purchase menu")

        container = get_container()
        data_package_service = container.resolve(DataPackageService)
        buy_handler = BuyGbHandler(data_package_service)
        await buy_handler.show_slots_menu(update, context)

    async def back_to_main_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if not update.callback_query or not update.effective_user:
            return
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        logger.info(f"⚙️ User {user_id} returned to main menu")

        from telegram_bot.common.keyboards import CommonKeyboards
        from telegram_bot.common.messages import CommonMessages

        is_admin = update.effective_user.id == int(settings.ADMIN_ID)

        await query.edit_message_text(
            text=CommonMessages.Menu.WELCOME_BACK,
            reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
            parse_mode="Markdown",
        )

    async def _send_error(self, update: Update, message: str):
        if update.message:
            await update.message.reply_text(text=message, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                text=message, parse_mode="Markdown"
            )


def get_operations_handlers(vpn_service: VpnService, referral_service: ReferralService):
    handler = OperationsHandler(vpn_service, referral_service)

    return [
        MessageHandler(filters.Regex("^⚙️ Operaciones$"), handler.operations_menu),
        CommandHandler("operaciones", handler.operations_menu),
    ]


def get_operations_callback_handlers(
    vpn_service: VpnService, referral_service: ReferralService
):
    handler = OperationsHandler(vpn_service, referral_service)

    return [
        CallbackQueryHandler(handler.operations_menu, pattern="^operations_menu$"),
        CallbackQueryHandler(handler.show_credits, pattern="^credits_menu$"),
        CallbackQueryHandler(handler.show_shop, pattern="^shop_menu$"),
        CallbackQueryHandler(handler.back_to_main_menu, pattern="^main_menu$"),
        CallbackQueryHandler(
            handler.redeem_credits_for_data, pattern="^credits_redeem_data$"
        ),
        CallbackQueryHandler(
            handler.redeem_credits_for_slot, pattern="^credits_redeem_slot$"
        ),
        CallbackQueryHandler(handler.show_buy_slots_menu, pattern="^buy_slots_menu$"),
    ]
