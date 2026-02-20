"""
Teclados para el modulo de compra de GB.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from application.services.data_package_service import PACKAGE_OPTIONS


class BuyGbKeyboards:
    """Teclados para compra de GB."""

    @staticmethod
    def packages_menu() -> InlineKeyboardMarkup:
        keyboard = []
        row = []
        
        for pkg in PACKAGE_OPTIONS:
            button_text = f"⭐ {pkg.name} - {pkg.data_gb}GB"
            row.append(InlineKeyboardButton(button_text, callback_data=f"buy_package_{pkg.package_type.value}"))
            
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton("📊 Ver Mis Datos", callback_data="view_data_summary"),
            InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_packages() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📦 Ver Paquetes", callback_data="buy_gb_menu"),
                InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_success() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("📦 Comprar Otro", callback_data="buy_gb_menu"),
                InlineKeyboardButton("📊 Ver Mis Datos", callback_data="view_data_summary")
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
