from telegram import Bot
from domain.entities.ticket import Ticket, TicketStatus
from utils.logger import logger


class TicketNotificationService:
    """Servicio para notificaciones de tickets."""

    def __init__(self, bot: Bot, admin_id: int):
        self.bot = bot
        self.admin_id = admin_id

    async def notify_admin_new_ticket(self, ticket: Ticket, username: str = None) -> bool:
        """Notifica al admin de un nuevo ticket."""
        try:
            category_emoji = {
                "vpn_fail": "🔴",
                "payment": "💰",
                "account": "👤",
                "other": "❓"
            }.get(ticket.category.value, "🎫")
            
            priority_emoji = {
                "high": "🔴 ALTA",
                "medium": "🟡 MEDIA",
                "low": "🟢 BAJA"
            }.get(ticket.priority.value, "⚪")
            
            username_text = f"(@{username})" if username else ""
            
            message = (
                f"🆕 *NUEVO TICKET DE SOPORTE*\n\n"
                f"📋 *Número:* `{ticket.ticket_number}`\n"
                f"{category_emoji} *Categoría:* {ticket.category.value.upper()}\n"
                f"{priority_emoji} *Prioridad:* {ticket.priority.value.upper()}\n"
                f"👤 *Usuario:* {ticket.user_id} {username_text}\n"
                f"📝 *Asunto:* {ticket.subject}\n\n"
                f"Usa `/admin` → Gestionar Tickets para responder."
            )
            
            await self.bot.send_message(
                chat_id=self.admin_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"Admin notified of new ticket: {ticket.ticket_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
            return False

    async def notify_user_response(
        self, 
        user_id: int, 
        ticket: Ticket, 
        response_text: str
    ) -> bool:
        """Notifica al usuario de una respuesta del admin."""
        try:
            # Truncate long responses
            preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
            
            message = (
                f"📨 *NUEVA RESPUESTA A TU TICKET*\n\n"
                f"📋 *Ticket:* `{ticket.ticket_number}`\n"
                f"💬 *Mensaje:* {preview}\n\n"
                f"Usa el menú de Soporte para ver la conversación completa."
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"User {user_id} notified of response to {ticket.ticket_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            return False

    async def notify_ticket_resolved(self, user_id: int, ticket: Ticket) -> bool:
        """Notifica al usuario que su ticket fue resuelto."""
        try:
            message = (
                f"✅ *TICKET RESUELTO*\n\n"
                f"📋 *Ticket:* `{ticket.ticket_number}`\n"
                f"📝 *Asunto:* {ticket.subject}\n\n"
                f"Tu solicitud ha sido resuelta. Si necesitas más ayuda, "
                f"puedes crear un nuevo ticket desde el menú de Soporte."
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to notify user of resolution: {e}")
            return False
