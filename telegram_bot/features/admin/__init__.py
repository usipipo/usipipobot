"""
Admin Feature - Panel Administrativo

Este módulo contiene toda la funcionalidad relacionada con la administración del bot,
incluyendo gestión de usuarios, llaves, estadísticas y configuración del sistema.

Author: uSipipo Team
Version: 3.0.0 - Refactored into mixins
"""

from .handlers_admin import (
    ADMIN_MENU,
    CONFIRMING_KEY_DELETE,
    CONFIRMING_USER_DELETE,
    VIEWING_KEY_DETAILS,
    VIEWING_KEYS,
    VIEWING_MAINTENANCE,
    VIEWING_SETTINGS,
    VIEWING_TICKETS,
    VIEWING_USER_DETAILS,
    VIEWING_USERS,
    AdminHandler,
)
from .handlers_keys_actions import KEYS_PER_PAGE
from .handlers_registry import (
    get_admin_callback_handlers,
    get_admin_conversation_handler,
    get_admin_handlers,
)
from .handlers_users_list import USERS_PER_PAGE

__all__ = [
    "AdminHandler",
    "get_admin_handlers",
    "get_admin_callback_handlers",
    "get_admin_conversation_handler",
    "ADMIN_MENU",
    "VIEWING_USERS",
    "VIEWING_USER_DETAILS",
    "VIEWING_KEYS",
    "VIEWING_KEY_DETAILS",
    "CONFIRMING_USER_DELETE",
    "CONFIRMING_KEY_DELETE",
    "VIEWING_SETTINGS",
    "VIEWING_MAINTENANCE",
    "VIEWING_TICKETS",
    "USERS_PER_PAGE",
    "KEYS_PER_PAGE",
]
