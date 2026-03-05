"""
Handlers para gestión de usuarios de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Refactored into mixins
"""

from typing import Optional

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from application.services.consumption_billing_service import ConsumptionBillingService
from application.services.user_profile_service import UserProfileService
from application.services.vpn_service import VpnService
from config import settings
from telegram_bot.common.base_handler import BaseHandler
from telegram_bot.common.keyboards import get_miniapp_url
from utils.logger import logger

from .handlers_menu_callbacks import MenuCallbacksMixin
from .handlers_user_actions import UserActionsMixin
from .handlers_user_profile import UserProfileMixin
from .keyboards_user_management import UserManagementKeyboards
from .messages_user_management import UserManagementMessages

__all__ = [
    "UserManagementHandler",
    "get_user_management_handlers",
    "get_user_callback_handlers",
]


class UserManagementHandler(
    BaseHandler,
    UserActionsMixin,
    UserProfileMixin,
    MenuCallbacksMixin,
):
    """Handler para gestión de usuarios."""

    def __init__(
        self,
        vpn_service: VpnService,
        user_profile_service: Optional[UserProfileService] = None,
        billing_service: Optional[ConsumptionBillingService] = None,
    ):
        """
        Inicializa el handler de gestión de usuarios.

        Args:
            vpn_service: Servicio de VPN
            user_profile_service: Servicio de perfil de usuario (opcional)
            billing_service: Servicio de facturación por consumo (opcional)
        """
        super().__init__(vpn_service, "VpnService")
        self.vpn_service = vpn_service
        self.user_profile_service = user_profile_service
        self.billing_service = billing_service
        self.settings = settings
        self.messages = UserManagementMessages
        self.keyboards = UserManagementKeyboards
        logger.info("👤 UserManagementHandler inicializado")

    def _get_miniapp_url(self) -> str:
        """Retorna la URL de la mini app."""
        return get_miniapp_url()

    async def _reply_message(
        self,
        update: Update,
        text: str,
        reply_markup=None,
        parse_mode: str = "Markdown",
        context: ContextTypes.DEFAULT_TYPE = None,
    ):
        """Helper para responder mensajes de forma consistente."""
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        elif update.message:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )


def get_user_management_handlers(
    vpn_service: VpnService,
    user_profile_service: Optional[UserProfileService] = None,
    billing_service: Optional[ConsumptionBillingService] = None,
):
    """
    Retorna los handlers de gestión de usuarios.

    Args:
        vpn_service: Servicio de VPN
        user_profile_service: Servicio de perfil de usuario (opcional)
        billing_service: Servicio de facturación por consumo (opcional)

    Returns:
        list: Lista de handlers
    """
    handler = UserManagementHandler(vpn_service, user_profile_service, billing_service)

    return [
        CommandHandler("start", handler.start_handler),
        CommandHandler("info", handler.info_handler),
        CommandHandler("history", handler.history_handler),
        MessageHandler(filters.Regex("^📊 Estado$"), handler.status_handler),
        CommandHandler("status", handler.status_handler),
    ]


def get_user_callback_handlers(
    vpn_service: VpnService,
    user_profile_service: Optional[UserProfileService] = None,
    billing_service: Optional[ConsumptionBillingService] = None,
):
    """
    Retorna los handlers de callbacks para gestión de usuarios.

    Args:
        vpn_service: Servicio de VPN
        user_profile_service: Servicio de perfil de usuario (opcional)
        billing_service: Servicio de facturación por consumo (opcional)

    Returns:
        list: Lista de CallbackQueryHandler
    """
    from application.services.admin_service import AdminService
    from application.services.common.container import get_container

    container = get_container()
    admin_service = container.resolve(AdminService)

    handler = UserManagementHandler(vpn_service, user_profile_service, billing_service)

    return [
        CallbackQueryHandler(
            lambda u, c: handler.status_handler(u, c, admin_service), pattern="^status$"
        ),
        CallbackQueryHandler(
            handler.main_menu_callback,
            pattern=(
                "^(show_keys|buy_data|operations_menu|show_usage|"
                "help|help_faq|help_bonuses|admin_panel|show_history|main_menu)$"
            ),
        ),
    ]
