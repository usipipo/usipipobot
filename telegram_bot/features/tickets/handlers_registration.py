"""
Registro de handlers para el sistema de tickets.

Author: uSipipo Team
Version: 2.0.0 - Handler Registration
"""

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from application.services.ticket_notification_service import TicketNotificationService
from application.services.ticket_service import TicketService

from .handlers_create_ticket import (
    TICKET_CONFIRMING,
    TICKET_SELECTING_CATEGORY,
    TICKET_WRITING_MESSAGE,
    CreateTicketMixin,
)
from .handlers_ticket_actions import TICKET_REPLYING, TicketActionsMixin
from .handlers_user_tickets import TICKET_MENU, UserTicketHandler
from .handlers_view_tickets import TICKET_VIEWING, ViewTicketsMixin


class UserTicketHandlerImpl(
    UserTicketHandler, CreateTicketMixin, ViewTicketsMixin, TicketActionsMixin
):
    """Implementación combinada de handlers de tickets."""

    pass


def get_ticket_conversation_handler(
    ticket_service: TicketService,
    notification_service: TicketNotificationService,
) -> ConversationHandler:
    """Crea y retorna el handler de conversación para tickets."""
    handler = UserTicketHandlerImpl(ticket_service, notification_service)

    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handler.show_menu, pattern="^tickets_menu$"),
            CommandHandler("soporte", handler.show_menu),
        ],
        states={
            TICKET_MENU: [
                CallbackQueryHandler(handler.start_create, pattern="^tickets_create$"),
                CallbackQueryHandler(handler.show_list, pattern="^tickets_list$"),
                CallbackQueryHandler(handler.cancel, pattern="^main_menu$"),
                CallbackQueryHandler(handler.exit_to_help, pattern="^tickets_menu_exit$"),
            ],
            TICKET_SELECTING_CATEGORY: [
                CallbackQueryHandler(handler.select_category, pattern="^tickets_cat_"),
                CallbackQueryHandler(handler.cancel, pattern="^tickets_menu$"),
            ],
            TICKET_WRITING_MESSAGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handler.receive_message,
                ),
                CallbackQueryHandler(handler.cancel, pattern="^tickets_menu$"),
            ],
            TICKET_CONFIRMING: [
                CallbackQueryHandler(handler.confirm_create, pattern="^tickets_confirm$"),
                CallbackQueryHandler(handler.cancel, pattern="^tickets_menu$"),
            ],
            TICKET_VIEWING: [
                CallbackQueryHandler(handler.view_ticket, pattern="^tickets_view_"),
                CallbackQueryHandler(handler.start_reply, pattern="^tickets_reply_"),
                CallbackQueryHandler(handler.close_ticket, pattern="^tickets_close_"),
                CallbackQueryHandler(handler.show_list, pattern="^tickets_list$"),
                CallbackQueryHandler(handler.show_menu, pattern="^tickets_menu$"),
                CallbackQueryHandler(handler.back_to_main_menu, pattern="^main_menu$"),
            ],
            TICKET_REPLYING: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handler.receive_reply,
                ),
                CallbackQueryHandler(handler.cancel, pattern="^tickets_menu$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", handler.cancel),
            CallbackQueryHandler(handler.cancel, pattern="^tickets_menu$"),
        ],
        name="ticket_conversation",
        persistent=False,
    )


def get_ticket_callback_handlers(
    ticket_service: TicketService,
    notification_service: TicketNotificationService,
):
    """Retorna handlers de callback para tickets (sin conversación)."""
    handler = UserTicketHandlerImpl(ticket_service, notification_service)

    return [
        CallbackQueryHandler(handler.show_menu, pattern="^tickets_menu$"),
        CallbackQueryHandler(handler.show_list, pattern="^tickets_list$"),
    ]
