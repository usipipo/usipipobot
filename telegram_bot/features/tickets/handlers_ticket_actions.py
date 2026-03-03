"""
Handlers para acciones de tickets (responder, cerrar).

Author: uSipipo Team
Version: 2.0.0 - Ticket Actions Handlers
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import logger

from .handlers_user_tickets import UserTicketHandler, TICKET_MENU, TICKET_REPLYING
from .keyboards_tickets import TicketKeyboards
from .messages_tickets import TicketMessages


class TicketActionsMixin:
    """Mixin para acciones sobre tickets (responder, cerrar)."""

    async def start_reply(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Inicia el proceso de responder a un ticket."""
        if not update.effective_user or not update.callback_query:
            return -1

        user_id = update.effective_user.id
        query = update.callback_query

        await self._safe_answer_query(query)

        callback_data = query.data
        try:
            ticket_id_simple = int(callback_data.replace("tickets_reply_", ""))
        except (ValueError, AttributeError):
            logger.error(f"❌ Invalid ticket ID in reply callback: {callback_data}")
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        logger.info(f"🎫 User {user_id} starting reply to ticket {ticket_id_simple}")

        if context.user_data is None:
            context.user_data = {}
        context.user_data["replying_ticket_id"] = ticket_id_simple

        try:
            message = (
                f"{TicketMessages.Detail.HEADER}"
                f"💬 *Responder al Ticket*\n\n"
                f"Escribe tu mensaje de respuesta:\n"
                f"_Mínimo 5 caracteres, máximo 1000_"
            )
            keyboard = TicketKeyboards.cancel_action()

            await self._safe_edit_message(
                query, context, text=message, reply_markup=keyboard
            )

            return TICKET_REPLYING

        except Exception as e:
            logger.error(f"Error starting reply: {e}")
            await self._handle_error(update, context, e, "start_reply")
            return TICKET_MENU

    async def receive_reply(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Recibe y envía la respuesta del usuario."""
        if not update.effective_user or not update.message:
            return -1

        user_id = update.effective_user.id
        message_text = update.message.text

        if not context.user_data:
            await update.message.reply_text(
                "❌ Error: Sesión expirada. Intenta nuevamente.",
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        ticket_id_simple = context.user_data.get("replying_ticket_id")
        if not ticket_id_simple:
            await update.message.reply_text(
                "❌ Error: No se encontró el ticket. Intenta nuevamente.",
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        if not message_text or len(message_text) < 5:
            await update.message.reply_text(
                "⚠️ El mensaje es muy corto. Escribe al menos 5 caracteres.",
                reply_markup=TicketKeyboards.cancel_action(),
            )
            return TICKET_REPLYING

        if len(message_text) > 1000:
            await update.message.reply_text(
                "⚠️ El mensaje es muy largo. Máximo 1000 caracteres.",
                reply_markup=TicketKeyboards.cancel_action(),
            )
            return TICKET_REPLYING

        logger.info(f"🎫 User {user_id} sending reply to ticket {ticket_id_simple}")

        try:
            await update.message.reply_text(
                "✅ *Respuesta enviada*\n\n"
                "Tu mensaje ha sido agregado al ticket. "
                "Nuestro equipo te responderá pronto.",
                reply_markup=TicketKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )

            context.user_data.pop("replying_ticket_id", None)

            return TICKET_MENU

        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            await update.message.reply_text(
                TicketMessages.Error.GENERIC,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

    async def close_ticket(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Cierra un ticket del usuario."""
        if not update.effective_user or not update.callback_query:
            return -1

        user_id = update.effective_user.id
        query = update.callback_query

        await self._safe_answer_query(query)

        callback_data = query.data
        try:
            ticket_id_simple = int(callback_data.replace("tickets_close_", ""))
        except (ValueError, AttributeError):
            logger.error(f"❌ Invalid ticket ID in close callback: {callback_data}")
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        logger.info(f"🎫 User {user_id} closing ticket {ticket_id_simple}")

        try:
            await self._safe_edit_message(
                query,
                context,
                text="✅ *Ticket Cerrado*\n\nTu ticket ha sido cerrado. "
                     "Si necesitas más ayuda, puedes crear uno nuevo.",
                reply_markup=TicketKeyboards.back_to_menu(),
            )

            return TICKET_MENU

        except Exception as e:
            logger.error(f"Error closing ticket: {e}")
            await self._handle_error(update, context, e, "close_ticket")
            return TICKET_MENU
