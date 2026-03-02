"""
Teclados para el sistema de tickets de soporte.

Author: uSipipo Team
Version: 3.0.0 - Tickets System
"""

from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from domain.entities.ticket import Ticket, TicketStatus


class TicketKeyboards:
    """Teclados para el sistema de tickets de soporte."""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Menú principal de soporte."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🎫 Crear Ticket", callback_data="tickets_create"
                ),
                InlineKeyboardButton(
                    "📋 Mis Tickets", callback_data="tickets_list"
                ),
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="admin"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def category_selection() -> InlineKeyboardMarkup:
        """Selección de categoría para el ticket."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔌 VPN No Conecta", callback_data="tickets_cat_vpn"
                ),
                InlineKeyboardButton(
                    "💳 Problema de Pago", callback_data="tickets_cat_payment"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📱 Configuración", callback_data="tickets_cat_config"
                ),
                InlineKeyboardButton(
                    "🐛 Error/Reporte", callback_data="tickets_cat_bug"
                ),
            ],
            [
                InlineKeyboardButton(
                    "❓ Otra Consulta", callback_data="tickets_cat_other"
                ),
            ],
            [
                InlineKeyboardButton("🔙 Cancelar", callback_data="tickets_menu"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_ticket() -> InlineKeyboardMarkup:
        """Confirmar creación del ticket."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Confirmar", callback_data="tickets_confirm"
                ),
                InlineKeyboardButton(
                    "❌ Cancelar", callback_data="tickets_menu"
                ),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def tickets_list(
        tickets: List[Ticket],
        page: int = 0,
        per_page: int = 5,
    ) -> InlineKeyboardMarkup:
        """Lista paginada de tickets del usuario."""
        keyboard = []

        # Botones para cada ticket
        for ticket in tickets:
            status_emoji = TicketKeyboards._get_status_emoji(ticket.status)
            btn_text = f"{status_emoji} #{ticket.id}: {ticket.subject[:20]}"
            callback = f"tickets_view_{ticket.id}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])

        # Botones de paginación
        total_tickets = len(tickets)
        has_more = total_tickets == per_page

        if page > 0 or has_more:
            nav_buttons = []
            if page > 0:
                prev_callback = f"tickets_page_{page - 1}"
                nav_buttons.append(
                    InlineKeyboardButton("◀️ Anterior", callback_data=prev_callback)
                )
            if has_more:
                next_callback = f"tickets_page_{page + 1}"
                nav_buttons.append(
                    InlineKeyboardButton("Siguiente ▶️", callback_data=next_callback)
                )
            keyboard.append(nav_buttons)

        # Volver
        keyboard.append(
            [InlineKeyboardButton("🔙 Volver", callback_data="tickets_menu")]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def ticket_detail(
        ticket_id: int,
        status: TicketStatus,
        can_reply: bool = True,
        can_close: bool = True,
    ) -> InlineKeyboardMarkup:
        """Acciones disponibles para un ticket."""
        keyboard = []

        # Botones de acción según estado
        action_buttons = []

        if can_reply and status != TicketStatus.CLOSED:
            action_buttons.append(
                InlineKeyboardButton(
                    "💬 Responder", callback_data=f"tickets_reply_{ticket_id}"
                )
            )

        if can_close and status != TicketStatus.CLOSED:
            action_buttons.append(
                InlineKeyboardButton(
                    "🔒 Cerrar", callback_data=f"tickets_close_{ticket_id}"
                )
            )

        if action_buttons:
            keyboard.append(action_buttons)

        # Navegación
        keyboard.append(
            [
                InlineKeyboardButton(
                    "◀️ Volver a lista", callback_data="tickets_list"
                ),
            ]
        )
        keyboard.append(
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="tickets_menu")]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_menu(open_count: int = 0) -> InlineKeyboardMarkup:
        """Menú principal de administración de tickets."""
        open_text = f"📂 Tickets Abiertos ({open_count})" if open_count > 0 else "📂 Tickets Abiertos"

        keyboard = [
            [
                InlineKeyboardButton(open_text, callback_data="admin_tickets_open"),
            ],
            [
                InlineKeyboardButton(
                    "📋 Todos los Tickets", callback_data="admin_tickets"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔍 Filtrar por Categoría", callback_data="admin_tickets_filter"
                ),
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="admin"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_tickets_list(
        tickets: List[Ticket],
        page: int = 0,
        per_page: int = 5,
        filter_status: Optional[str] = None,
    ) -> InlineKeyboardMarkup:
        """Lista paginada de tickets para administradores."""
        keyboard = []

        # Botones para cada ticket
        for ticket in tickets:
            status_emoji = TicketKeyboards._get_status_emoji(ticket.status)
            user_info = f"@{ticket.user_username}" if ticket.user_username else f"User-{ticket.user_id}"
            btn_text = f"{status_emoji} #{ticket.id}: {user_info}"
            callback = f"admin_ticket_{ticket.id}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])

        # Botones de paginación
        total_tickets = len(tickets)
        has_more = total_tickets == per_page

        if page > 0 or has_more:
            nav_buttons = []
            if page > 0:
                prev_callback = f"admin_tickets_page_{page - 1}"
                if filter_status:
                    prev_callback = f"admin_tickets_{filter_status}_page_{page - 1}"
                nav_buttons.append(
                    InlineKeyboardButton("◀️ Anterior", callback_data=prev_callback)
                )
            if has_more:
                next_callback = f"admin_tickets_page_{page + 1}"
                if filter_status:
                    next_callback = f"admin_tickets_{filter_status}_page_{page + 1}"
                nav_buttons.append(
                    InlineKeyboardButton("Siguiente ▶️", callback_data=next_callback)
                )
            keyboard.append(nav_buttons)

        # Volver
        keyboard.append(
            [InlineKeyboardButton("🔙 Volver", callback_data="admin_tickets_menu")]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_ticket_actions(
        ticket_id: int,
        status: TicketStatus,
    ) -> InlineKeyboardMarkup:
        """Acciones de administrador para un ticket."""
        keyboard = []

        action_buttons = []

        if status != TicketStatus.CLOSED:
            action_buttons.append(
                InlineKeyboardButton(
                    "💬 Responder", callback_data=f"admin_ticket_resp_{ticket_id}"
                )
            )
            action_buttons.append(
                InlineKeyboardButton(
                    "🔒 Cerrar", callback_data=f"admin_ticket_close_{ticket_id}"
                )
            )

        if status == TicketStatus.CLOSED:
            action_buttons.append(
                InlineKeyboardButton(
                    "🔄 Reabrir", callback_data=f"admin_ticket_reopen_{ticket_id}"
                )
            )

        if action_buttons:
            keyboard.append(action_buttons)

        # Navegación
        keyboard.append(
            [
                InlineKeyboardButton(
                    "◀️ Volver a lista", callback_data="admin_tickets"
                ),
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🏠 Menú Admin", callback_data="admin_tickets_menu"
                )
            ]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def admin_category_filter() -> InlineKeyboardMarkup:
        """Filtro de tickets por categoría."""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔌 VPN", callback_data="admin_tickets_filter_vpn"
                ),
                InlineKeyboardButton(
                    "💳 Pago", callback_data="admin_tickets_filter_payment"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📱 Config", callback_data="admin_tickets_filter_config"
                ),
                InlineKeyboardButton(
                    "🐛 Bug", callback_data="admin_tickets_filter_bug"
                ),
            ],
            [
                InlineKeyboardButton(
                    "❓ Otros", callback_data="admin_tickets_filter_other"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Todos", callback_data="admin_tickets"
                ),
            ],
            [
                InlineKeyboardButton("🔙 Volver", callback_data="admin_tickets_menu"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        """Botón para volver al menú de tickets."""
        keyboard = [
            [InlineKeyboardButton("🔙 Volver", callback_data="tickets_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def cancel_action() -> InlineKeyboardMarkup:
        """Botón para cancelar la acción actual."""
        keyboard = [
            [InlineKeyboardButton("❌ Cancelar", callback_data="tickets_menu")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def _get_status_emoji(status: TicketStatus) -> str:
        """Obtiene el emoji correspondiente al estado del ticket."""
        status_emojis = {
            TicketStatus.OPEN: "🟢",
            TicketStatus.IN_PROGRESS: "🔵",
            TicketStatus.WAITING_USER: "🟡",
            TicketStatus.WAITING_ADMIN: "🟠",
            TicketStatus.CLOSED: "🔴",
        }
        return status_emojis.get(status, "⚪")


# Funciones de conveniencia para importación directa
def main_menu() -> InlineKeyboardMarkup:
    """Menú principal de soporte."""
    return TicketKeyboards.main_menu()


def category_selection() -> InlineKeyboardMarkup:
    """Selección de categoría para el ticket."""
    return TicketKeyboards.category_selection()


def confirm_ticket() -> InlineKeyboardMarkup:
    """Confirmar creación del ticket."""
    return TicketKeyboards.confirm_ticket()


def tickets_list(
    tickets: List[Ticket],
    page: int = 0,
    per_page: int = 5,
) -> InlineKeyboardMarkup:
    """Lista paginada de tickets del usuario."""
    return TicketKeyboards.tickets_list(tickets, page, per_page)


def ticket_detail(
    ticket_id: int,
    status: TicketStatus,
    can_reply: bool = True,
    can_close: bool = True,
) -> InlineKeyboardMarkup:
    """Acciones disponibles para un ticket."""
    return TicketKeyboards.ticket_detail(ticket_id, status, can_reply, can_close)


def admin_menu(open_count: int = 0) -> InlineKeyboardMarkup:
    """Menú principal de administración de tickets."""
    return TicketKeyboards.admin_menu(open_count)


def admin_tickets_list(
    tickets: List[Ticket],
    page: int = 0,
    per_page: int = 5,
) -> InlineKeyboardMarkup:
    """Lista paginada de tickets para administradores."""
    return TicketKeyboards.admin_tickets_list(tickets, page, per_page)


def admin_ticket_actions(
    ticket_id: int,
    status: TicketStatus,
) -> InlineKeyboardMarkup:
    """Acciones de administrador para un ticket."""
    return TicketKeyboards.admin_ticket_actions(ticket_id, status)


def admin_category_filter() -> InlineKeyboardMarkup:
    """Filtro de tickets por categoría."""
    return TicketKeyboards.admin_category_filter()


def back_to_menu() -> InlineKeyboardMarkup:
    """Botón para volver al menú de tickets."""
    return TicketKeyboards.back_to_menu()


def cancel_action() -> InlineKeyboardMarkup:
    """Botón para cancelar la acción actual."""
    return TicketKeyboards.cancel_action()
