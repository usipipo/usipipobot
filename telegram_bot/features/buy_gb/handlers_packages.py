"""
Handlers para visualización de paquetes y resumen de datos.

Author: uSipipo Team
Version: 1.2.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import ContextTypes

from application.services.data_package_service import PACKAGE_OPTIONS
from config import settings
from telegram_bot.features.user_management.keyboards_user_management import UserManagementKeyboards
from utils.logger import logger
from utils.telegram_utils import TelegramUtils

from .keyboards_buy_gb import BuyGbKeyboards
from .messages_buy_gb import BuyGbMessages


class PackagesMixin:
    """Mixin para manejo de paquetes y visualización de datos."""

    async def show_packages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú de paquetes disponibles."""
        query = update.callback_query
        if query:
            await query.answer()

        if not update.effective_user:
            return

        try:
            packages_list = BuyGbMessages.Menu.format_packages_list()
            message = BuyGbMessages.Menu.PACKAGES_LIST.format(packages_list=packages_list)
            keyboard = BuyGbKeyboards.packages_menu()

            if query:
                await TelegramUtils.safe_edit_message(
                    query,
                    context,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error en show_packages: {e}")
            error_message = BuyGbMessages.Error.SYSTEM_ERROR

            if query:
                await TelegramUtils.safe_edit_message(
                    query,
                    context,
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

    async def select_payment_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                crypto_price=package_option.stars / 120,  # 1 USDT = 120 Stars
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

    async def view_data_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el resumen de datos del usuario."""
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

            message = BuyGbMessages.Info.DATA_SUMMARY(
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

            if summary["active_packages"] == 0 and summary["free_plan"]["remaining_gb"] <= 0:
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
