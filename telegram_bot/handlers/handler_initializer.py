"""
Handler Initializer for uSipipo VPN Manager Bot.

Centralizes the initialization and registration of all Telegram handlers
across different features following the hexagonal architecture pattern.

Author: uSipipo Team
Version: 2.0.0
"""

from typing import List
from telegram.ext import BaseHandler
from utils.logger import logger

from telegram_bot.features.admin.handlers_admin import (
    get_admin_handlers, get_admin_callback_handlers
)
from telegram_bot.features.announcer.handlers_announcer import (
    get_announcer_handlers, get_announcer_callback_handlers
)
from telegram_bot.features.broadcast.handlers_broadcast import (
    get_broadcast_handlers, get_broadcast_callback_handlers
)
from telegram_bot.features.game.handlers_game import (
    get_game_handlers, get_game_callback_handlers
)
from telegram_bot.features.key_management.handlers_key_management import (
    get_key_management_handlers, get_key_management_callback_handlers
)
from telegram_bot.features.operations.handlers_operations import (
    get_operations_handlers, get_operations_callback_handlers
)
from telegram_bot.features.payments.handlers_payments import (
    get_payments_handlers, get_payments_callback_handlers
)
from telegram_bot.features.referral.handlers_referral import (
    get_referral_handlers, get_referral_callback_handlers
)
from telegram_bot.features.shop.handlers_shop import (
    get_shop_handlers, get_shop_callback_handlers
)
from telegram_bot.features.user_management.handlers_user_management import (
    get_user_management_handlers, get_user_callback_handlers
)
from telegram_bot.features.vip.handlers_vip import (
    get_vip_handlers, get_vip_callback_handlers
)
from telegram_bot.features.vpn_keys.handlers_vpn_keys import (
    get_vpn_keys_handlers, get_vpn_keys_callback_handlers
)

from application.services.vpn_service import VpnService
from application.services.payment_service import PaymentService
from application.services.referral_service import ReferralService
from application.services.admin_service import AdminService
from application.services.announcer_service import AnnouncerService
from application.services.broadcast_service import BroadcastService
from application.services.game_service import GameService
from application.services.common.container import get_container


def _get_admin_handlers(container) -> List[BaseHandler]:
    """Initialize and return admin handlers."""
    admin_service = container.resolve(AdminService)
    handlers = []
    handlers.extend(get_admin_handlers(admin_service))
    handlers.extend(get_admin_callback_handlers(admin_service))
    logger.info("✅ Handlers de administración configurados")
    return handlers


def _get_service_handlers(container, vpn_service) -> List[BaseHandler]:
    """Initialize and return all service-based handlers."""
    handlers = []

    announcer_service = container.resolve(AnnouncerService)
    handlers.extend(get_announcer_handlers(announcer_service, vpn_service))
    handlers.extend(get_announcer_callback_handlers(announcer_service, vpn_service))
    logger.info("✅ Handlers de anunciador configurados")

    broadcast_service = container.resolve(BroadcastService)
    handlers.extend(get_broadcast_handlers(broadcast_service))
    handlers.extend(get_broadcast_callback_handlers(broadcast_service))
    logger.info("✅ Handlers de difusión configurados")

    game_service = container.resolve(GameService)
    handlers.extend(get_game_handlers(game_service))
    handlers.extend(get_game_callback_handlers(game_service))
    logger.info("✅ Handlers de juego configurados")

    return handlers


def _get_core_handlers(vpn_service, referral_service, payment_service) -> List[BaseHandler]:
    """Initialize and return core feature handlers."""
    handlers = []

    handlers.extend(get_key_management_handlers(vpn_service))
    handlers.extend(get_key_management_callback_handlers(vpn_service))
    logger.info("✅ Handlers de gestión de claves configurados")

    handlers.extend(get_operations_handlers(vpn_service, referral_service))
    handlers.extend(get_operations_callback_handlers(vpn_service, referral_service))
    logger.info("✅ Handlers de operaciones configurados")

    handlers.extend(get_payments_handlers(payment_service, vpn_service, referral_service))
    handlers.extend(get_payments_callback_handlers(payment_service, vpn_service, referral_service))
    logger.info("✅ Handlers de pagos configurados")

    handlers.extend(get_referral_handlers(referral_service, vpn_service))
    handlers.extend(get_referral_callback_handlers(referral_service, vpn_service))
    logger.info("✅ Handlers de referidos configurados")

    handlers.extend(get_shop_handlers(payment_service, vpn_service))
    handlers.extend(get_shop_callback_handlers(payment_service, vpn_service))
    logger.info("✅ Handlers de tienda configurados")

    handlers.extend(get_user_management_handlers(vpn_service, None))
    handlers.extend(get_user_callback_handlers(vpn_service, None))
    logger.info("✅ Handlers de gestión de usuarios configurados")

    handlers.extend(get_vip_handlers(payment_service, vpn_service))
    handlers.extend(get_vip_callback_handlers(payment_service, vpn_service))
    logger.info("✅ Handlers VIP configurados")

    handlers.extend(get_vpn_keys_handlers(vpn_service))
    handlers.extend(get_vpn_keys_callback_handlers(vpn_service))
    logger.info("✅ Handlers de claves VPN configurados")

    return handlers


def initialize_handlers(
    vpn_service: VpnService,
    referral_service: ReferralService,
    payment_service: PaymentService
) -> List[BaseHandler]:
    """
    Initialize and return all Telegram handlers for the bot.

    Args:
        vpn_service: VPN management service
        referral_service: Referral system service
        payment_service: Payment processing service

    Returns:
        List[BaseHandler]: List of all configured handlers
    """
    logger.info("🔧 Inicializando handlers del bot...")
    handlers = []

    try:
        container = get_container()

        handlers.extend(_get_admin_handlers(container))
        handlers.extend(_get_service_handlers(container, vpn_service))
        handlers.extend(_get_core_handlers(vpn_service, referral_service, payment_service))

        logger.info(f"🎉 Total de handlers configurados: {len(handlers)}")
        return handlers

    except Exception as e:
        logger.error(f"❌ Error al inicializar handlers: {e}")
        raise
