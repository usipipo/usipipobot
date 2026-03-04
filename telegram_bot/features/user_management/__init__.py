"""
User Management Feature - Sistema de Gestión de Usuarios

Este módulo contiene toda la funcionalidad relacionada con la gestión de usuarios,
perfiles, autenticación y autorización.

Author: uSipipo Team
Version: 3.0.0 - Refactored into mixins
"""

from .handlers_user_management import (
    get_user_callback_handlers,
    get_user_management_handlers,
    UserManagementHandler,
)

# Re-export mixins for advanced usage
from .handlers_menu_callbacks import MenuCallbacksMixin
from .handlers_user_actions import UserActionsMixin
from .handlers_user_profile import UserProfileMixin

__all__ = [
    "UserManagementHandler",
    "get_user_management_handlers",
    "get_user_callback_handlers",
    # Mixins for advanced usage
    "UserActionsMixin",
    "UserProfileMixin",
    "MenuCallbacksMixin",
]
