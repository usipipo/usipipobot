"""
Teclados para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 2.0.0 - Feature-based architecture
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class OperationsKeyboards:
    """Teclados para operaciones del usuario."""

    @staticmethod
    def operations_menu() -> InlineKeyboardMarkup:
        """
        Teclado del menú principal de operaciones.

        Returns:
            InlineKeyboardMarkup: Teclado del menú de operaciones
        """
        keyboard = [
            [
                InlineKeyboardButton("💰 Mi Balance", callback_data="balance"),
            ],
            [
                InlineKeyboardButton("📊 Transacciones", callback_data="transactions"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """
        Teclado para volver al menú principal del bot.

        Args:
            is_admin: Si es True, incluye opciones de administrador

        Returns:
            InlineKeyboardMarkup: Teclado de retorno
        """
        keyboard = [
            [
                InlineKeyboardButton("🛡️ Mis Llaves", callback_data="operations"),
                InlineKeyboardButton("📊 Estado", callback_data="status"),
            ],
            [
                InlineKeyboardButton("💰 Operaciones", callback_data="operations"),
                InlineKeyboardButton("🏆 Logros", callback_data="achievements"),
            ],
            [InlineKeyboardButton("⚙️ Ayuda", callback_data="help")],
        ]

        # Agregar opciones de administrador si corresponde
        if is_admin:
            keyboard.insert(
                0, [InlineKeyboardButton("🔧 Panel Admin", callback_data="admin")]
            )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def balance_actions() -> InlineKeyboardMarkup:
        """
        Teclado de acciones de balance.

        Returns:
            InlineKeyboardMarkup: Teclado de balance
        """
        keyboard = [
            [
                InlineKeyboardButton("💳 Recargar", callback_data="add_balance"),
                InlineKeyboardButton("📊 Historial", callback_data="balance_history"),
            ],
            [
                InlineKeyboardButton(
                    "🎁 Canjear Recompensas", callback_data="redeem_rewards"
                ),
                InlineKeyboardButton("📈 Estadísticas", callback_data="balance_stats"),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_methods() -> InlineKeyboardMarkup:
        """
        Teclado de métodos de pago.

        Returns:
            InlineKeyboardMarkup: Teclado de pagos
        """
        keyboard = [
            [
                InlineKeyboardButton("💳 Tarjeta de Crédito", callback_data="pay_card"),
                InlineKeyboardButton("🏦 Transferencia", callback_data="pay_transfer"),
            ],
            [
                InlineKeyboardButton("₿ Criptomonedas", callback_data="pay_crypto"),
                InlineKeyboardButton("📱 PayPal", callback_data="pay_paypal"),
            ],
            [InlineKeyboardButton("🔙 Cancelar", callback_data="cancel_payment")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirmation_dialog(action: str, amount: float = None) -> InlineKeyboardMarkup:
        """
        Teclado de confirmación para operaciones.

        Args:
            action: Tipo de acción
            amount: Monto (opcional)

        Returns:
            InlineKeyboardMarkup: Teclado de confirmación
        """
        keyboard = []

        if action == "add_balance" and amount:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"✅ Confirmar ${amount:.2f}",
                        callback_data=f"confirm_add_{amount}",
                    ),
                    InlineKeyboardButton("❌ Cancelar", callback_data="cancel_add"),
                ]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "✅ Confirmar", callback_data=f"confirm_{action}"
                    ),
                    InlineKeyboardButton(
                        "❌ Cancelar", callback_data=f"cancel_{action}"
                    ),
                ]
            )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def transaction_filters() -> InlineKeyboardMarkup:
        """
        Teclado de filtros para transacciones.

        Returns:
            InlineKeyboardMarkup: Teclado de filtros
        """
        keyboard = [
            [
                InlineKeyboardButton("📅 Todas", callback_data="filter_all"),
                InlineKeyboardButton("💳 Depósitos", callback_data="filter_deposits"),
            ],
            [
                InlineKeyboardButton("💸 Gastos", callback_data="filter_spending"),
                InlineKeyboardButton("🎁 Recompensas", callback_data="filter_rewards"),
            ],
            [
                InlineKeyboardButton("📊 Últimos 7 días", callback_data="filter_week"),
                InlineKeyboardButton(
                    "📅 Últimos 30 días", callback_data="filter_month"
                ),
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="operations_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)
