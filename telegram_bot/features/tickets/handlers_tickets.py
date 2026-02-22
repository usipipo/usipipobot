"""
Handlers para el sistema de tickets de soporte.

Author: uSipipo Team
Version: 1.0.0
"""

import uuid
from typing import Optional

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from application.services.ticket_service import TicketService
from config import settings
from telegram_bot.keyboards import MainMenuKeyboard
from utils.logger import logger

from .keyboards_tickets import TicketKeyboards
from .messages_tickets import TicketMessages


class TicketHandler:
    def __init__(self, ticket_service: TicketService):
        self.ticket_service = ticket_service
        logger.info("🎫 TicketHandler inicializado")

    async def create_ticket_prompt(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            text=TicketMessages.User.CREATE_PROMPT,
            reply_markup=TicketKeyboards.back_to_support(),
            parse_mode="Markdown",
        )
        _context.user_data["awaiting_ticket"] = True

    async def handle_ticket_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        if not context.user_data.get("awaiting_ticket"):
            return

        context.user_data["awaiting_ticket"] = False
        user_id = update.effective_user.id
        message_text = update.message.text

        try:
            subject = message_text[:50] + ("..." if len(message_text) > 50 else "")
            
            ticket = await self.ticket_service.create_ticket(
                user_id=user_id,
                subject=subject,
                message=message_text,
                current_user_id=user_id,
            )

            await update.message.reply_text(
                text=TicketMessages.User.CREATED.format(
                    ticket_id=str(ticket.id)[:8],
                    subject=subject,
                ),
                reply_markup=MainMenuKeyboard.main_menu(),
                parse_mode="MarkdownV2",
            )

            logger.info(f"🎫 Ticket {ticket.id} created by user {user_id}")

        except Exception as e:
            logger.error(f"❌ Error creating ticket: {e}")
            await update.message.reply_text(
                text=TicketMessages.Error.CREATE_FAILED,
                parse_mode="MarkdownV2",
            )

    async def list_my_tickets(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        try:
            tickets = await self.ticket_service.get_user_tickets(user_id, user_id)

            if not tickets:
                await query.edit_message_text(
                    text=TicketMessages.User.NO_TICKETS,
                    reply_markup=TicketKeyboards.back_to_support(),
                    parse_mode="MarkdownV2",
                )
                return

            text = TicketMessages.User.MY_TICKETS_HEADER
            keyboard = []

            for ticket in tickets[:5]:
                status_emoji = ticket.status_emoji
                subject = ticket.subject[:25]
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_emoji} {subject}",
                        callback_data=f"view_ticket_{ticket.id}"
                    )
                ])

            keyboard.append([
                InlineKeyboardButton("🔙 Volver", callback_data="help_support")
            ])

            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error listing tickets: {e}")

    async def view_ticket(self, update: Update, _context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        ticket_id = uuid.UUID(query.data.split("_")[-1])

        try:
            ticket = await self.ticket_service.get_ticket(ticket_id, user_id)

            if not ticket:
                await query.edit_message_text(
                    text=TicketMessages.Error.NOT_FOUND,
                    parse_mode="MarkdownV2",
                )
                return

            response_section = ""
            if ticket.response:
                resolved_at = ticket.resolved_at.strftime("%Y-%m-%d %H:%M") if ticket.resolved_at else "N/A"
                response_section = TicketMessages.User.RESPONSE_SECTION.format(
                    response=ticket.response,
                    resolved_at=resolved_at,
                )

            text = TicketMessages.User.TICKET_DETAIL.format(
                ticket_id=str(ticket.id)[:8],
                subject=ticket.subject,
                status=f"{ticket.status_emoji} {ticket.status.value}",
                created_at=ticket.created_at.strftime("%Y-%m-%d %H:%M"),
                message=ticket.message,
                response_section=response_section,
            )

            await query.edit_message_text(
                text=text,
                reply_markup=TicketKeyboards.user_ticket_actions(ticket.id),
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"❌ Error viewing ticket: {e}")

    async def admin_list_tickets(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()

        admin_id = update.effective_user.id

        if str(admin_id) != str(settings.ADMIN_ID):
            await query.edit_message_text(
                text=TicketMessages.Error.NOT_AUTHORIZED,
                parse_mode="MarkdownV2",
            )
            return

        try:
            tickets = await self.ticket_service.get_all_open_tickets(admin_id)

            if not tickets:
                await query.edit_message_text(
                    text=TicketMessages.Admin.NO_PENDING,
                    parse_mode="MarkdownV2",
                )
                return

            text = TicketMessages.Admin.LIST_HEADER
            keyboard = []

            for ticket in tickets[:10]:
                status_emoji = ticket.status_emoji
                subject = ticket.subject[:25]
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status_emoji} [{ticket.user_id}] {subject}",
                        callback_data=f"admin_view_ticket_{ticket.id}"
                    )
                ])

            keyboard.append([
                InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")
            ])

            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error listing admin tickets: {e}")

    async def admin_view_ticket(
        self, update: Update, _context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()

        admin_id = update.effective_user.id
        ticket_id = uuid.UUID(query.data.split("_")[-1])

        if str(admin_id) != str(settings.ADMIN_ID):
            await query.edit_message_text(
                text=TicketMessages.Error.NOT_AUTHORIZED,
                parse_mode="MarkdownV2",
            )
            return

        try:
            ticket = await self.ticket_service.get_ticket(ticket_id, admin_id)

            if not ticket:
                await query.edit_message_text(
                    text=TicketMessages.Error.NOT_FOUND,
                    parse_mode="MarkdownV2",
                )
                return

            response_section = ""
            if ticket.response:
                resolved_at = ticket.resolved_at.strftime("%Y-%m-%d %H:%M") if ticket.resolved_at else "N/A"
                response_section = f"\n✅ *Respuesta:* {ticket.response}\n_Respondido: {resolved_at}_"

            text = TicketMessages.Admin.TICKET_DETAIL.format(
                ticket_id=str(ticket.id)[:8],
                user_id=ticket.user_id,
                subject=ticket.subject,
                status=f"{ticket.status_emoji} {ticket.status.value}",
                created_at=ticket.created_at.strftime("%Y-%m-%d %H:%M"),
                message=ticket.message,
                response_section=response_section,
            )

            await query.edit_message_text(
                text=text,
                reply_markup=TicketKeyboards.ticket_actions(ticket.id),
                parse_mode="MarkdownV2",
            )

        except Exception as e:
            logger.error(f"❌ Error viewing admin ticket: {e}")

    async def admin_respond_prompt(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.answer()

        admin_id = update.effective_user.id
        ticket_id = uuid.UUID(query.data.split("_")[-1])

        if str(admin_id) != str(settings.ADMIN_ID):
            return

        context.user_data["responding_to_ticket"] = str(ticket_id)

        await query.edit_message_text(
            text=TicketMessages.Admin.RESPOND_PROMPT.format(
                ticket_id=str(ticket_id)[:8]
            ),
            parse_mode="MarkdownV2",
        )

    async def handle_admin_response(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        ticket_id_str = context.user_data.get("responding_to_ticket")
        if not ticket_id_str:
            return

        context.user_data["responding_to_ticket"] = None
        admin_id = update.effective_user.id
        response_text = update.message.text

        if str(admin_id) != str(settings.ADMIN_ID):
            return

        try:
            ticket_id = uuid.UUID(ticket_id_str)
            
            await self.ticket_service.respond_to_ticket(
                ticket_id=ticket_id,
                response=response_text,
                admin_id=admin_id,
                current_user_id=admin_id,
            )

            await update.message.reply_text(
                text="✅ *Respuesta enviada*",
                parse_mode="Markdown",
            )

            logger.info(f"🎫 Admin {admin_id} responded to ticket {ticket_id}")

        except Exception as e:
            logger.error(f"❌ Error responding to ticket: {e}")


def get_ticket_handlers(ticket_service: TicketService):
    handler = TicketHandler(ticket_service)

    return [
        MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_ticket_message),
    ]


def get_ticket_callback_handlers(ticket_service: TicketService):
    handler = TicketHandler(ticket_service)

    return [
        CallbackQueryHandler(
            handler.create_ticket_prompt, pattern="^create_ticket$"
        ),
        CallbackQueryHandler(
            handler.list_my_tickets, pattern="^list_my_tickets$"
        ),
        CallbackQueryHandler(
            handler.view_ticket, pattern=r"^view_ticket_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.admin_list_tickets, pattern="^admin_tickets$"
        ),
        CallbackQueryHandler(
            handler.admin_view_ticket, pattern=r"^admin_view_ticket_[a-f0-9\-]+$"
        ),
        CallbackQueryHandler(
            handler.admin_respond_prompt, pattern=r"^ticket_respond_[a-f0-9\-]+$"
        ),
    ]
