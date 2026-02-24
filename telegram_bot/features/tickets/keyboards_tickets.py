import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class TicketKeyboards:
    @staticmethod
    def ticket_actions(ticket_id: uuid.UUID) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Responder", callback_data=f"ticket_respond_{ticket_id}"
                )
            ],
            [InlineKeyboardButton("🔙 Volver", callback_data="admin_tickets")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def user_ticket_actions(ticket_id: uuid.UUID) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Volver a Mis Tickets", callback_data="list_my_tickets"
                )
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_support() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🔙 Volver a Soporte", callback_data="help_support")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def ticket_list_item(
        ticket_id: uuid.UUID, subject: str, status: str
    ) -> InlineKeyboardMarkup:
        status_emoji = {
            "open": "🟡",
            "in_progress": "🔵",
            "resolved": "🟢",
            "closed": "⚫",
        }.get(status, "⚪")
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{status_emoji} {subject[:30]}...",
                    callback_data=f"view_ticket_{ticket_id}",
                )
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
