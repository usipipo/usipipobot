"""
Handlers para acciones de tickets (responder, cerrar).

Author: uSipipo Team
Version: 2.0.0 - Ticket Actions Handlers
"""

from uuid import UUID

from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import logger

from .handlers_user_tickets import TICKET_MENU, TICKET_REPLYING, UserTicketHandler
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
        if not callback_data:
            logger.error("❌ No callback data in reply query")
            return TICKET_MENU

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

        # Obtener UUID desde el mapeo
        if not context.user_data:
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        ticket_id_map = context.user_data.get("ticket_id_map")
        if not ticket_id_map or str(ticket_id_simple) not in ticket_id_map:
            logger.error(f"❌ Ticket ID {ticket_id_simple} not found in mapping for reply")
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        try:
            ticket_id = UUID(ticket_id_map[str(ticket_id_simple)])
        except (ValueError, KeyError) as e:
            logger.error(f"❌ Error converting ticket ID for reply: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        logger.info(
            f"🎫 User {user_id} starting reply to ticket {ticket_id} (simple_id: {ticket_id_simple})"
        )

        if context.user_data is None:
            context.user_data = {}
        context.user_data["replying_ticket_id"] = ticket_id_simple
        context.user_data["replying_ticket_uuid"] = str(ticket_id)

        try:
            message = (
                f"{TicketMessages.Detail.HEADER}"
                f"💬 *Responder al Ticket*\n\n"
                f"Escribe tu mensaje de respuesta:\n"
                f"_Mínimo 5 caracteres, máximo 1000_"
            )
            keyboard = TicketKeyboards.cancel_action()

            await self._safe_edit_message(query, context, text=message, reply_markup=keyboard)

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
        ticket_uuid_str = context.user_data.get("replying_ticket_uuid")

        if not ticket_id_simple or not ticket_uuid_str:
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

        logger.info(f"🎫 User {user_id} sending reply to ticket {ticket_uuid_str}")

        try:
            # Usar el UUID real para la operación en DB
            ticket_id = UUID(ticket_uuid_str)

            # Llamar a service para guardar respuesta real
            result = await self.ticket_service.add_user_message(ticket_id, user_id, message_text)

            if not result:
                await update.message.reply_text(
                    TicketMessages.Error.TICKET_NOT_FOUND,
                    reply_markup=TicketKeyboards.back_to_menu(),
                )
                return TICKET_MENU

            await update.message.reply_text(
                "✅ *Respuesta enviada*\n\n"
                "Tu mensaje ha sido agregado al ticket. "
                "Nuestro equipo te responderá pronto.",
                reply_markup=TicketKeyboards.back_to_menu(),
                parse_mode="Markdown",
            )

            context.user_data.pop("replying_ticket_id", None)
            context.user_data.pop("replying_ticket_uuid", None)

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
        if not callback_data:
            logger.error("❌ No callback data in close query")
            return TICKET_MENU

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

        # Obtener UUID desde el mapeo
        if not context.user_data:
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        ticket_id_map = context.user_data.get("ticket_id_map")
        if not ticket_id_map or str(ticket_id_simple) not in ticket_id_map:
            logger.error(f"❌ Ticket ID {ticket_id_simple} not found in mapping for close")
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        try:
            ticket_id = UUID(ticket_id_map[str(ticket_id_simple)])
        except (ValueError, KeyError) as e:
            logger.error(f"❌ Error converting ticket ID for close: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.TICKET_NOT_FOUND,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        logger.info(f"🎫 User {user_id} closing ticket {ticket_id} (simple_id: {ticket_id_simple})")

        try:
            # Usar UUID real para cerrar ticket en DB
            result = await self.ticket_service.close_ticket(ticket_id, user_id)

            if not result:
                await self._safe_edit_message(
                    query,
                    context,
                    text=TicketMessages.Error.TICKET_NOT_FOUND,
                    reply_markup=TicketKeyboards.back_to_menu(),
                )
                return TICKET_MENU

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
