"""
Handlers para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.1.0 - Creditos + Shop + Historial
"""

from typing import List, Optional

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from application.services.referral_service import ReferralService
from application.services.vpn_service import VpnService
from config import settings
from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus
from infrastructure.persistence.postgresql.crypto_order_repository import (
    PostgresCryptoOrderRepository,
)
from utils.logger import logger
from utils.telegram_utils import TelegramUtils

from .keyboards_operations import OperationsKeyboards
from .messages_operations import OperationsMessages


class OperationsHandler:
    """Handler para operaciones del usuario."""

    def __init__(
        self,
        vpn_service: VpnService,
        referral_service: ReferralService,
        crypto_order_repo: Optional[PostgresCryptoOrderRepository] = None,
    ):
        self.vpn_service = vpn_service
        self.referral_service = referral_service
        self.crypto_order_repo = crypto_order_repo
        logger.info("⚙️ OperationsHandler inicializado")

    async def operations_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return
        user_id = update.effective_user.id

        logger.info(f"⚙️ User {user_id} opened operations menu")

        try:
            stats = await self.referral_service.get_referral_stats(user_id, user_id)
            credits = stats.referral_credits

            message = OperationsMessages.Menu.main_with_credits(credits)
            keyboard = OperationsKeyboards.operations_menu(credits=credits)

            if update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )
            elif update.callback_query:
                await update.callback_query.answer()
                await TelegramUtils.safe_edit_message(
                    update.callback_query,
                    context,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.error(f"Error en operations_menu: {e}")
            await self._send_error(update, context, OperationsMessages.Error.SYSTEM_ERROR)

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

            message = OperationsMessages.Credits.DISPLAY.format(credits=stats.referral_credits)
            keyboard = OperationsKeyboards.credits_menu(stats.referral_credits)

            await TelegramUtils.safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error en show_credits: {e}")
            await TelegramUtils.safe_edit_message(
                query,
                context,
                text=OperationsMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    async def show_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.callback_query:
            return
        query = update.callback_query
        await query.answer()

        logger.info("⚙️ User opened shop menu")

        message = OperationsMessages.Shop.MENU
        keyboard = OperationsKeyboards.shop_menu()

        await TelegramUtils.safe_edit_message(
            query, context, text=message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def redeem_credits_for_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    async def redeem_credits_for_slot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    async def show_buy_slots_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        if not isinstance(data_package_service, DataPackageService):
            raise RuntimeError("Failed to resolve DataPackageService from container")
        buy_handler = BuyGbHandler(data_package_service)
        await buy_handler.show_slots_menu(update, context)

    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.callback_query or not update.effective_user:
            return
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        logger.info(f"⚙️ User {user_id} returned to main menu")

        from telegram_bot.common.keyboards import CommonKeyboards
        from telegram_bot.common.messages import CommonMessages

        is_admin = update.effective_user.id == int(settings.ADMIN_ID)

        await TelegramUtils.safe_edit_message(
            query,
            context,
            text=CommonMessages.Menu.WELCOME_BACK,
            reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
            parse_mode="Markdown",
        )

    async def show_transactions_history(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0
    ):
        """Mostrar historial de transacciones crypto del usuario."""
        if not update.callback_query or not update.effective_user:
            return
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        logger.info(f"📜 User {user_id} viewing transaction history (page {page})")

        if not self.crypto_order_repo:
            logger.error("CryptoOrderRepository not available")
            await TelegramUtils.safe_edit_message(
                query,
                context,
                text=OperationsMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )
            return

        try:
            # Obtener órdenes paginadas
            limit = 10
            offset = page * limit
            orders = await self.crypto_order_repo.get_by_user_paginated(
                user_id, limit=limit + 1, offset=offset  # +1 para saber si hay más
            )

            if not orders:
                message = OperationsMessages.Transactions.NO_TRANSACTIONS
                keyboard = OperationsKeyboards.transactions_history_menu()
            else:
                has_more = len(orders) > limit
                orders_to_show = orders[:limit]

                message = OperationsMessages.Transactions.HISTORY_HEADER
                message += self._format_orders_list(orders_to_show)

                if has_more or page > 0:
                    message += OperationsMessages.Transactions.PAGE_FOOTER.format(page=page + 1)

                keyboard = OperationsKeyboards.transactions_history_menu(
                    has_more=has_more, page=page
                )

            await TelegramUtils.safe_edit_message(
                query,
                context,
                text=message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error showing transaction history: {e}")
            await TelegramUtils.safe_edit_message(
                query,
                context,
                text=OperationsMessages.Error.SYSTEM_ERROR,
                parse_mode="Markdown",
            )

    def _format_orders_list(self, orders: List[CryptoOrder]) -> str:
        """Formatear lista de órdenes para mostrar al usuario."""
        # Mapeo de estados: (emoji_color, emoji_icon, texto)
        status_map = {
            CryptoOrderStatus.PENDING: ("🟡", "⏳", "Pendiente"),
            CryptoOrderStatus.COMPLETED: ("🟢", "✅", "Completada"),
            CryptoOrderStatus.FAILED: ("🔴", "❌", "Fallida"),
            CryptoOrderStatus.EXPIRED: ("🔴", "⚠️", "Expirada"),
        }

        lines = []
        total_usdt = 0.0

        for order in orders:
            color_emoji, icon, text = status_map.get(order.status, ("⚪", "❓", str(order.status)))
            date_str = order.created_at.strftime("%d/%m/%Y %H:%M")
            lines.append(
                OperationsMessages.Transactions.ORDER_ITEM.format(
                    status_emoji=color_emoji,
                    package_type=order.package_type.upper(),
                    amount_usdt=order.amount_usdt,
                    date=date_str,
                    status_icon=icon,
                    status_text=text,
                )
            )
            total_usdt += float(order.amount_usdt)

        # Agregar footer con totales
        lines.append(
            OperationsMessages.Transactions.HISTORY_FOOTER.format(
                total_usdt=round(total_usdt, 2), total_count=len(orders)
            )
        )

        return "".join(lines)

    async def _handle_transactions_pagination(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handler para paginación del historial."""
        if not update.callback_query:
            return
        query = update.callback_query
        await query.answer()

        # Extraer número de página del callback_data
        # Format: transactions_page_N
        data = query.data
        if data and data.startswith("transactions_page_"):
            try:
                page = int(data.split("_")[-1])
                await self.show_transactions_history(update, context, page=page)
            except ValueError:
                logger.error(f"Invalid pagination data: {data}")

    async def _send_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
        if update.message:
            await update.message.reply_text(text=message, parse_mode="Markdown")
        elif update.callback_query:
            await TelegramUtils.safe_edit_message(
                update.callback_query, context, text=message, parse_mode="Markdown"
            )


def get_operations_handlers(
    vpn_service: VpnService,
    referral_service: ReferralService,
    crypto_order_repo: Optional[PostgresCryptoOrderRepository] = None,
):
    handler = OperationsHandler(vpn_service, referral_service, crypto_order_repo)

    return [
        MessageHandler(filters.Regex("^⚙️ Operaciones$"), handler.operations_menu),
        CommandHandler("operaciones", handler.operations_menu),
    ]


def get_operations_callback_handlers(
    vpn_service: VpnService,
    referral_service: ReferralService,
    crypto_order_repo: Optional[PostgresCryptoOrderRepository] = None,
):
    handler = OperationsHandler(vpn_service, referral_service, crypto_order_repo)

    return [
        CallbackQueryHandler(handler.operations_menu, pattern="^operations_menu$"),
        CallbackQueryHandler(handler.show_credits, pattern="^credits_menu$"),
        CallbackQueryHandler(handler.show_shop, pattern="^shop_menu$"),
        CallbackQueryHandler(handler.back_to_main_menu, pattern="^main_menu$"),
        CallbackQueryHandler(handler.redeem_credits_for_data, pattern="^credits_redeem_data$"),
        CallbackQueryHandler(handler.redeem_credits_for_slot, pattern="^credits_redeem_slot$"),
        CallbackQueryHandler(handler.show_buy_slots_menu, pattern="^buy_slots_menu$"),
        CallbackQueryHandler(handler.show_transactions_history, pattern="^transactions_history$"),
        CallbackQueryHandler(
            handler._handle_transactions_pagination, pattern="^transactions_page_"
        ),
    ]
