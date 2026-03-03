"""
Sistema de tickets de soporte para usuarios.

Author: uSipipo Team
Version: 2.0.0 - Tickets Feature
"""

from .handlers_user_tickets import UserTicketHandler
from .handlers_create_ticket import CreateTicketMixin
from .handlers_view_tickets import ViewTicketsMixin
from .handlers_ticket_actions import TicketActionsMixin
from .handlers_registration import (
    UserTicketHandlerImpl,
    get_ticket_conversation_handler,
    get_ticket_callback_handlers,
)
from .messages_tickets import (
    TicketMessages,
    CATEGORY_EMOJI,
    CATEGORY_NAME,
    PRIORITY_EMOJI,
    PRIORITY_NAME,
    STATUS_EMOJI,
    STATUS_NAME,
)
from .keyboards_tickets import TicketKeyboards

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
