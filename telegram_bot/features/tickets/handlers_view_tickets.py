"""
Handlers para visualización de tickets de soporte.

Author: uSipipo Team
Version: 2.0.0 - View Tickets Handlers
"""

from uuid import UUID

from telegram import Update
from telegram.ext import ContextTypes

from domain.entities.ticket import TicketStatus
from utils.logger import logger

from .handlers_user_tickets import UserTicketHandler, TICKET_MENU, TICKET_VIEWING
from .keyboards_tickets import TicketKeyboards
from .messages_tickets import TicketMessages, CATEGORY_NAME, PRIORITY_NAME, STATUS_NAME


class ViewTicketsMixin:
    """Mixin para operaciones de visualización de tickets."""

    async def show_list(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Muestra la lista de tickets del usuario."""
        if not update.effective_user:
            return -1

        user_id = update.effective_user.id
        query = update.callback_query

        logger.info(f"🎫 User {user_id} viewing ticket list")

        try:
            tickets = await self.ticket_service.get_user_tickets(user_id)

            if not tickets:
                message = TicketMessages.List._HEADER + TicketMessages.List._EMPTY
                keyboard = TicketKeyboards.back_to_menu()
            else:
                tickets_text = self._format_ticket_list(tickets)
                message = TicketMessages.List.with_tickets(tickets_text)
                keyboard = TicketKeyboards.tickets_list(tickets)

            if query:
                await self._safe_answer_query(query)
                await self._safe_edit_message(
                    query, context, text=message, reply_markup=keyboard
                )
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

            return TICKET_VIEWING

        except Exception as e:
            logger.error(f"Error showing ticket list: {e}")
            await self._handle_error(update, context, e, "show_list")
            return TICKET_MENU

    async def view_ticket(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Muestra el detalle de un ticket específico."""
        if not update.effective_user or not update.callback_query:
            return -1

        user_id = update.effective_user.id
        query = update.callback_query

        await self._safe_answer_query(query)

        callback_data = query.data
        try:
            ticket_id_str = callback_data.replace("tickets_view_", "")
            ticket_id = UUID(ticket_id_str)
        except (ValueError, AttributeError):
            logger.error(f"❌ Invalid ticket ID in callback: {callback_data}")
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        logger.info(f"🎫 User {user_id} viewing ticket {ticket_id}")

        try:
            result = await self.ticket_service.get_ticket_with_messages(ticket_id)

            if not result:
                await self._safe_edit_message(
                    query,
                    context,
                    text=TicketMessages.Error.TICKET_NOT_FOUND,
                    reply_markup=TicketKeyboards.back_to_menu(),
                )
                return TICKET_MENU

            ticket, messages = result

            if ticket.user_id != user_id:
                logger.warning(f"⚠️ User {user_id} tried to access ticket {ticket_id} not owned by them")
                await self._safe_edit_message(
                    query,
                    context,
                    text=TicketMessages.Error.TICKET_NOT_FOUND,
                    reply_markup=TicketKeyboards.back_to_menu(),
                )
                return TICKET_MENU

            header = TicketMessages.Detail.HEADER
            info = TicketMessages.Detail.INFO.format(
                ticket_number=ticket.ticket_number,
                category=CATEGORY_NAME.get(ticket.category.value, ticket.category.value),
                priority=PRIORITY_NAME.get(ticket.priority.value, ticket.priority.value),
                status=STATUS_NAME.get(ticket.status.value, ticket.status.value.upper()),
                created_at=ticket.created_at.strftime("%d/%m/%Y %H:%M"),
            )
            messages_text = self._format_messages(messages)

            message = header + info + messages_text
            keyboard = TicketKeyboards.ticket_detail(
                ticket_id=int(ticket.id.int % 100000000),
                status=ticket.status,
                can_reply=ticket.status != TicketStatus.CLOSED,
                can_close=ticket.status != TicketStatus.CLOSED,
            )

            await self._safe_edit_message(
                query, context, text=message, reply_markup=keyboard
            )

            return TICKET_VIEWING

        except Exception as e:
            logger.error(f"Error viewing ticket: {e}")
            await self._handle_error(update, context, e, "view_ticket")
            return TICKET_MENU
