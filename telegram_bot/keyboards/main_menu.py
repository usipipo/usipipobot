"""
Menú principal del bot uSipipo.

Author: uSipipo Team
Version: 1.1.0 - Added Mini App button
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


class MainMenuKeyboard:
    """Teclado del menú principal simplificado."""

    @staticmethod
    def main_menu(miniapp_url: str | None = None) -> InlineKeyboardMarkup:
        keyboard = []

        if miniapp_url:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📱 Mini App", web_app=WebAppInfo(url=miniapp_url)
                    ),
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton("🔑 Mis Claves VPN", callback_data="show_keys"),
                InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key"),
            ]
        )

        keyboard.extend(
            [
                [
                    InlineKeyboardButton(
                        "⚙️ Operaciones", callback_data="operations_menu"
                    ),
                    InlineKeyboardButton("💾 Mis Datos", callback_data="show_usage"),
                ],
                [InlineKeyboardButton("❓ Ayuda", callback_data="help")],
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def main_menu_with_admin(
        admin_id: int, current_user_id: int, miniapp_url: str | None = None
    ) -> InlineKeyboardMarkup:
        if str(current_user_id) == str(admin_id):
            keyboard = [
                [InlineKeyboardButton("🔧 Admin", callback_data="admin_panel")],
            ]

            if miniapp_url:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            "📱 Mini App", web_app=WebAppInfo(url=miniapp_url)
                        ),
                    ]
                )

            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🔑 Mis Claves VPN", callback_data="show_keys"
                    ),
                    InlineKeyboardButton("➕ Nueva Clave", callback_data="create_key"),
                ]
            )

            keyboard.extend(
                [
                    [
                        InlineKeyboardButton(
                            "⚙️ Operaciones", callback_data="operations_menu"
                        ),
                        InlineKeyboardButton(
                            "💾 Mis Datos", callback_data="show_usage"
                        ),
                    ],
                    [InlineKeyboardButton("❓ Ayuda", callback_data="help")],
                ]
            )
            return InlineKeyboardMarkup(keyboard)
        return MainMenuKeyboard.main_menu(miniapp_url)
