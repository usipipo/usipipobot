"""
Mensajes del sistema de tickets de soporte.

Author: uSipipo Team
Version: 1.0.0 - Support Ticket System
"""

from utils.message_separators import (
    MessageSeparatorBuilder,
    TELEGRAM_MOBILE_WIDTH,
)

# Separadores
_SEP_HEADER = (
    MessageSeparatorBuilder()
    .compact().style("double").length(TELEGRAM_MOBILE_WIDTH).build()
)
_SEP_DIVIDER = (
    MessageSeparatorBuilder()
    .compact().style("simple").length(TELEGRAM_MOBILE_WIDTH).build()
)


class TicketMessages:
    """Mensajes para el sistema de tickets."""

    class Menu:
        """Mensajes del menú principal."""
        
        _HEADER = (
            f"{_SEP_HEADER}\n"
            "🎫 *SOPORTE Y AYUDA*\n"
            f"{_SEP_HEADER}\n"
        )
        
        _OPTIONS = (
            "\n"
            "*¿Necesitas ayuda?*\n"
            "\n"
            "├─ 🆕 *Crear Ticket*\n"
            "│  └─ Nueva solicitud de soporte\n"
            "│\n"
            "├─ 📋 *Mis Tickets*\n"
            "│  └─ Ver estado de tus tickets\n"
            "│\n"
            "└─ ❓ *FAQ*\n"
            "   └─ Preguntas frecuentes\n"
        )
        
        _FOOTER = (
            f"\n{_SEP_DIVIDER}\n"
            "👇 *Selecciona una opción:*"
        )
        
        MAIN = _HEADER + _OPTIONS + _FOOTER
    
    class Create:
        """Mensajes para crear ticket."""
        
        SELECT_CATEGORY = (
            f"{_SEP_HEADER}\n"
            "🆕 *CREAR NUEVO TICKET*\n"
            f"{_SEP_HEADER}\n\n"
            "*Selecciona la categoría*\n"
            "que mejor describe tu problema:\n\n"
            "🔴 *VPN-Fallas* - Problemas de conexión\n"
            "💰 *Pagos* - Pagos y facturación\n"
            "👤 *Cuenta* - Tu cuenta y perfil\n"
            "❓ *Otro* - Consultas generales\n\n"
            "👇 *Toca una opción:*"
        )
        
        ENTER_DESCRIPTION = (
            f"{_SEP_HEADER}\n"
            "📝 *DESCRIPCIÓN DEL PROBLEMA*\n"
            f"{_SEP_HEADER}\n\n"
            "*Categoría:* {category}\n\n"
            "Por favor describe tu problema:\n"
            "• Qué intentabas hacer\n"
            "• Qué error apareció\n"
            "• Cuándo empezó\n\n"
            "_Escribe tu mensaje ahora:_"
        )
        
        CONFIRM = (
            f"{_SEP_HEADER}\n"
            "✅ *CONFIRMAR TICKET*\n"
            f"{_SEP_HEADER}\n\n"
            "*Categoría:* {category}\n"
            "*Descripción:*\n"
            "```\n{description}\n```\n"
            f"{_SEP_DIVIDER}\n\n"
            "¿Enviar este ticket?"
        )
        
        SUCCESS = (
            f"{_SEP_HEADER}\n"
            "✅ *TICKET CREADO*\n"
            f"{_SEP_HEADER}\n\n"
            "📋 *Número:* `{ticket_number}`\n"
            "📂 *Categoría:* {category}\n"
            "🟠 *Prioridad:* {priority}\n"
            "📊 *Estado:* ABIERTO\n\n"
            f"{_SEP_DIVIDER}\n\n"
            "✨ *Nuestro equipo responderá*\n"
            "*en menos de 24 horas.*\n\n"
            "📬 Te notificaremos cuando\n"
            "haya una respuesta."
        )
        
        RATE_LIMIT = (
            "⚠️ *LÍMITE DE TICKETS*\n\n"
            "Has alcanzado el límite de 3 tickets\n"
            "en las últimas 24 horas.\n\n"
            "Por favor espera antes de crear\n"
            "un nuevo ticket."
        )

    class List:
        """Mensajes para listar tickets."""
        
        _HEADER = (
            f"{_SEP_HEADER}\n"
            "📋 *MIS TICKETS*\n"
            f"{_SEP_HEADER}\n\n"
        )
        
        _EMPTY = (
            "*No tienes tickets activos*\n\n"
            "¿Necesitas ayuda?\n"
            "Crea un ticket desde el menú."
        )
        
        @classmethod
        def with_tickets(cls, tickets_text: str) -> str:
            return cls._HEADER + tickets_text + f"\n{_SEP_DIVIDER}\n👇 *Toca un ticket para ver:*"
    
    class Detail:
        """Mensajes de detalle de ticket."""
        
        HEADER = (
            f"{_SEP_HEADER}\n"
            "🎫 *DETALLE DEL TICKET*\n"
            f"{_SEP_HEADER}\n\n"
        )
        
        INFO = (
            "📋 *{ticket_number}*\n"
            "📂 *Categoría:* {category}\n"
            "🔘 *Prioridad:* {priority}\n"
            "📊 *Estado:* {status}\n"
            "📅 *Creado:* {created_at}\n\n"
        )
        
        MESSAGE_USER = (
            "👤 *Tú:*\n"
            "```\n{message}\n```\n"
            "🕐 {timestamp}\n\n"
        )
        
        MESSAGE_ADMIN = (
            "👨‍💼 *Soporte:*\n"
            "```\n{message}\n```\n"
            "🕐 {timestamp}\n\n"
        )

    class Admin:
        """Mensajes para administradores."""
        
        _HEADER = (
            f"{_SEP_HEADER}\n"
            "🎫 *GESTIÓN DE TICKETS*\n"
            f"{_SEP_HEADER}\n\n"
        )
        
        @classmethod
        def menu(cls, open_count: int) -> str:
            badge = f" ({open_count})" if open_count > 0 else ""
            return (
                cls._HEADER +
                f"💎 *Pendientes:* {open_count}\n\n"
                f"{_SEP_DIVIDER}\n\n"
                "├─ 📥 *Tickets Abiertos{badge}*\n"
                "│  └─ Ver tickets pendientes\n"
                "│\n"
                "├─ 📋 *Todos los Tickets*\n"
                "│  └─ Historial completo\n"
                "│\n"
                "└─ 🔍 *Buscar por Categoría*\n"
                "   └─ Filtrar tickets\n\n"
                f"{_SEP_DIVIDER}\n"
                "👇 *Selecciona una opción:*"
            )
        
        TICKET_ITEM = (
            "{priority_emoji} *{priority}* | *{ticket_number}* | {category_emoji}\n"
            "├─ 👤 User: {username}\n"
            "├─ 📝 {subject_preview}\n"
            "└─ ⏱️ {time_ago}\n\n"
        )

    class Error:
        """Mensajes de error."""
        
        TICKET_NOT_FOUND = (
            "❌ *Ticket no encontrado*\n\n"
            "El ticket que buscas no existe "
            "o no tienes permiso para verlo."
        )
        
        GENERIC = (
            "❌ *Error*\n\n"
            "Ocurrió un error procesando tu solicitud.\n"
            "Por favor intenta nuevamente."
        )


# Category and priority display mappings
CATEGORY_EMOJI = {
    "vpn_fail": "🔴",
    "payment": "💰",
    "account": "👤",
    "other": "❓"
}

CATEGORY_NAME = {
    "vpn_fail": "VPN-Fallas",
    "payment": "Pagos",
    "account": "Cuenta",
    "other": "Otro"
}

PRIORITY_EMOJI = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢"
}

PRIORITY_NAME = {
    "high": "ALTA",
    "medium": "MEDIA",
    "low": "BAJA"
}

STATUS_EMOJI = {
    "open": "📂",
    "responded": "↩️",
    "resolved": "✅",
    "closed": "🔒"
}

STATUS_NAME = {
    "open": "ABIERTO",
    "responded": "RESPONDIDO",
    "resolved": "RESUELTO",
    "closed": "CERRADO"
}
