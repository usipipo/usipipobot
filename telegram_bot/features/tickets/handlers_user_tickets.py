"""
Handlers base para tickets de soporte - Interfaz de usuario.

Author: uSipipo Team
Version: 2.0.0 - Refactored Base Handler
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from uuid import UUID

from telegram import Update
from telegram.ext import ContextTypes

from application.services.ticket_service import TicketService
from application.services.ticket_notification_service import TicketNotificationService
from domain.entities.ticket import Ticket, TicketCategory
from telegram_bot.common.base_handler import BaseHandler
from telegram_bot.common.keyboards import CommonKeyboards
from telegram_bot.common.messages import CommonMessages
from utils.logger import logger

from .keyboards_tickets import TicketKeyboards
from .messages_tickets import (
    TicketMessages,
    CATEGORY_EMOJI,
    CATEGORY_NAME,
    PRIORITY_EMOJI,
    PRIORITY_NAME,
    STATUS_EMOJI,
    STATUS_NAME,
)


# Conversation states
TICKET_MENU = 0
TICKET_SELECTING_CATEGORY = 1
TICKET_WRITING_MESSAGE = 2
TICKET_CONFIRMING = 3
TICKET_VIEWING = 4
TICKET_REPLYING = 5


class UserTicketHandler(BaseHandler):
    """Handler base para operaciones de tickets de usuarios."""

    def __init__(
        self,
        ticket_service: TicketService,
        notification_service: TicketNotificationService,
    ):
        super().__init__(ticket_service, "TicketService")
        self.ticket_service = ticket_service
        self.notification_service = notification_service
        self._ticket_creation_cache: dict = {}
        logger.info("🎫 UserTicketHandler inicializado")

    def _is_rate_limited(self, user_id: int) -> bool:
        """Verifica si el usuario ha alcanzado el límite de tickets."""
        cache_key = f"tickets_{user_id}"
        now = datetime.now(timezone.utc)

        if cache_key not in self._ticket_creation_cache:
            self._ticket_creation_cache[cache_key] = []

        user_tickets = self._ticket_creation_cache[cache_key]
        user_tickets = [
            ts for ts in user_tickets
            if now - ts < timedelta(hours=24)
        ]
        self._ticket_creation_cache[cache_key] = user_tickets

        return len(user_tickets) >= 3

    def _record_ticket_created(self, user_id: int) -> None:
        """Registra la creación de un ticket para rate limiting."""
        cache_key = f"tickets_{user_id}"
        now = datetime.now(timezone.utc)

        if cache_key not in self._ticket_creation_cache:
            self._ticket_creation_cache[cache_key] = []

        self._ticket_creation_cache[cache_key].append(now)

    def _get_back_keyboard(self):
        """Override para obtener teclado de tickets."""
        return TicketKeyboards.back_to_menu()

    def _map_callback_to_category(self, callback_data: str) -> Optional[TicketCategory]:
        """Mapea callback de categoría al enum correspondiente."""
        category_map = {
            "tickets_cat_vpn": TicketCategory.VPN_FAIL,
            "tickets_cat_payment": TicketCategory.PAYMENT,
            "tickets_cat_config": TicketCategory.ACCOUNT,
            "tickets_cat_bug": TicketCategory.VPN_FAIL,
            "tickets_cat_other": TicketCategory.OTHER,
        }
        return category_map.get(callback_data)

    def _map_category_to_subject(self, category: TicketCategory) -> str:
        """Genera asunto basado en categoría."""
        subject_map = {
            TicketCategory.VPN_FAIL: "Problema de conexión VPN",
            TicketCategory.PAYMENT: "Consulta sobre pago",
            TicketCategory.ACCOUNT: "Configuración de cuenta",
            TicketCategory.OTHER: "Otra consulta",
        }
        return subject_map.get(category, "Consulta de soporte")

    def _format_ticket_list(self, tickets: List[Ticket]) -> str:
        """Formatea lista de tickets para mostrar."""
        if not tickets:
            return "*No tienes tickets activos*\n\n"

        lines = []
        for ticket in tickets[:10]:
            status_emoji = STATUS_EMOJI.get(ticket.status.value, "⚪")
            category_emoji = CATEGORY_EMOJI.get(ticket.category.value, "🎫")
            lines.append(
                f"{status_emoji} *{ticket.ticket_number}* {category_emoji}\n"
                f"  ├─ {CATEGORY_NAME.get(ticket.category.value, ticket.category.value)}\n"
                f"  └─ Creado: {ticket.created_at.strftime('%d/%m/%y')}\n"
            )

        return "\n".join(lines)

    def _format_messages(self, messages: List[Any]) -> str:
        """Formatea mensajes del ticket."""
        from domain.entities.ticket_message import TicketMessage

        if not messages:
            return "_Sin mensajes_\n"

        lines = []
        for msg in messages:
            prefix = "👨‍💼 *Soporte:*" if msg.is_from_admin else "👤 *Tú:*"
            timestamp = msg.created_at.strftime("%d/%m %H:%M")
            lines.append(
                f"{prefix}\n"
                f"```\n{msg.message[:200]}\n```\n"
                f"🕐 {timestamp}\n"
            )

        return "\n".join(lines)

    async def show_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Muestra el menú principal de soporte."""
        if not update.effective_user:
            return -1

        user_id = update.effective_user.id
        query = update.callback_query

        logger.info(f"🎫 User {user_id} opened ticket menu")

        try:
            message = TicketMessages.Menu.MAIN
            keyboard = TicketKeyboards.main_menu()

            if query:
                await self._safe_answer_query(query)
                await self._safe_edit_message(
                    query, context, text=message, reply_markup=keyboard
                )
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

            return TICKET_MENU

        except Exception as e:
            logger.error(f"Error showing ticket menu: {e}")
            await self._handle_error(update, context, e, "show_menu")
            return -1

    async def cancel(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Cancela la operación actual y vuelve al menú."""
        if update.callback_query:
            await self._safe_answer_query(update.callback_query)

        if context.user_data:
            context.user_data.pop("ticket_category", None)
            context.user_data.pop("ticket_category_name", None)
            context.user_data.pop("ticket_message", None)
            context.user_data.pop("replying_ticket_id", None)

        logger.info("🎫 Ticket operation cancelled")
        return await self.show_menu(update, context)
