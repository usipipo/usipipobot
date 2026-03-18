"""
Handlers para gestión avanzada de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Refactored into mixins
"""

from typing import Optional

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from application.services.consumption_billing_service import ConsumptionBillingService
from application.services.vpn_service import VpnService
from config import settings
from telegram_bot.common.base_handler import BaseHandler
from utils.logger import logger
from utils.telegram_utils import escape_markdown

from .handlers_key_actions import KeyActionsMixin
from .handlers_key_info import KeyInfoMixin
from .handlers_key_latency import LatencyMixin
from .handlers_rename_key import RenameKeyMixin
from .handlers_view_keys import ViewKeysMixin
from .keyboards_key_management import KeyManagementKeyboards
from .messages_key_management import KeyManagementMessages

__all__ = [
    "KeyManagementHandler",
    "get_key_management_handlers",
    "get_key_management_callback_handlers",
]


class KeyManagementHandler(
    BaseHandler,
    ViewKeysMixin,
    KeyActionsMixin,
    RenameKeyMixin,
    KeyInfoMixin,
    LatencyMixin,
):
    """Handler para gestión avanzada de llaves VPN."""

    def __init__(
        self,
        vpn_service: VpnService,
        billing_service: Optional[ConsumptionBillingService] = None,
    ):
        """
        Inicializa el handler de gestión de llaves.

        Args:
            vpn_service: Servicio de VPN
            billing_service: Servicio de facturación por consumo (opcional)
        """
        super().__init__(vpn_service, "VpnService")
        self.vpn_service = vpn_service
        self.billing_service = billing_service
        logger.info("🔑 KeyManagementHandler inicializado")

    async def _get_consumption_status(self, user_id: int) -> bool:
        """Verifica si el usuario tiene tarifa por consumo activa."""
        if self.billing_service is None:
            return False
        try:
            summary = await self.billing_service.get_current_consumption(user_id, user_id)
            return summary is not None and summary.is_active
        except Exception as e:
            logger.error(f"Error verificando estado de consumo: {e}")
            return False

    async def show_key_submenu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú principal de gestión de llaves."""
        query = update.callback_query

        if query is None:
            if update.effective_user is None:
                return
            user_id = update.effective_user.id
            logger.info(f"User {user_id} viewing key submenu")
            if update.message is None:
                return
            try:
                user_status = await self.vpn_service.get_user_status(
                    user_id, current_user_id=user_id
                )
                keys = user_status.get("keys", [])

                keys_summary = {"total_count": len(keys)}

                for protocol in settings.get_vpn_protocols():
                    count = len([k for k in keys if k.key_type.lower() == protocol.lower()])
                    keys_summary[f"{protocol}_count"] = count

                has_consumption_active = await self._get_consumption_status(user_id)

                if keys_summary["total_count"] == 0:
                    message = KeyManagementMessages.NO_KEYS
                else:
                    message = KeyManagementMessages.MAIN_MENU.format(
                        total_keys=escape_markdown(str(keys_summary["total_count"])),
                        outline_count=escape_markdown(str(keys_summary.get("outline_count", 0))),
                        wireguard_count=escape_markdown(
                            str(keys_summary.get("wireguard_count", 0))
                        ),
                    )

                await update.message.reply_text(
                    text=message,
                    reply_markup=KeyManagementKeyboards.main_menu(
                        keys_summary, has_consumption_active
                    ),
                    parse_mode="Markdown",
                )

            except Exception as e:
                logger.error(f"Error mostrando submenú de llaves: {e}")
                if update.message is not None:
                    await update.message.reply_text(
                        text=KeyManagementMessages.Error.SYSTEM_ERROR,
                        parse_mode="Markdown",
                    )
        else:
            await self._safe_answer_query(query)
            if update.effective_user is None:
                return
            user_id = update.effective_user.id
            logger.info(f"User {user_id} viewing key submenu")

            try:
                user_status = await self.vpn_service.get_user_status(
                    user_id, current_user_id=user_id
                )
                keys = user_status.get("keys", [])

                keys_summary = {"total_count": len(keys)}

                for protocol in settings.get_vpn_protocols():
                    count = len([k for k in keys if k.key_type.lower() == protocol.lower()])
                    keys_summary[f"{protocol}_count"] = count

                has_consumption_active = await self._get_consumption_status(user_id)

                if keys_summary["total_count"] == 0:
                    message = KeyManagementMessages.NO_KEYS
                else:
                    message = KeyManagementMessages.MAIN_MENU.format(
                        total_keys=escape_markdown(str(keys_summary["total_count"])),
                        outline_count=escape_markdown(str(keys_summary.get("outline_count", 0))),
                        wireguard_count=escape_markdown(
                            str(keys_summary.get("wireguard_count", 0))
                        ),
                    )

                await self._safe_edit_message(
                    query,
                    context,
                    text=message,
                    reply_markup=KeyManagementKeyboards.main_menu(
                        keys_summary, has_consumption_active
                    ),
                    parse_mode="Markdown",
                )

            except Exception as e:
                logger.error(f"Error mostrando submenú de llaves: {e}")
                await self._safe_edit_message(
                    query,
                    context,
                    text=KeyManagementMessages.Error.SYSTEM_ERROR,
                    reply_markup=KeyManagementKeyboards.back_to_main(),
                    parse_mode="Markdown",
                )

    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Vuelve al menú principal."""
        query = update.callback_query
        if query is None:
            return
        await self._safe_answer_query(query)

        user = update.effective_user
        if user is None:
            return
        is_admin = user.id == int(settings.ADMIN_ID)

        from telegram_bot.common.keyboards import CommonKeyboards
        from telegram_bot.common.messages import CommonMessages

        await self._safe_edit_message(
            query,
            context,
            text=CommonMessages.Menu.WELCOME_BACK,
            reply_markup=CommonKeyboards.main_menu(is_admin=is_admin),
            parse_mode="Markdown",
        )

    async def back_to_keys(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Vuelve al submenú de gestión de llaves."""
        await self.show_key_submenu(update, context)


def get_key_management_handlers(
    vpn_service: VpnService,
    billing_service: Optional[ConsumptionBillingService] = None,
):
    """Retorna los handlers de gestión de llaves."""
    handler = KeyManagementHandler(vpn_service, billing_service)
    return [
        MessageHandler(filters.Regex("^🛡️ Mis Llaves$"), handler.show_key_submenu),
        CommandHandler("keys", handler.show_key_submenu),
        CommandHandler("latency", handler.latency_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handler.process_rename_key),
    ]


def get_key_management_callback_handlers(
    vpn_service: VpnService,
    billing_service: Optional[ConsumptionBillingService] = None,
):
    """Retorna los handlers de callbacks para gestión de llaves."""
    handler = KeyManagementHandler(vpn_service, billing_service)
    return [
        CallbackQueryHandler(handler.show_key_submenu, pattern="^key_management$"),
        CallbackQueryHandler(handler.back_to_main_menu, pattern="^main_menu$"),
        CallbackQueryHandler(handler.show_keys_by_type, pattern="^keys_"),
        CallbackQueryHandler(handler.show_key_details, pattern="^key_details_"),
        CallbackQueryHandler(handler.show_key_statistics, pattern="^key_stats$"),
        CallbackQueryHandler(handler.show_server_latency, pattern="^server_latency$"),
        CallbackQueryHandler(handler.refresh_server_latency, pattern="^refresh_latency$"),
        CallbackQueryHandler(handler.back_to_main_menu, pattern="^back_to_main$"),
        CallbackQueryHandler(handler.back_to_keys, pattern="^back_to_keys$"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_reactivate_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_rename_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_qr_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_change_server_"),
        CallbackQueryHandler(handler.handle_key_action, pattern="^key_extend_"),
        CallbackQueryHandler(handler.download_wireguard_config, pattern="^key_download_wg_"),
        CallbackQueryHandler(handler.get_outline_link, pattern="^key_get_link_"),
        CallbackQueryHandler(handler.cancel_rename, pattern="^cancel_rename$"),
    ]
