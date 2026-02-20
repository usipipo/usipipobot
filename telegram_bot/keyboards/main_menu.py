"""
Menú principal del bot uSipipo.

Author: uSipipo Team
Version: 1.0.0 - Main Menu Module
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenuKeyboard:
    """Teclado del menú principal simplificado."""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("🔑 Mis Claves VPN", callback_data="show_keys"),
                InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key")
            ],
            [
                InlineKeyboardButton("📦 Comprar GB", callback_data="buy_data"),
                InlineKeyboardButton("💾 Mis Datos", callback_data="show_usage")
            ],
            [
                InlineKeyboardButton("❓ Ayuda", callback_data="help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def main_menu_with_admin(admin_id: int, current_user_id: int) -> InlineKeyboardMarkup:
        keyboard = MainMenuKeyboard.main_menu()
        if str(current_user_id) == str(admin_id):
            keyboard.keyboard.insert(0, [
                InlineKeyboardButton("🔧 Admin", callback_data="admin_panel")
            ])
        return keyboard
