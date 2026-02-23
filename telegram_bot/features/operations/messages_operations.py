"""
Mensajes para operaciones del usuario de uSipipo.

Author: uSipipo Team
Version: 3.0.0 - Creditos + Shop
"""


class OperationsMessages:
    """Mensajes para operaciones del usuario."""

    class Menu:
        MAIN = (
            "⚙️ **Operaciones**\n\n"
            "Gestiona tu cuenta y servicios:\n\n"
            "🎁 **Creditos** - Obtén beneficios por referir amigos\n"
            "🛒 **Shop** - Compra paquetes y slots\n"
            "👥 **Referidos** - Invita amigos y gana creditos\n\n"
            "Selecciona una opcion:"
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

    class Success:
        OPERATION_COMPLETED = (
            "✅ **Operacion Completada**\n\n"
            "Tu solicitud ha sido procesada exitosamente."
        )
