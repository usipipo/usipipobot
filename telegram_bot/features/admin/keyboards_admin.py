"""
Teclados para panel administrativo de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Complete admin management
"""

from typing import Any, Dict, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class AdminKeyboards:
    """Teclados para panel administrativo."""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Teclado del menú principal administrativo."""
        keyboard = [
            [
                InlineKeyboardButton("👥 Usuarios", callback_data="admin_show_users"),
                InlineKeyboardButton("🔑 Llaves VPN", callback_data="admin_show_keys"),
            ],
            [
                InlineKeyboardButton(
                    "📊 Dashboard", callback_data="admin_server_status"
                ),
                InlineKeyboardButton("🎫 Tickets", callback_data="admin_tickets"),
            ],
            [
                InlineKeyboardButton(
                    "⚙️ Configuración", callback_data="admin_settings"
                ),
                InlineKeyboardButton(
                    "🔧 Mantenimiento", callback_data="admin_maintenance"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚡ Gestionar Servidores VPN", callback_data="admin_vpn"
                ),
            ],
            [
                InlineKeyboardButton("📋 Ver Logs", callback_data="admin_logs"),
                InlineKeyboardButton("🚪 Salir", callback_data="end_admin"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        """Teclado para volver al menú admin."""
        keyboard = [[InlineKeyboardButton("🔙 Menú Admin", callback_data="admin")]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_user_menu() -> InlineKeyboardMarkup:
        """Teclado para volver al menú de usuario."""
        from telegram_bot.common.keyboards import get_miniapp_url
        from telegram_bot.keyboards import MainMenuKeyboard

        return MainMenuKeyboard.main_menu(miniapp_url=get_miniapp_url())

    @staticmethod
    def back_to_users() -> InlineKeyboardMarkup:
        """Teclado para volver a lista de usuarios."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Volver a Usuarios", callback_data="admin_show_users"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_keys() -> InlineKeyboardMarkup:
        """Teclado para volver a lista de llaves."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Volver a Llaves", callback_data="admin_show_keys"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def users_list_paginated(
        users: List[Dict[str, Any]], page: int, total_pages: int
    ) -> InlineKeyboardMarkup:
        """Teclado con lista de usuarios paginada."""
        keyboard = []

        for user in users:
            status_icon = "✅" if user.get("status") == "active" else "❌"
            full_name = (
                user.get("full_name")
                or user.get("username")
                or f"User {user.get('user_id')}"
            )
            if len(full_name) > 20:
                full_name = full_name[:20] + "..."
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status_icon} {full_name} ({user.get('user_id')})",
                        callback_data=f"user_details_{user.get('user_id')}",
                    )
                ]
            )

        nav_row = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    "⬅️ Anterior", callback_data=f"users_page_{page - 1}"
                )
            )
        nav_row.append(
            InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop")
        )
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    "➡️ Siguiente", callback_data=f"users_page_{page + 1}"
                )
            )
        keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("🔙 Menú Admin", callback_data="admin")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def user_actions(user_id: int, is_active: bool) -> InlineKeyboardMarkup:
        """Teclado de acciones para un usuario específico."""
        keyboard = []

        if is_active:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "⏸️ Suspender", callback_data=f"user_suspend_{user_id}"
                    ),
                ]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "✅ Reactivar", callback_data=f"user_reactivate_{user_id}"
                    ),
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🗑️ Eliminar Usuario", callback_data=f"user_delete_{user_id}"
                )
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 Volver a Usuarios", callback_data="admin_show_users"
                ),
                InlineKeyboardButton("🏠 Menú Admin", callback_data="admin"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def keys_filter_menu() -> InlineKeyboardMarkup:
        """Teclado para filtrar llaves por tipo."""
        keyboard = [
            [
                InlineKeyboardButton("🔑 Todas", callback_data="keys_filter_all"),
                InlineKeyboardButton(
                    "⚡ WireGuard", callback_data="keys_filter_wireguard"
                ),
                InlineKeyboardButton("🔵 Outline", callback_data="keys_filter_outline"),
            ],
            [InlineKeyboardButton("🔙 Menú Admin", callback_data="admin")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def keys_list_paginated(
        keys: List[Dict[str, Any]], page: int, total_pages: int, key_filter: str = "all"
    ) -> InlineKeyboardMarkup:
        """Teclado con lista de llaves paginada."""
        keyboard = []

        for key in keys:
            status_icon = "✅" if key.get("is_active") else "❌"
            key_type_icon = (
                "⚡" if key.get("key_type", "").lower() == "wireguard" else "🔵"
            )
            key_name = key.get("key_name") or f"Key {str(key.get('key_id', ''))[:8]}"
            if len(key_name) > 15:
                key_name = key_name[:15] + "..."
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status_icon} {key_type_icon} {key_name}",
                        callback_data=f"admin_key_details_{key.get('key_id')}",
                    )
                ]
            )

        filter_row = [
            InlineKeyboardButton("🔑 Todas", callback_data="keys_filter_all"),
            InlineKeyboardButton("⚡ WG", callback_data="keys_filter_wireguard"),
            InlineKeyboardButton("🔵 OL", callback_data="keys_filter_outline"),
        ]
        keyboard.append(filter_row)

        nav_row = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    "⬅️ Anterior", callback_data=f"keys_page_{page - 1}"
                )
            )
        nav_row.append(
            InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop")
        )
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    "➡️ Siguiente", callback_data=f"keys_page_{page + 1}"
                )
            )
        keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("🔙 Menú Admin", callback_data="admin")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def key_actions(key_id: str, is_active: bool) -> InlineKeyboardMarkup:
        """Teclado de acciones para una llave específica."""
        keyboard = []

        if is_active:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "⏸️ Suspender", callback_data=f"admin_key_suspend_{key_id}"
                    ),
                ]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "✅ Reactivar", callback_data=f"admin_key_reactivate_{key_id}"
                    ),
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🗑️ Eliminar Llave", callback_data=f"admin_key_delete_{key_id}"
                )
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 Volver a Llaves", callback_data="admin_show_keys"
                ),
                InlineKeyboardButton("🏠 Menú Admin", callback_data="admin"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirmation(action: str, target_id) -> InlineKeyboardMarkup:
        """Teclado de confirmación para acciones peligrosas."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Confirmar", callback_data=f"confirm_{action}_{target_id}"
                ),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_{action}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def dashboard_actions() -> InlineKeyboardMarkup:
        """Teclado de acciones del dashboard."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 Ver Usuarios", callback_data="admin_show_users"
                ),
                InlineKeyboardButton("🔑 Ver Llaves", callback_data="admin_show_keys"),
            ],
            [InlineKeyboardButton("🔙 Menú Admin", callback_data="admin")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Teclado del menú de configuración."""
        keyboard = [
            [
                InlineKeyboardButton("🌐 Servidores", callback_data="settings_servers"),
                InlineKeyboardButton("📊 Límites", callback_data="settings_limits"),
            ],
            [
                InlineKeyboardButton(
                    "👤 Administradores", callback_data="settings_admins"
                ),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="admin")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def maintenance_menu() -> InlineKeyboardMarkup:
        """Teclado del menú de mantenimiento."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Reiniciar WG", callback_data="restart_wireguard"
                ),
                InlineKeyboardButton(
                    "🔄 Reiniciar OL", callback_data="restart_outline"
                ),
            ],
            [
                InlineKeyboardButton("🧹 Limpiar Logs", callback_data="clear_logs"),
                InlineKeyboardButton("📦 Backup BD", callback_data="backup_db"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="admin")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_settings() -> InlineKeyboardMarkup:
        """Teclado para volver a configuración."""
        keyboard = [
            [InlineKeyboardButton("🔙 Volver a Config", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_maintenance() -> InlineKeyboardMarkup:
        """Teclado para volver a mantenimiento."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Volver a Mantenimiento", callback_data="admin_maintenance"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
