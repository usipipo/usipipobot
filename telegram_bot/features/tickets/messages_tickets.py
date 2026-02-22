class TicketMessages:
    class User:
        CREATE_PROMPT = (
            "🎫 *Crear Ticket de Soporte*\n\n"
            "Escribe tu mensaje describiendo el problema:\n\n"
            "_Ejemplo: No puedo conectar mi VPN desde mi teléfono_"
        )

        CREATED = (
            "✅ *Ticket Creado*\n\n"
            "ID: \\#{ticket_id}\n"
            "Asunto: {subject}\n"
            "Estado: 🟡 Pendiente\n\n"
            "Te responderemos pronto\\."
        )

        MY_TICKETS_HEADER = "📋 *Mis Tickets*\n\n"

        NO_TICKETS = (
            "📋 *Mis Tickets*\n\n"
            "No tienes tickets abiertos\\.\n\n"
            "¿Necesitas ayuda? Crea uno nuevo\\."
        )

        TICKET_DETAIL = (
            "🎫 *Ticket \\#{ticket_id}*\n\n"
            "📝 *Asunto:* {subject}\n"
            "📊 *Estado:* {status}\n"
            "📅 *Creado:* {created_at}\n\n"
            "💬 *Mensaje:*\n{message}\n\n"
            "{response_section}"
        )

        RESPONSE_SECTION = (
            "✅ *Respuesta del soporte:*\n"
            "{response}\n\n"
            "_Respondido el {resolved_at}_"
        )

    class Admin:
        LIST_HEADER = "🔧 *Tickets Pendientes*\n\n"

        NO_PENDING = (
            "🔧 *Tickets Pendientes*\n\n"
            "No hay tickets pendientes\\."
        )

        TICKET_DETAIL = (
            "🎫 *Ticket \\#{ticket_id}*\n\n"
            "👤 *Usuario:* `{user_id}`\n"
            "📝 *Asunto:* {subject}\n"
            "📊 *Estado:* {status}\n"
            "📅 *Creado:* {created_at}\n\n"
            "💬 *Mensaje:*\n{message}\n\n"
            "{response_section}"
        )

        RESPOND_PROMPT = (
            "✍️ *Responder Ticket \\#{ticket_id}*\n\n"
            "Escribe tu respuesta para el usuario:"
        )

    class Error:
        NOT_FOUND = "❌ Ticket no encontrado\\."
        CREATE_FAILED = "❌ Error al crear el ticket\\. Intenta de nuevo\\."
        NOT_AUTHORIZED = "❌ No tienes permiso para esta acción\\."
