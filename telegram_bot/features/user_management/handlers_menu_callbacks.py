"""
Mixin para callbacks del menú principal.

Author: uSipipo Team
Version: 3.0.0 - Refactored into mixins
"""

from telegram import Update
from telegram.ext import ContextTypes

from application.services.admin_service import AdminService


class MenuCallbacksMixin:
    """Mixin para manejar callbacks del menú principal."""

    async def main_menu_callback(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Maneja los callbacks del menú principal.
        """
        if not update.callback_query:
            return
        if not update.effective_user:
            return

        query = update.callback_query
        await query.answer()

        callback_data = query.data

        if callback_data == "show_keys":
            from telegram_bot.features.key_management.handlers_key_management import (
                KeyManagementHandler,
            )

            key_mgmt_handler = KeyManagementHandler(
                self.vpn_service, self.billing_service
            )
            await key_mgmt_handler.show_key_submenu(update, _context)

        elif callback_data == "create_key":
            from telegram_bot.features.vpn_keys.handlers_vpn_keys import VpnKeysHandler

            vpn_keys_handler = VpnKeysHandler(self.vpn_service)
            await vpn_keys_handler.start_creation(update, _context)

        elif callback_data == "buy_data" or callback_data == "operations_menu":
            from application.services.common.container import get_container
            from application.services.referral_service import ReferralService
            from telegram_bot.features.operations.handlers_operations import (
                OperationsHandler,
            )

            container = get_container()
            referral_service = container.resolve(ReferralService)
            ops_handler = OperationsHandler(self.vpn_service, referral_service)
            await ops_handler.operations_menu(update, _context)

        elif callback_data == "show_usage":
            await self.info_handler(update, _context)

        elif callback_data == "help":
            await query.edit_message_text(
                text=self.messages.Welcome.HELP_TEXT,
                reply_markup=self.keyboards.help_menu(),
                parse_mode="Markdown",
            )

        elif callback_data == "help_faq":
            await query.edit_message_text(
                text=self.messages.Welcome.FAQ_TEXT,
                reply_markup=self.keyboards.back_to_help(),
                parse_mode="Markdown",
            )

        elif callback_data == "help_bonuses":
            await query.edit_message_text(
                text=self.messages.Welcome.BONUSES_INFO,
                reply_markup=self.keyboards.back_to_help(),
                parse_mode="Markdown",
            )

        elif callback_data == "admin_panel":
            from application.services.common.container import get_container
            from telegram_bot.features.admin.handlers_admin import AdminHandler

            container = get_container()
            admin_service = container.resolve(AdminService)
            admin_handler = AdminHandler(admin_service)
            await admin_handler.admin_menu(update, _context)

        elif callback_data == "show_history":
            await self.history_handler(update, _context)
