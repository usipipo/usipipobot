"""
Teclados para gestión de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Cyberpunk UX
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class VpnKeysKeyboards:
    """Teclados para gestión de llaves VPN - Estilo Cyberpunk."""

    @staticmethod
    def vpn_types() -> InlineKeyboardMarkup:
        """
        Teclado para seleccionar tipo de VPN.

        Returns:
            InlineKeyboardMarkup: Teclado de tipos VPN
        """
        keyboard = [
            [
                InlineKeyboardButton("🌐 Outline", callback_data="type_outline"),
                InlineKeyboardButton("🔒 WireGuard", callback_data="type_wireguard"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancel_creation() -> InlineKeyboardMarkup:
        """
        Teclado con botón de cancelar creación.

        Returns:
            InlineKeyboardMarkup: Teclado de cancelación
        """
        keyboard = [
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_create_key")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def key_actions(is_admin: bool = False) -> InlineKeyboardMarkup:
        """
        Teclado de acciones para una llave específica.

        Args:
            is_admin: Si es True, incluye opciones adicionales

        Returns:
            InlineKeyboardMarkup: Teclado de acciones
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "✏️ Renombrar", callback_data="key_rename_{key_id}"
                ),
                # Delete button removed - prevents abuse of free 5GB
            ],
        ]

        if is_admin:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🔧 Admin Options", callback_data="key_admin_{key_id}"
                    )
                ]
            )

        keyboard.append(
            [InlineKeyboardButton("🔙 Volver", callback_data="back_to_keys")]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def limit_reached_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """
        Teclado cuando se alcanza el límite de llaves - Incluye opción de comprar slots.

        Args:
            is_admin: Si es True, incluye opciones de administrador

        Returns:
            InlineKeyboardMarkup: Teclado del menú de límite alcanzado
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔑 Comprar Slots Extra", callback_data="buy_slots_menu"
                ),
                InlineKeyboardButton("📦 Ver Planes", callback_data="buy_gb_menu"),
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Gestionar Llaves", callback_data="key_management"
                ),
                InlineKeyboardButton("🔙 Volver", callback_data="main_menu"),
            ],
        ]

        if is_admin:
            keyboard.insert(
                0, [InlineKeyboardButton("🔧 Panel Admin", callback_data="admin")]
            )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def key_list(keys: list, is_admin: bool = False) -> InlineKeyboardMarkup:
        """
        Genera teclado dinámico para lista de llaves - Estilo Cyberpunk.

        Args:
            keys: Lista de llaves VPN
            is_admin: Si es True, incluye opciones adicionales

        Returns:
            InlineKeyboardMarkup: Teclado de lista de llaves
        """
        keyboard = []

        for key in keys:
            # Botón principal de la llave con icono según tipo
            icon = "🌐" if key.type.lower() == "outline" else "🔒"
            button_text = f"{icon} {key.name}"
            callback_data = f"key_details_{key.id}"
            keyboard.append(
                [InlineKeyboardButton(button_text, callback_data=callback_data)]
            )

        # Opciones adicionales
        keyboard.append(
            [InlineKeyboardButton("➕ Crear Nueva", callback_data="create_key")]
        )

        if is_admin:
            keyboard.append(
                [InlineKeyboardButton("🔧 Admin Keys", callback_data="admin_keys")]
            )

        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="main_menu")])

        return InlineKeyboardMarkup(keyboard)
