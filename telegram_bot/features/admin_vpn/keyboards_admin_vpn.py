"""
Keyboards for admin VPN management.

Author: uSipipo Team
Version: 1.0.0 - VPN Server Management
"""

from typing import Any, Dict, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class AdminVpnKeyboards:
    """Keyboards for admin VPN management."""

    @staticmethod
    def vpn_management_menu() -> InlineKeyboardMarkup:
        """Main VPN management menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 Estado Servidores", callback_data="vpn_status"
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚡ Gestionar WireGuard", callback_data="vpn_manage_wireguard"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔵 Gestionar Outline", callback_data="vpn_manage_outline"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🧹 Limpieza Claves Fantasmas", callback_data="vpn_cleanup_ghosts"
                ),
            ],
            [InlineKeyboardButton("🔙 Menú Admin", callback_data="admin")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def server_actions(server_type: str) -> InlineKeyboardMarkup:
        """Actions for a specific server type."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔑 Ver Claves", callback_data=f"vpn_list_keys_{server_type}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Estado Detallado", callback_data=f"vpn_server_status_{server_type}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 Volver a VPN", callback_data="admin_vpn"
                ),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def key_actions(key_id: str, is_active: bool, key_type: str) -> InlineKeyboardMarkup:
        """Enable/Disable/Delete buttons for a key."""
        keyboard = []
        key_id_short = key_id[:8] if len(key_id) > 8 else key_id

        if is_active:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "⏸️ Deshabilitar",
                        callback_data=f"vkdis_{key_type}_{key_id_short}",
                    ),
                ]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "✅ Habilitar",
                        callback_data=f"vke_{key_type}_{key_id_short}",
                    ),
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🗑️ Eliminar Clave",
                    callback_data=f"vkdel_{key_type}_{key_id_short}",
                ),
            ]
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 Volver a Lista",
                    callback_data=f"vpn_list_keys_{key_type}",
                ),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirmation(action: str, key_id: str, key_type: str) -> InlineKeyboardMarkup:
        """Confirm/cancel buttons for dangerous actions."""
        key_id_short = key_id[:8] if len(key_id) > 8 else key_id
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Confirmar",
                    callback_data=f"vc_{action}_{key_type}_{key_id_short}",
                ),
                InlineKeyboardButton(
                    "❌ Cancelar",
                    callback_data=f"vx_{action}_{key_type}_{key_id_short}",
                ),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def keys_list_paginated(
        keys: List[Dict[str, Any]], page: int, total_pages: int, server_type: str
    ) -> InlineKeyboardMarkup:
        """Keyboard with paginated keys list."""
        keyboard = []

        for key in keys:
            status_icon = "✅" if key.get("is_active") else "❌"
            key_id = str(key.get('id', ''))
            key_id_short = key_id[:8] if len(key_id) > 8 else key_id
            key_name = key.get("name") or f"Key {key_id_short}"
            if len(key_name) > 20:
                key_name = key_name[:20] + "..."
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status_icon} {key_name}",
                        callback_data=f"vkdet_{server_type}_{key_id_short}",
                    )
                ]
            )

        nav_row = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    "⬅️ Anterior", callback_data=f"vpn_keys_page_{server_type}_{page - 1}"
                )
            )
        nav_row.append(
            InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop")
        )
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    "➡️ Siguiente", callback_data=f"vpn_keys_page_{server_type}_{page + 1}"
                )
            )
        keyboard.append(nav_row)

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 Volver", callback_data=f"vpn_manage_{server_type}"
                )
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_vpn_menu() -> InlineKeyboardMarkup:
        """Keyboard to go back to VPN menu."""
        keyboard = [
            [InlineKeyboardButton("🔙 Menú VPN", callback_data="admin_vpn")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_server(server_type: str) -> InlineKeyboardMarkup:
        """Keyboard to go back to server management."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Volver", callback_data=f"vpn_manage_{server_type}"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
