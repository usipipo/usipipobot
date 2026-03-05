"""
Sistema de tickets de soporte para usuarios.

Author: uSipipo Team
Version: 2.0.0 - Tickets Feature
"""

from .handlers_create_ticket import CreateTicketMixin
from .handlers_registration import (
    UserTicketHandlerImpl,
    get_ticket_callback_handlers,
    get_ticket_conversation_handler,
)
from .handlers_ticket_actions import TicketActionsMixin
from .handlers_user_tickets import UserTicketHandler
from .handlers_view_tickets import ViewTicketsMixin
from .keyboards_tickets import TicketKeyboards
from .messages_tickets import (
    CATEGORY_EMOJI,
    CATEGORY_NAME,
    PRIORITY_EMOJI,
    PRIORITY_NAME,
    STATUS_EMOJI,
    STATUS_NAME,
    TicketMessages,
)

__all__ = [
    "UserTicketHandler",
    "CreateTicketMixin",
    "ViewTicketsMixin",
    "TicketActionsMixin",
    "UserTicketHandlerImpl",
    "get_ticket_conversation_handler",
    "get_ticket_callback_handlers",
    "TicketMessages",
    "TicketKeyboards",
    "CATEGORY_EMOJI",
    "CATEGORY_NAME",
    "PRIORITY_EMOJI",
    "PRIORITY_NAME",
    "STATUS_EMOJI",
    "STATUS_NAME",
]
