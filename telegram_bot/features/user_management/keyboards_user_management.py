"""
Teclados para gestión de usuarios de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class UserManagementKeyboards:
    """Teclados para gestión de usuarios."""

    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """
        Genera el menú principal según el tipo de usuario.

        NOTE: Para el nuevo menú simplificado, usar MainMenuKeyboard
        from telegram_bot.keyboards import MainMenuKeyboard

        Args:
            is_admin: Si es True, incluye opciones de administrador

        Returns:
            InlineKeyboardMarkup: Teclado del menú principal
        """
        from telegram_bot.keyboards import MainMenuKeyboard

        if is_admin:
            from config import settings

            return MainMenuKeyboard.main_menu_with_admin(
                admin_id=int(settings.ADMIN_ID), current_user_id=int(settings.ADMIN_ID)
            )
        return MainMenuKeyboard.main_menu()
