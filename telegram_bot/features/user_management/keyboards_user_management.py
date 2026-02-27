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
        from telegram_bot.common.keyboards import get_miniapp_url
        from telegram_bot.keyboards import MainMenuKeyboard

        miniapp_url = get_miniapp_url()
        if is_admin:
            from config import settings

            return MainMenuKeyboard.main_menu_with_admin(
                admin_id=int(settings.ADMIN_ID),
                current_user_id=int(settings.ADMIN_ID),
                miniapp_url=miniapp_url,
            )
        return MainMenuKeyboard.main_menu(miniapp_url=miniapp_url)

    @staticmethod
    def profile_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """
        Teclado del menú de perfil con botón de historial.

        Args:
            is_admin: Si es True, incluye opciones de administrador

        Returns:
            InlineKeyboardMarkup: Teclado del menú de perfil
        """
        keyboard = [
            [
                InlineKeyboardButton("📜 Historial", callback_data="show_history"),
                InlineKeyboardButton("📊 Estado", callback_data="status"),
            ],
            [
                InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu"),
            ],
        ]

        if is_admin:
            keyboard.append(
                [
                    InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel"),
                ]
            )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def help_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📚 FAQ", callback_data="help_faq"),
                InlineKeyboardButton("🎁 Bonos", callback_data="help_bonuses"),
            ],
            [
                InlineKeyboardButton("🎫 Soporte", callback_data="help_support"),
            ],
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def support_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🎫 Crear Ticket", callback_data="create_ticket")],
            [InlineKeyboardButton("📋 Mis Tickets", callback_data="list_my_tickets")],
            [InlineKeyboardButton("🔙 Volver", callback_data="help")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_help() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🔙 Volver a Ayuda", callback_data="help")],
        ]
        return InlineKeyboardMarkup(keyboard)
