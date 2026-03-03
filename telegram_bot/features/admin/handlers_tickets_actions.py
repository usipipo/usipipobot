"""
Handlers para acciones de tickets en panel administrativo.

Author: uSipipo Team
Version: 1.0.0 - Refactor from handlers_tickets.py
"""

import uuid

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from telegram_bot.common.decorators import admin_required
from telegram_bot.features.tickets.keyboards_tickets import TicketKeyboards
from utils.spinner import SpinnerManager, admin_spinner_callback
from utils.logger import logger

ADMIN_MENU = 0
VIEWING_TICKETS = 9


class TicketsActionsMixin:
    """Mixin para acciones de tickets en panel admin."""

    def _format_ticket_messages(self, messages) -> str:
        """Formatea mensajes de ticket para mostrar."""
        if not messages:
            return "_Sin mensajes_\n"

        lines = []
        for msg in messages:
            prefix = "👨‍💼 *Admin:*" if msg.is_from_admin else "👤 *Usuario:*"
            timestamp = msg.created_at.strftime("%d/%m %H:%M")
            lines.append(
                f"{prefix}\n"
                f"```\n{msg.message[:200]}\n```\n"
                f"🕐 {timestamp}\n"
            )
        return "\n".join(lines)

    @admin_required
    @admin_spinner_callback
    async def view_admin_ticket(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        spinner_message_id: int | None = None,
    ):
        """Muestra detalle de un ticket específico."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return VIEWING_TICKETS

        try:
            ticket_id_str = query.data.replace("admin_ticket_", "")
            ticket_id = uuid.UUID(ticket_id_str)
        except (ValueError, AttributeError):
            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text="❌ *Ticket no encontrado*",
                reply_markup=TicketKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        try:
            from application.services.ticket_service import TicketService
            ticket_service = TicketService(self.service.ticket_repo)
            result = await ticket_service.get_ticket_with_messages(ticket_id)

            if not result:
                await SpinnerManager.replace_spinner_with_message(
                    update,
                    context,
                    spinner_message_id,
                    text="❌ *Ticket no encontrado*",
                    reply_markup=TicketKeyboards.back_to_menu(),
                    parse_mode="Markdown",
                )
                return VIEWING_TICKETS

            ticket, messages = result

            messages_text = self._format_ticket_messages(messages)

            header = (
                f"🎫 *Ticket {ticket.ticket_number}*\n\n"
                f"👤 *Usuario:* `{ticket.user_id}`\n"
                f"📂 *Categoría:* {ticket.category.value}\n"
                f"🔘 *Prioridad:* {ticket.priority.value}\n"
                f"📊 *Estado:* {ticket.status.value}\n"
                f"📅 *Creado:* {ticket.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
            )

            message = header + messages_text

            await SpinnerManager.replace_spinner_with_message(
                update,
                context,
                spinner_message_id,
                text=message[:3500],
                reply_markup=TicketKeyboards.admin_ticket_actions(
                    ticket_id=int(ticket.id.int % 100000000),
                    status=ticket.status,
                ),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        except Exception as e:
            await self._handle_error(update, context, e, "view_admin_ticket")
            return VIEWING_TICKETS

    @admin_required
    async def start_ticket_reply(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Inicia respuesta a un ticket."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return VIEWING_TICKETS

        try:
            ticket_id_simple = int(query.data.replace("admin_ticket_resp_", ""))
        except (ValueError, AttributeError):
            await self._safe_edit_message(
                query,
                context,
                text="❌ *Error: ID de ticket inválido*",
                reply_markup=TicketKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        if context.user_data is None:
            context.user_data = {}
        context.user_data["admin_replying_ticket_id"] = ticket_id_simple

        await self._safe_edit_message(
            query,
            context,
            text=(
                "💬 *Responder al Ticket*\n\n"
                "Escribe tu mensaje de respuesta:\n"
                "_Mínimo 5 caracteres, máximo 1000_"
            ),
            reply_markup=TicketKeyboards.cancel_action(),
            parse_mode="Markdown",
        )
        return VIEWING_TICKETS

    @admin_required
    async def send_ticket_reply(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Envía respuesta del admin al ticket."""
        if not update.effective_user or not update.message:
            return VIEWING_TICKETS

        admin_id = update.effective_user.id
        message_text = update.message.text

        logger.info(f"Admin {admin_id} sending ticket reply")

        if not context.user_data:
            await update.message.reply_text(
                "❌ *Error: Sesión expirada*",
                reply_markup=TicketKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        ticket_id_simple = context.user_data.get("admin_replying_ticket_id")
        logger.info(f"Replying to ticket {ticket_id_simple}")
        if not ticket_id_simple:
            await update.message.reply_text(
                "❌ *Error: No se encontró el ticket*",
                reply_markup=TicketKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        if not message_text or len(message_text) < 5:
            await update.message.reply_text(
                "⚠️ *Mensaje muy corto*\nEscribe al menos 5 caracteres.",
                reply_markup=TicketKeyboards.cancel_action(),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        if len(message_text) > 1000:
            await update.message.reply_text(
                "⚠️ *Mensaje muy largo*\nMáximo 1000 caracteres.",
                reply_markup=TicketKeyboards.cancel_action(),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        await update.message.reply_text(
            "✅ *Respuesta enviada*\n\n"
            "Tu respuesta ha sido registrada. "
            "El usuario será notificado.",
            reply_markup=TicketKeyboards.back_to_menu(),
            parse_mode="Markdown",
        )

        context.user_data.pop("admin_replying_ticket_id", None)
        return VIEWING_TICKETS

    @admin_required
    async def close_admin_ticket(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Cierra un ticket desde el panel admin."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return VIEWING_TICKETS

        try:
            ticket_id_simple = int(query.data.replace("admin_ticket_close_", ""))
            logger.info(f"Closing ticket {ticket_id_simple}")
        except (ValueError, AttributeError):
            await self._safe_edit_message(
                query,
                context,
                text="❌ *Error: ID de ticket inválido*",
                reply_markup=TicketKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        await self._safe_edit_message(
            query,
            context,
            text=(
                "🔒 *Ticket Cerrado*\n\n"
                "El ticket ha sido cerrado exitosamente."
            ),
            reply_markup=TicketKeyboards.back_to_menu(),
            parse_mode="Markdown",
        )
        return VIEWING_TICKETS

    @admin_required
    async def reopen_admin_ticket(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Reabre un ticket cerrado."""
        query = update.callback_query
        await self._safe_answer_query(query)

        if query is None or query.data is None:
            return VIEWING_TICKETS

        try:
            ticket_id_simple = int(query.data.replace("admin_ticket_reopen_", ""))
            logger.info(f"Reopening ticket {ticket_id_simple}")
        except (ValueError, AttributeError):
            await self._safe_edit_message(
                query,
                context,
                text="❌ *Error: ID de ticket inválido*",
                reply_markup=TicketKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )
            return VIEWING_TICKETS

        await self._safe_edit_message(
            query,
            context,
            text=(
                "🔄 *Ticket Reabierto*\n\n"
                "El ticket ha sido reabierto exitosamente."
            ),
            reply_markup=TicketKeyboards.back_to_menu(),
            parse_mode="Markdown",
        )
        return VIEWING_TICKETS
