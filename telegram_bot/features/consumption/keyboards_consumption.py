"""
Teclados para el módulo de tarifa por consumo.

Author: uSipipo Team
Version: 1.0.0
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class ConsumptionKeyboards:
    """Teclados para el sistema de tarifa por consumo."""

    @staticmethod
    def consumption_main_menu(
        has_active_cycle: bool = False,
        has_pending_debt: bool = False,
        can_activate: bool = False,
    ) -> InlineKeyboardMarkup:
        """
        Menú principal de tarifa por consumo.

        Args:
            has_active_cycle: Si el usuario tiene un ciclo activo
            has_pending_debt: Si el usuario tiene deuda pendiente
            can_activate: Si el usuario puede activar el modo consumo
        """
        keyboard = []

        if has_pending_debt:
            # Usuario con deuda - mostrar botón de generar factura
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "💳 Generar Factura",
                        callback_data="consumption_generate_invoice",
                    )
                ]
            )
        elif has_active_cycle:
            # Usuario con ciclo activo - ver consumo y opción de cancelar
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📊 Ver Mi Consumo", callback_data="consumption_view_status"
                    )
                ]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🚫 Cancelar Modo Consumo", callback_data="consumption_cancel"
                    )
                ]
            )
        elif can_activate:
            # Usuario puede activar
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "⚡ Activar Modo Consumo", callback_data="consumption_activate"
                    )
                ]
            )

        # Información siempre disponible
        keyboard.append(
            [
                InlineKeyboardButton(
                    "ℹ️ ¿Qué es el Modo Consumo?", callback_data="consumption_info"
                )
            ]
        )

        keyboard.append(
            [InlineKeyboardButton("🔙 Volver al Menú", callback_data="main_menu")]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def activation_confirmation() -> InlineKeyboardMarkup:
        """Teclado de confirmación para activar modo consumo."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Acepto los Términos",
                    callback_data="consumption_confirm_activate",
                )
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="consumption_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_method_selection(
        consumption_formatted: str, cost_formatted: str
    ) -> InlineKeyboardMarkup:
        """
        Teclado para seleccionar método de pago.

        Args:
            consumption_formatted: Consumo formateado (ej: "5.23 GB")
            cost_formatted: Costo formateado (ej: "$2.35 USD")
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "💫 Pagar con Telegram Stars", callback_data="consumption_pay_stars"
                )
            ],
            [
                InlineKeyboardButton(
                    "💰 Pagar con Crypto (USDT)", callback_data="consumption_pay_crypto"
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="consumption_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_consumption_menu() -> InlineKeyboardMarkup:
        """Teclado para volver al menú de consumo."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 Menú Consumo", callback_data="consumption_menu"
                ),
                InlineKeyboardButton("🔙 Menú Principal", callback_data="main_menu"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def generate_new_invoice() -> InlineKeyboardMarkup:
        """Teclado para generar nueva factura si expiró."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Generar Nueva Factura",
                    callback_data="consumption_generate_invoice",
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="consumption_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def activation_success() -> InlineKeyboardMarkup:
        """Teclado tras activación exitosa."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 Ver Mi Consumo", callback_data="consumption_view_status"
                )
            ],
            [InlineKeyboardButton("🔙 Menú Principal", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_success() -> InlineKeyboardMarkup:
        """Teclado tras pago exitoso."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "⚡ Activar Nuevo Ciclo", callback_data="consumption_activate"
                )
            ],
            [InlineKeyboardButton("🔙 Menú Principal", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def view_info_only() -> InlineKeyboardMarkup:
        """Teclado solo informativo."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "⚡ Activar Modo Consumo", callback_data="consumption_activate"
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancellation_confirmation() -> InlineKeyboardMarkup:
        """Teclado de confirmación para cancelar modo consumo."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Sí, Cancelar Modo Consumo",
                    callback_data="consumption_confirm_cancel",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ No, Mantener Activo", callback_data="consumption_menu"
                )
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancel_success_keyboard() -> InlineKeyboardMarkup:
        """Teclado tras cancelación exitosa."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 Generar Factura", callback_data="consumption_generate_invoice"
                )
            ],
            [InlineKeyboardButton("🔙 Menú Principal", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
