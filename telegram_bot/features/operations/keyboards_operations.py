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
            # Sección de Beneficios y Referidos
            [
                InlineKeyboardButton(f"🎁 Créditos ({credits})", callback_data="credits_menu"),
                InlineKeyboardButton("👥 Referidos", callback_data="referral_menu"),
            ],
            # Sección de Compras e Historial
            [
                InlineKeyboardButton("🛒 Shop", callback_data="shop_menu"),
                InlineKeyboardButton("📜 Historial", callback_data="transactions_history"),
            ],
            # Volver
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        from telegram_bot.common.keyboards import get_miniapp_url
        from telegram_bot.keyboards import MainMenuKeyboard

        return MainMenuKeyboard.main_menu(miniapp_url=get_miniapp_url())

    @staticmethod
    def credits_menu(credits: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("✨ Canjear por GB", callback_data="credits_redeem_data"),
                InlineKeyboardButton("🔑 Canjear por Slot", callback_data="credits_redeem_slot"),
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
                InlineKeyboardButton("🔑 Slots Adicionales", callback_data="buy_slots_menu"),
            ],
            [
                InlineKeyboardButton("✨ Extras con Creditos", callback_data="credits_menu"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def transactions_history_menu(has_more: bool = False, page: int = 0) -> InlineKeyboardMarkup:
        """Teclado para el historial de transacciones."""
        keyboard = []

        # Botones de paginación si hay más páginas
        if page > 0 or has_more:
            nav_buttons = []
            if page > 0:
                prev_callback = f"transactions_page_{page - 1}"
                nav_buttons.append(InlineKeyboardButton("◀️ Anterior", callback_data=prev_callback))
            if has_more:
                next_callback = f"transactions_page_{page + 1}"
                nav_buttons.append(InlineKeyboardButton("Siguiente ▶️", callback_data=next_callback))
            keyboard.append(nav_buttons)

        keyboard.append(
            [InlineKeyboardButton("🔙 Volver a Operaciones", callback_data="operations_menu")]
        )
        return InlineKeyboardMarkup(keyboard)
