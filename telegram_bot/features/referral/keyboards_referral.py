"""
Teclados para el modulo de referidos.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import settings


class ReferralKeyboards:
    """Teclados para el sistema de referidos."""

    @staticmethod
    def main_menu(credits: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("💳 Canjear Creditos", callback_data="referral_redeem_menu"),
            ],
            [
                InlineKeyboardButton("📋 Copiar Codigo", callback_data="referral_copy_code"),
                InlineKeyboardButton("🔄 Actualizar", callback_data="referral_refresh"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def redeem_menu(credits: int) -> InlineKeyboardMarkup:
        keyboard = []
        
        can_redeem_data = credits >= settings.REFERRAL_CREDITS_PER_GB
        can_redeem_slot = credits >= settings.REFERRAL_CREDITS_PER_SLOT
        
        if can_redeem_data:
            keyboard.append([
                InlineKeyboardButton(
                    f"📦 1 GB Extra ({settings.REFERRAL_CREDITS_PER_GB} cr.)",
                    callback_data="referral_redeem_data"
                )
            ])
        
        if can_redeem_slot:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔑 +1 Slot ({settings.REFERRAL_CREDITS_PER_SLOT} cr.)",
                    callback_data="referral_redeem_slot"
                )
            ])
        
        if not can_redeem_data and not can_redeem_slot:
            keyboard.append([
                InlineKeyboardButton("❌ Sin creditos suficientes", callback_data="referral_noop")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Volver", callback_data="referral_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_redeem_data(credits: int, gb: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data="referral_confirm_data"),
                InlineKeyboardButton("❌ Cancelar", callback_data="referral_redeem_menu"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_redeem_slot(credits: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data="referral_confirm_slot"),
                InlineKeyboardButton("❌ Cancelar", callback_data="referral_redeem_menu"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def success_back() -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("💳 Canjear Mas", callback_data="referral_redeem_menu"),
                InlineKeyboardButton("📋 Mi Codigo", callback_data="referral_menu"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
