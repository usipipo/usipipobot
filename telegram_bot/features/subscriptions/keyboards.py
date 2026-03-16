"""
Teclados para gestión de suscripciones de uSipipo.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class SubscriptionKeyboards:
    """Teclados para gestión de suscripciones."""

    @staticmethod
    def subscription_menu() -> InlineKeyboardMarkup:
        """Keyboard para el menú de suscripciones."""
        keyboard = [
            [
                InlineKeyboardButton("🥇 1 Mes - 360 ⭐", callback_data="sub_1_month"),
            ],
            [
                InlineKeyboardButton("🥈 3 Meses - 960 ⭐", callback_data="sub_3_months"),
            ],
            [
                InlineKeyboardButton("🥉 6 Meses - 1560 ⭐", callback_data="sub_6_months"),
            ],
            [InlineKeyboardButton("« Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_purchase(plan_type: str) -> InlineKeyboardMarkup:
        """Keyboard para confirmar compra de suscripción."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data=f"sub_confirm_{plan_type}"),
                InlineKeyboardButton("❌ Cancelar", callback_data="subscriptions"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def active_subscription() -> InlineKeyboardMarkup:
        """Keyboard para usuario con suscripción activa."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Ver Estado", callback_data="sub_status"),
            ],
            [InlineKeyboardButton("« Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def subscription_status() -> InlineKeyboardMarkup:
        """Keyboard para ver estado de suscripción."""
        keyboard = [
            [InlineKeyboardButton("« Volver", callback_data="subscriptions")],
        ]
        return InlineKeyboardMarkup(keyboard)
