"""
Handlers para creación de tickets de soporte.

Author: uSipipo Team
Version: 2.0.0 - Create Ticket Handlers
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import logger

from .handlers_user_tickets import (
    TICKET_CONFIRMING,
    TICKET_MENU,
    TICKET_SELECTING_CATEGORY,
    TICKET_WRITING_MESSAGE,
    UserTicketHandler,
)
from .keyboards_tickets import TicketKeyboards
from .messages_tickets import CATEGORY_NAME, PRIORITY_NAME, TicketMessages


class CreateTicketMixin:
    """Mixin para operaciones de creación de tickets."""

    async def start_create(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Inicia el proceso de creación de ticket."""
        if not update.effective_user:
            return -1

        user_id = update.effective_user.id
        query = update.callback_query

        logger.info(f"🎫 User {user_id} started ticket creation")

        if self._is_rate_limited(user_id):
            logger.warning(f"⚠️ User {user_id} rate limited for ticket creation")

            if query:
                await self._safe_answer_query(query)
                await self._safe_edit_message(
                    query,
                    context,
                    text=TicketMessages.Create.RATE_LIMIT,
                    reply_markup=TicketKeyboards.back_to_menu(),
                )
            return TICKET_MENU

        try:
            message = TicketMessages.Create.SELECT_CATEGORY
            keyboard = TicketKeyboards.category_selection()

            if query:
                await self._safe_answer_query(query)
                await self._safe_edit_message(query, context, text=message, reply_markup=keyboard)
            elif update.message:
                await update.message.reply_text(
                    text=message, reply_markup=keyboard, parse_mode="Markdown"
                )

            return TICKET_SELECTING_CATEGORY

        except Exception as e:
            logger.error(f"Error starting ticket creation: {e}")
            await self._handle_error(update, context, e, "start_create")
            return TICKET_MENU

    async def select_category(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Procesa la selección de categoría del ticket."""
        if not update.effective_user or not update.callback_query:
            return -1

        user_id = update.effective_user.id
        query = update.callback_query

        await self._safe_answer_query(query)

        callback_data = query.data
        category = self._map_callback_to_category(callback_data)

        if not category:
            logger.warning(f"⚠️ Invalid category callback: {callback_data}")
            return TICKET_MENU

        logger.info(f"🎫 User {user_id} selected category: {category.value}")

        if context.user_data is None:
            context.user_data = {}
        context.user_data["ticket_category"] = category
        context.user_data["ticket_category_name"] = CATEGORY_NAME.get(
            category.value, category.value
        )

        try:
            message = TicketMessages.Create.ENTER_DESCRIPTION.format(
                category=context.user_data["ticket_category_name"]
            )
            keyboard = TicketKeyboards.cancel_action()

            await self._safe_edit_message(query, context, text=message, reply_markup=keyboard)

            return TICKET_WRITING_MESSAGE

        except Exception as e:
            logger.error(f"Error selecting category: {e}")
            await self._handle_error(update, context, e, "select_category")
            return TICKET_MENU

    async def receive_message(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Recibe y valida el mensaje/descripción del ticket."""
        if not update.effective_user or not update.message:
            return -1

        user_id = update.effective_user.id
        message_text = update.message.text

        if not message_text or len(message_text) < 10:
            await update.message.reply_text(
                "⚠️ El mensaje es muy corto. Por favor describe tu problema con al menos 10 caracteres.",
                reply_markup=TicketKeyboards.cancel_action(),
            )
            return TICKET_WRITING_MESSAGE

        if len(message_text) > 1000:
            await update.message.reply_text(
                "⚠️ El mensaje es muy largo (máximo 1000 caracteres). Por favor resume tu problema.",
                reply_markup=TicketKeyboards.cancel_action(),
            )
            return TICKET_WRITING_MESSAGE

        logger.info(f"🎫 User {user_id} entered ticket message")

        if context.user_data is None:
            context.user_data = {}
        context.user_data["ticket_message"] = message_text

        category_name = context.user_data.get("ticket_category_name", "Otro")

        try:
            confirm_message = TicketMessages.Create.CONFIRM.format(
                category=category_name,
                description=(
                    message_text[:200] + "..." if len(message_text) > 200 else message_text
                ),
            )
            keyboard = TicketKeyboards.confirm_ticket()

            await update.message.reply_text(
                text=confirm_message,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

            return TICKET_CONFIRMING

        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            await self._handle_error(update, context, e, "receive_message")
            return TICKET_MENU

    async def confirm_create(
        self: UserTicketHandler, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Confirma y crea el ticket."""
        if not update.effective_user or not update.callback_query:
            return -1

        user_id = update.effective_user.id
        username = update.effective_user.username
        query = update.callback_query

        await self._safe_answer_query(query)

        if not context.user_data:
            logger.error(f"❌ No user data in context for user {user_id}")
            await self._safe_edit_message(
                query,
                context,
                text="❌ Error: Datos de sesión perdidos. Intenta nuevamente.",
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        category = context.user_data.get("ticket_category")
        message_text = context.user_data.get("ticket_message")

        if not category or not message_text:
            logger.error(f"❌ Missing data for ticket creation by user {user_id}")
            await self._safe_edit_message(
                query,
                context,
                text="❌ Error: Datos incompletos. Intenta nuevamente.",
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU

        try:
            subject = self._map_category_to_subject(category)

            ticket = await self.ticket_service.create_ticket(
                user_id=user_id,
                category=category,
                subject=subject,
                message=message_text,
            )

            self._record_ticket_created(user_id)

            logger.info(f"✅ Ticket {ticket.ticket_number} created by user {user_id}")

            await self.notification_service.notify_admin_new_ticket(ticket, username)

            context.user_data.pop("ticket_category", None)
            context.user_data.pop("ticket_category_name", None)
            context.user_data.pop("ticket_message", None)

            success_message = TicketMessages.Create.SUCCESS.format(
                ticket_number=ticket.ticket_number,
                category=CATEGORY_NAME.get(category.value, category.value),
                priority=PRIORITY_NAME.get(ticket.priority.value, ticket.priority.value.upper()),
            )

            await self._safe_edit_message(
                query,
                context,
                text=success_message,
                reply_markup=TicketKeyboards.back_to_menu(),
            )

            return TICKET_MENU

        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            await self._safe_edit_message(
                query,
                context,
                text=TicketMessages.Error.GENERIC,
                reply_markup=TicketKeyboards.back_to_menu(),
            )
            return TICKET_MENU
