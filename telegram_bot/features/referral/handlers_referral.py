"""
Handlers para el sistema de referidos.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from application.services.referral_service import ReferralService
from config import settings
from utils.logger import logger

from .keyboards_referral import ReferralKeyboards
from .messages_referral import ReferralMessages


class ReferralHandler:
    """Handler para el sistema de referidos."""

    def __init__(self, referral_service: ReferralService):
        self.referral_service = referral_service
        logger.info("🎁 ReferralHandler inicializado")

    async def show_referral_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el menu principal de referidos."""
        user_id = update.effective_user.id
        query = update.callback_query

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            
            message = ReferralMessages.Menu.referral_info(
                code=stats.referral_code,
                credits=stats.referral_credits,
                total_referrals=stats.total_referrals,
                bot_username=settings.BOT_USERNAME,
            )
            
            keyboard = ReferralKeyboards.main_menu(stats.referral_credits)

            if query:
                await query.answer()
                await query.edit_message_text(
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
            logger.error(f"Error en show_referral_menu: {e}")
            error_msg = ReferralMessages.Error.SYSTEM_ERROR
            
            if query:
                await query.answer()
                await query.edit_message_text(text=error_msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(text=error_msg, parse_mode="Markdown")

    async def show_redeem_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra el menu de canje de creditos."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            
            message = ReferralMessages.Redeem.OPTIONS
            keyboard = ReferralKeyboards.redeem_menu(stats.referral_credits)

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en show_redeem_menu: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def confirm_redeem_data(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra confirmacion para canjear creditos por datos."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            
            if stats.referral_credits < settings.REFERRAL_CREDITS_PER_GB:
                message = ReferralMessages.Redeem.INSUFFICIENT_CREDITS
                keyboard = ReferralKeyboards.redeem_menu(stats.referral_credits)
            else:
                gb = stats.referral_credits // settings.REFERRAL_CREDITS_PER_GB
                credits_to_spend = gb * settings.REFERRAL_CREDITS_PER_GB
                
                message = ReferralMessages.Redeem.confirm_data(
                    credits=credits_to_spend,
                    gb=gb,
                )
                keyboard = ReferralKeyboards.confirm_redeem_data(
                    credits=credits_to_spend,
                    gb=gb,
                )
                
                context.user_data["redeem_gb"] = gb
                context.user_data["redeem_credits"] = credits_to_spend

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en confirm_redeem_data: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def confirm_redeem_slot(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Muestra confirmacion para canjear creditos por slot."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            
            if stats.referral_credits < settings.REFERRAL_CREDITS_PER_SLOT:
                message = ReferralMessages.Redeem.insufficient_for_slot(
                    required=settings.REFERRAL_CREDITS_PER_SLOT,
                    current=stats.referral_credits,
                )
                keyboard = ReferralKeyboards.redeem_menu(stats.referral_credits)
            else:
                message = ReferralMessages.Redeem.confirm_slot(
                    credits=settings.REFERRAL_CREDITS_PER_SLOT
                )
                keyboard = ReferralKeyboards.confirm_redeem_slot(
                    credits=settings.REFERRAL_CREDITS_PER_SLOT
                )

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en confirm_redeem_slot: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def execute_redeem_data(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Ejecuta el canje de creditos por datos."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        gb = context.user_data.get("redeem_gb", 1)
        credits = context.user_data.get("redeem_credits", settings.REFERRAL_CREDITS_PER_GB)

        try:
            result = await self.referral_service.redeem_credits_for_data(
                user_id=user_id,
                credits=credits,
                current_user_id=user_id,
            )

            if result.get("success"):
                message = ReferralMessages.Success.data_redeemed(
                    gb=result.get("gb_added", gb),
                    remaining=result.get("remaining_credits", 0),
                )
                keyboard = ReferralKeyboards.success_back()
                
                context.user_data.pop("redeem_gb", None)
                context.user_data.pop("redeem_credits", None)
            else:
                message = ReferralMessages.Error.INSUFFICIENT_CREDITS
                keyboard = ReferralKeyboards.redeem_menu(0)

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en execute_redeem_data: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def execute_redeem_slot(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Ejecuta el canje de creditos por slot."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id

        try:
            result = await self.referral_service.redeem_credits_for_slot(
                user_id=user_id,
                current_user_id=user_id,
            )

            if result.get("success"):
                message = ReferralMessages.Success.slot_redeemed(
                    remaining=result.get("remaining_credits", 0),
                )
                keyboard = ReferralKeyboards.success_back()
            else:
                error = result.get("error", "unknown")
                if error == "insufficient_credits":
                    message = ReferralMessages.Redeem.insufficient_for_slot(
                        required=result.get("required", settings.REFERRAL_CREDITS_PER_SLOT),
                        current=result.get("current", 0),
                    )
                else:
                    message = ReferralMessages.Error.SYSTEM_ERROR
                keyboard = ReferralKeyboards.redeem_menu(result.get("current", 0))

            await query.edit_message_text(
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error en execute_redeem_slot: {e}")
            await query.edit_message_text(
                text=ReferralMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )


def get_referral_handlers(referral_service: ReferralService):
    """Retorna los handlers de comandos de referidos."""
    handler = ReferralHandler(referral_service)

    return [
        CommandHandler("referir", handler.show_referral_menu),
    ]


def get_referral_callback_handlers(referral_service: ReferralService):
    """Retorna los handlers de callbacks para referidos."""
    handler = ReferralHandler(referral_service)

    return [
        CallbackQueryHandler(handler.show_referral_menu, pattern="^referral_menu$"),
        CallbackQueryHandler(handler.show_referral_menu, pattern="^referral_refresh$"),
        CallbackQueryHandler(handler.show_redeem_menu, pattern="^referral_redeem_menu$"),
        CallbackQueryHandler(handler.confirm_redeem_data, pattern="^referral_redeem_data$"),
        CallbackQueryHandler(handler.confirm_redeem_slot, pattern="^referral_redeem_slot$"),
        CallbackQueryHandler(handler.execute_redeem_data, pattern="^referral_confirm_data$"),
        CallbackQueryHandler(handler.execute_redeem_slot, pattern="^referral_confirm_slot$"),
    ]
