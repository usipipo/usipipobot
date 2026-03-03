"""
Handlers for admin VPN management.

Author: uSipipo Team
Version: 2.0.0 - Refactored into mixins
"""

from typing import Any, List

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from application.services.vpn_infrastructure_service import VpnInfrastructureService
from telegram_bot.common.base_handler import BaseHandler
from telegram_bot.common.decorators import admin_required
from utils.logger import logger

from .handlers_cleanup import CleanupMixin
from .handlers_key_deletion import KeyDeletionMixin
from .handlers_key_listing import KEYS_PER_PAGE, KeyListingMixin
from .handlers_key_operations import KeyOperationsMixin
from .handlers_server_monitoring import ServerMonitoringMixin
from .keyboards_admin_vpn import AdminVpnKeyboards
from .messages_admin_vpn import AdminVpnMessages

__all__ = [
    "AdminVpnHandler",
    "get_admin_vpn_handlers",
    "KEYS_PER_PAGE",
]


class AdminVpnHandler(
    BaseHandler,
    ServerMonitoringMixin,
    KeyListingMixin,
    KeyOperationsMixin,
    KeyDeletionMixin,
    CleanupMixin,
):
    """Handler for VPN server management."""

    def __init__(self, vpn_service: VpnInfrastructureService):
        super().__init__()
        self.vpn_service = vpn_service
        logger.info("⚡ AdminVpnHandler inicializado")

    def get_handlers(self) -> List[CallbackQueryHandler]:
        """Define handler callbacks."""
        return [
            CallbackQueryHandler(self.show_vpn_menu, pattern="^admin_vpn$"),
            CallbackQueryHandler(self.show_server_status, pattern="^vpn_status$"),
            CallbackQueryHandler(self.manage_server, pattern="^vpn_manage_wireguard$"),
            CallbackQueryHandler(self.manage_server, pattern="^vpn_manage_outline$"),
            CallbackQueryHandler(self.show_server_details, pattern="^vpn_server_status_wireguard$"),
            CallbackQueryHandler(self.show_server_details, pattern="^vpn_server_status_outline$"),
            CallbackQueryHandler(self.list_server_keys, pattern="^vpn_list_keys_wireguard$"),
            CallbackQueryHandler(self.list_server_keys, pattern="^vpn_list_keys_outline$"),
            CallbackQueryHandler(self.cleanup_ghost_keys, pattern="^vpn_cleanup_ghosts$"),
            CallbackQueryHandler(self.show_key_details, pattern="^vkdet_wireguard_"),
            CallbackQueryHandler(self.show_key_details, pattern="^vkdet_outline_"),
            CallbackQueryHandler(self.handle_key_enable, pattern="^vke_wireguard_"),
            CallbackQueryHandler(self.handle_key_enable, pattern="^vke_outline_"),
            CallbackQueryHandler(self.handle_key_disable, pattern="^vkdis_wireguard_"),
            CallbackQueryHandler(self.handle_key_disable, pattern="^vkdis_outline_"),
            CallbackQueryHandler(self.confirm_delete_key, pattern="^vkdel_wireguard_"),
            CallbackQueryHandler(self.confirm_delete_key, pattern="^vkdel_outline_"),
            CallbackQueryHandler(self.execute_delete_key, pattern="^vc_delete_wireguard_"),
            CallbackQueryHandler(self.execute_delete_key, pattern="^vc_delete_outline_"),
            CallbackQueryHandler(self.cancel_key_action, pattern="^vx_delete_wireguard_"),
            CallbackQueryHandler(self.cancel_key_action, pattern="^vx_delete_outline_"),
            CallbackQueryHandler(self.keys_page, pattern="^vpn_keys_page_wireguard_"),
            CallbackQueryHandler(self.keys_page, pattern="^vpn_keys_page_outline_"),
        ]

    @admin_required
    async def show_vpn_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main VPN management menu."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query:
            await self._safe_edit_message(
                query,
                context,
                text=AdminVpnMessages.MAIN_MENU,
                reply_markup=AdminVpnKeyboards.vpn_management_menu(),
                parse_mode="Markdown",
            )
        else:
            await self._reply_message(
                update,
                text=AdminVpnMessages.MAIN_MENU,
                reply_markup=AdminVpnKeyboards.vpn_management_menu(),
                parse_mode="Markdown",
                context=context,
            )
        return None


def get_admin_vpn_handlers(vpn_service: VpnInfrastructureService) -> List[Any]:
    """Get all admin VPN handlers."""
    handler = AdminVpnHandler(vpn_service)
    return handler.get_handlers()
