"""
Mensajes para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.1.0 - Elegant UI
"""

from utils.message_separators import (
    MessageSeparatorBuilder,
    TELEGRAM_MOBILE_WIDTH,
    section_separator,
)


# Separadores predefinidos para consistencia visual
_SEP_HEADER = (
    MessageSeparatorBuilder()
    .compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_DIVIDER = (
    MessageSeparatorBuilder()
    .compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_DECORATIVE = (
    MessageSeparatorBuilder()
    .compact().style("bold").length(9).with_emoji("🔹", "both").build()
)


class OperationsMessages:
    """Mensajes para operaciones del usuario."""

    class Menu:
        """Mensajes para el menú principal de operaciones."""

        # Header del menú con estructura moderna/tech
        _HEADER = (
            f"{_SEP_HEADER}\n"
            "🔧 *CENTRO DE OPERACIONES*\n"
            f"{_SEP_HEADER}\n"
        )

        _CREDITS_INDICATOR = (
            "\n"
            "💎 *Créditos disponibles:* `{credits}`\n"
            f"{_SEP_DIVIDER}\n"
        )

        _TREE_STRUCTURE = (
            "\n"
            "*Gestiona tu cuenta:*\n"
            "│\n"
            "├─ 🎁 *Créditos*\n"
            "│  └─ Canjea por beneficios especiales\n"
            "│\n"
            "├─ 👥 *Referidos*\n"
            "│  └─ Invita amigos y gana recompensas\n"
            "│\n"
            "├─ 🛒 *Shop*\n"
            "│  └─ Compra paquetes de datos y slots\n"
            "│\n"
            "└─ 📜 *Historial*\n"
            "   └─ Revisa todas tus transacciones\n"
        )

        _FOOTER = (
            f"\n{_SEP_DIVIDER}\n"
            "👇 *Selecciona una opción:*"
        )

        @classmethod
        def main_with_credits(cls, credits: int = 0) -> str:
            """Genera mensaje principal con indicador de créditos."""
            message = cls._HEADER
            if credits > 0:
                message += cls._CREDITS_INDICATOR.format(credits=credits)
            message += cls._TREE_STRUCTURE
            message += cls._FOOTER
            return message

        # Mensaje legacy para compatibilidad (sin créditos)
        MAIN = (
            _HEADER +
            _TREE_STRUCTURE +
            _FOOTER
        )

    class Credits:
        DISPLAY = (
            "🎁 **Tus Creditos**\n\n"
            "💎 **Creditos disponibles:** {credits}\n\n"
            "💡 Los creditos se obtienen al referir amigos.\n"
            "Usalos para obtener GB extra o slots adicionales."
        )

        REDEEM_DATA = (
            "📦 **Canjear Creditos por GB**\n\n"
            "💡 {credits_per_gb} creditos = 1 GB de navegacion\n\n"
            "Tus creditos: {credits}\n"
            "GB disponibles para canjear: {gb_available}"
        )

        REDEEM_SLOT = (
            "🔑 **Canjear Creditos por Slot**\n\n"
            "💡 {credits_per_slot} creditos = 1 slot adicional\n\n"
            "Tus creditos: {credits}\n"
            "Puedes obtener: {slots_available} slot(s)"
        )

    class Shop:
        MENU = (
            "🛒 **Shop**\n\n"
            "📦 **Paquetes de GB** - Compra con Telegram Stars\n"
            "🔑 **Slots** - Mas claves VPN con Telegram Stars\n"
            "✨ **Extras** - Canjea tus creditos de referido\n\n"
            "Selecciona lo que deseas comprar:"
        )

    class Error:
        SYSTEM_ERROR = (
            "❌ **Error del Sistema**\n\n"
            "No pude procesar tu solicitud.\n\n"
            "Por favor, intenta mas tarde."
        )

        INSUFFICIENT_CREDITS = (
            "💸 **Creditos Insuficientes**\n\n"
            "No tienes suficientes creditos para esta operacion.\n\n"
            "💡 Invita mas amigos para obtener creditos."
        )

    class Transactions:
        """Mensajes para historial de transacciones."""

        # Separadores reutilizables - usando ancho óptimo para móviles
        _SEP_DOUBLE = (
            MessageSeparatorBuilder()
            .compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
        )
        _SEP_SIMPLE = (
            MessageSeparatorBuilder()
            .compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
        )

        HISTORY_HEADER = (
            section_separator("Historial de Transacciones", "📜")
            + f"{_SEP_DOUBLE}\n"
        )

        NO_TRANSACTIONS = (
            section_separator("Sin Transacciones", "📭")
            + "Aún no tienes transacciones registradas.\n\n"
            + "💡 Ve al 🛒 *Shop* para hacer tu primera compra."
        )

        ORDER_ITEM = (
            "{status_emoji} *{package_type}*\n"
            "   ├─ 💰 {amount_usdt} USDT\n"
            "   ├─ 📅 {date}\n"
            "   └─ {status_icon} Estado: {status_text}\n"
            f"{_SEP_SIMPLE}\n"
        )

        HISTORY_FOOTER = (
            f"{_SEP_DOUBLE}\n\n"
            "💵 Total: {total_usdt} USDT | 📦 {total_count} transacciones"
        )

        PAGE_FOOTER = "\n📄 Página {page}"

    class Success:
        OPERATION_COMPLETED = (
            "✅ **Operacion Completada**\n\n"
            "Tu solicitud ha sido procesada exitosamente."
        )
