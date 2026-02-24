"""
Teclados para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Creditos + Shop
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class OperationsKeyboards:
    """Teclados para operaciones del usuario."""

    @staticmethod
    def operations_menu(credits: int = 0) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    f"🎁 Creditos ({credits})", callback_data="credits_menu"
                ),
            ],
            [
                InlineKeyboardButton("🛒 Shop", callback_data="shop_menu"),
            ],
            [
                InlineKeyboardButton("👥 Referidos", callback_data="referral_menu"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        from telegram_bot.keyboards import MainMenuKeyboard

        return MainMenuKeyboard.main_menu()

    @staticmethod
    def credits_menu(credits: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    "✨ Canjear por GB", callback_data="credits_redeem_data"
                ),
                InlineKeyboardButton(
                    "🔑 Canjear por Slot", callback_data="credits_redeem_slot"
                ),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def shop_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📦 Paquetes de GB", callback_data="buy_gb_menu"),
            ],
            [
                InlineKeyboardButton(
                    "🔑 Slots Adicionales", callback_data="buy_slots_menu"
                ),
            ],
            [
                InlineKeyboardButton(
                    "✨ Extras con Creditos", callback_data="credits_menu"
                ),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
