"""
Teclados para gestión avanzada de llaves VPN de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""

from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class KeyManagementKeyboards:
    """Teclados para gestión de llaves VPN."""

    @staticmethod
    def main_menu(keys_summary: dict) -> InlineKeyboardMarkup:
        """
        Teclado del menú principal de gestión de llaves.

        Args:
            keys_summary: Resumen de llaves por tipo

        Returns:
            InlineKeyboardMarkup: Teclado del menú principal
        """
        keyboard = []

        if keys_summary.get("total_count", 0) == 0:
            keyboard.extend(
                [
                    [
                        InlineKeyboardButton(
                            "➕ Crear Nueva", callback_data="create_key"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 Volver al Menú Principal", callback_data="main_menu"
                        )
                    ],
                ]
            )
            return InlineKeyboardMarkup(keyboard)

        if keys_summary.get("outline_count", 0) > 0:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🌐 Outline ({keys_summary['outline_count']})",
                        callback_data="keys_outline",
                    )
                ]
            )

        if keys_summary.get("wireguard_count", 0) > 0:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🔒 WireGuard ({keys_summary['wireguard_count']})",
                        callback_data="keys_wireguard",
                    )
                ]
            )

        keyboard.extend(
            [
                [
                    InlineKeyboardButton("📊 Estadísticas", callback_data="key_stats"),
                    InlineKeyboardButton("➕ Crear Nueva", callback_data="create_key"),
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Volver al Menú Principal", callback_data="main_menu"
                    )
                ],
            ]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def keys_list(keys: list) -> InlineKeyboardMarkup:
        """
        Genera teclado dinámico para lista de llaves.

        Args:
            keys: Lista de llaves VPN

        Returns:
            InlineKeyboardMarkup: Teclado de lista de llaves
        """
        keyboard = []

        for key in keys:
            # Botón principal de la llave
            status_emoji = "🟢" if key.is_active else "🔴"
            button_text = f"{status_emoji} {key.name}"
            callback_data = f"key_details_{key.id}"
            keyboard.append(
                [InlineKeyboardButton(button_text, callback_data=callback_data)]
            )

        # Opciones adicionales
        keyboard.append(
            [InlineKeyboardButton("➕ Crear Nueva", callback_data="create_key")]
        )

        keyboard.append(
            [InlineKeyboardButton("🔙 Volver", callback_data="back_to_keys")]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def key_actions(
        key_id: str, is_active: bool, key_type: str = "wireguard"
    ) -> InlineKeyboardMarkup:
        """
        Teclado de acciones para una llave específica.

        Args:
            key_id: ID de la llave
            is_active: Si la llave está activa
            key_type: Tipo de llave (wireguard, outline)

        Returns:
            InlineKeyboardMarkup: Teclado de acciones
        """
        keyboard = []

        # 1. Acción principal (Descarga/Enlace) - Prominente
        if key_type.lower() == "wireguard":
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📥 Descargar Configuración .conf",
                        callback_data=f"key_download_wg_{key_id}",
                    )
                ]
            )
        elif key_type.lower() == "outline":
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🔗 Obtener Clave de Acceso",
                        callback_data=f"key_get_link_{key_id}",
                    )
                ]
            )

        # 2. Información y Ajustes - Fila secundaria
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📊 Estadísticas", callback_data=f"key_stats_{key_id}"
                ),
                InlineKeyboardButton(
                    "⚙️ Ajustes", callback_data=f"key_config_{key_id}"
                ),
            ]
        )

        # 3. Acciones de Gestión (Estado y Nombre)
        management_row = []
        if is_active:
            management_row.append(
                InlineKeyboardButton(
                    "⏸️ Suspender", callback_data=f"key_suspend_{key_id}"
                )
            )
        else:
            management_row.append(
                InlineKeyboardButton(
                    "✅ Reactivar", callback_data=f"key_reactivate_{key_id}"
                )
            )

        management_row.append(
            InlineKeyboardButton("✏️ Renombrar", callback_data=f"key_rename_{key_id}")
        )
        keyboard.append(management_row)

        # 4. Navegación (Eliminar llave removido - evita abuso de 5GB gratis)
        keyboard.append(
            [InlineKeyboardButton("🔙 Volver a la lista", callback_data="back_to_keys")]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_submenu() -> InlineKeyboardMarkup:
        """
        Teclado para volver al submenú de llaves.

        Returns:
            InlineKeyboardMarkup: Teclado de retorno
        """
        keyboard = [
            [InlineKeyboardButton("🔙 Volver a la Lista", callback_data="back_to_keys")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancel_rename() -> InlineKeyboardMarkup:
        """
        Teclado para cancelar el renombrado.

        Returns:
            InlineKeyboardMarkup: Teclado de cancelación
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "❌ Cancelar Renombrado", callback_data="cancel_rename"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        """
        Teclado para volver al menú principal.

        Returns:
            InlineKeyboardMarkup: Teclado de retorno
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Volver al Menú Principal", callback_data="main_menu"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_main_menu() -> InlineKeyboardMarkup:
        """
        Teclado para volver al menú principal del bot.

        Returns:
            InlineKeyboardMarkup: Teclado de retorno principal
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Volver al Menú Principal", callback_data="main_menu"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_action(action: str, key_id: str) -> InlineKeyboardMarkup:
        """
        Teclado de confirmación para acciones peligrosas.

        Args:
            action: Tipo de acción
            key_id: ID de la llave

        Returns:
            InlineKeyboardMarkup: Teclado de confirmación
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Confirmar", callback_data=f"confirm_{action}_{key_id}"
                ),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"cancel_{action}"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def key_config(key_id: str) -> InlineKeyboardMarkup:
        """
        Teclado de configuración para una llave.

        Args:
            key_id: ID de la llave

        Returns:
            InlineKeyboardMarkup: Teclado de configuración
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "📋 Ver Configuración", callback_data=f"key_view_config_{key_id}"
                ),
                InlineKeyboardButton(
                    "📱 Descargar QR", callback_data=f"key_qr_{key_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Cambiar Servidor", callback_data=f"key_change_server_{key_id}"
                ),
                InlineKeyboardButton(
                    "⏰ Extender Tiempo", callback_data=f"key_extend_{key_id}"
                ),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data=f"key_details_{key_id}")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def statistics_options(key_id: Optional[str] = None) -> InlineKeyboardMarkup:
        """
        Teclado de opciones de estadísticas.

        Args:
            key_id: ID de la llave (opcional)

        Returns:
            InlineKeyboardMarkup: Teclado de estadísticas
        """
        keyboard = []

        if key_id:
            # Estadísticas de una llave específica
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📈 Uso Diario", callback_data=f"stats_daily_{key_id}"
                    ),
                    InlineKeyboardButton(
                        "📊 Uso Semanal", callback_data=f"stats_weekly_{key_id}"
                    ),
                ]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📋 Historial", callback_data=f"stats_history_{key_id}"
                    ),
                    InlineKeyboardButton(
                        "🔄 Comparar", callback_data=f"stats_compare_{key_id}"
                    ),
                ]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🔙 Volver", callback_data=f"key_details_{key_id}"
                    )
                ]
            )
        else:
            # Estadísticas generales
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📈 Por Protocolo", callback_data="stats_by_protocol"
                    ),
                    InlineKeyboardButton(
                        "📊 Por Servidor", callback_data="stats_by_server"
                    ),
                ]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📋 Historial Completo", callback_data="stats_full_history"
                    ),
                    InlineKeyboardButton(
                        "🔄 Comparar Llaves", callback_data="stats_compare_all"
                    ),
                ]
            )
            keyboard.append(
                [InlineKeyboardButton("🔙 Volver", callback_data="back_to_keys")]
            )

        return InlineKeyboardMarkup(keyboard)
