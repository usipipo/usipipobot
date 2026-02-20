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
from telegram_bot.features.key_management.handlers_key_management import (
    get_key_management_handlers, get_key_management_callback_handlers
)
from telegram_bot.features.operations.handlers_operations import (
    get_operations_handlers, get_operations_callback_handlers
)
from telegram_bot.features.payments.handlers_payments import (
    get_payments_handlers, get_payments_callback_handlers
)
from telegram_bot.features.user_management.handlers_user_management import (
    get_user_management_handlers, get_user_callback_handlers
)
from telegram_bot.features.vpn_keys.handlers_vpn_keys import (
    get_vpn_keys_handlers, get_vpn_keys_callback_handlers
)
from telegram_bot.features.buy_gb.handlers_buy_gb import (
    get_buy_gb_handlers, get_buy_gb_callback_handlers, get_buy_gb_payment_handlers
)

from application.services.vpn_service import VpnService
from application.services.data_package_service import DataPackageService
from application.services.payment_service import PaymentService
from application.services.admin_service import AdminService
from application.services.common.container import get_container


def _get_admin_handlers(container) -> List[BaseHandler]:
    """Initialize and return admin handlers."""
    admin_service = container.resolve(AdminService)
    handlers = []
    handlers.extend(get_admin_handlers(admin_service))
    handlers.extend(get_admin_callback_handlers(admin_service))
    logger.info("✅ Handlers de administración configurados")
    return handlers


def _get_core_handlers(vpn_service, payment_service, data_package_service) -> List[BaseHandler]:
    """Initialize and return core feature handlers."""
    handlers = []

    handlers.extend(get_key_management_handlers(vpn_service))
    handlers.extend(get_key_management_callback_handlers(vpn_service))
    logger.info("Key management handlers configured")

    handlers.extend(get_operations_handlers(vpn_service, payment_service))
    handlers.extend(get_operations_callback_handlers(vpn_service, payment_service))
    logger.info("Operations handlers configured")

    handlers.extend(get_payments_handlers(payment_service, vpn_service))
    handlers.extend(get_payments_callback_handlers(payment_service, vpn_service))
    logger.info("Payments handlers configured")

    handlers.extend(get_user_management_handlers(vpn_service, None))
    handlers.extend(get_user_callback_handlers(vpn_service, None))
    logger.info("User management handlers configured")

    handlers.extend(get_vpn_keys_handlers(vpn_service))
    handlers.extend(get_vpn_keys_callback_handlers(vpn_service))
    logger.info("VPN keys handlers configured")

    handlers.extend(get_buy_gb_handlers(data_package_service))
    handlers.extend(get_buy_gb_callback_handlers(data_package_service))
    handlers.extend(get_buy_gb_payment_handlers(data_package_service))
    logger.info("Buy GB handlers configured")

    return handlers


def initialize_handlers(
    vpn_service: VpnService,
    payment_service: PaymentService
) -> List[BaseHandler]:
    logger.info("Initializing bot handlers...")
    handlers = []

    try:
        container = get_container()
        data_package_service = container.resolve(DataPackageService)

        handlers.extend(_get_admin_handlers(container))
        handlers.extend(_get_core_handlers(vpn_service, payment_service, data_package_service))

        logger.info(f"Total handlers configured: {len(handlers)}")
        return handlers

    except Exception as e:
        logger.error(f"Error initializing handlers: {e}")
        raise
