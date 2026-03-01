"""
Mensajes para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Creditos + Shop
"""

from utils.message_separators import (
    MessageSeparatorBuilder,
    TELEGRAM_MOBILE_WIDTH,
    section_separator,
)


class OperationsMessages:
    """Mensajes para operaciones del usuario."""

    class Menu:
        MAIN = (
            "⚙️ **Operaciones**\n\n"
            "Gestiona tu cuenta y servicios:\n\n"
            "🎁 **Créditos** - Canjea por beneficios especiales\n"
            "👥 **Referidos** - Invita amigos y gana recompensas\n"
            "🛒 **Shop** - Compra paquetes de datos y slots\n"
            "📜 **Historial** - Revisa todas tus transacciones\n\n"
            "Selecciona una opción:"
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
