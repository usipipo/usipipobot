from typing import List, Optional, Tuple
from uuid import UUID

from domain.entities.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from domain.entities.ticket_message import TicketMessage
from domain.interfaces.iticket_repository import ITicketRepository
from utils.logger import logger


class TicketService:
    """Servicio para gestión de tickets de soporte."""

    # Mapeo de categoría a prioridad automática
    CATEGORY_PRIORITY = {
        TicketCategory.VPN_FAIL: TicketPriority.HIGH,
        TicketCategory.PAYMENT: TicketPriority.MEDIUM,
        TicketCategory.ACCOUNT: TicketPriority.LOW,
        TicketCategory.OTHER: TicketPriority.LOW,
    }

    def __init__(self, ticket_repo: ITicketRepository):
        self.ticket_repo = ticket_repo

    def _get_priority_for_category(self, category: TicketCategory) -> TicketPriority:
        """Determina la prioridad automática según categoría."""
        return self.CATEGORY_PRIORITY.get(category, TicketPriority.LOW)

    async def create_ticket(
        self, user_id: int, category: TicketCategory, subject: str, message: str
    ) -> Ticket:
        """Crea un nuevo ticket de soporte."""
        priority = self._get_priority_for_category(category)

        ticket = Ticket(user_id=user_id, category=category, priority=priority, subject=subject)

        saved_ticket = await self.ticket_repo.save(ticket)
        logger.info(f"Ticket created: {saved_ticket.ticket_number} by user {user_id}")

        # Add initial message
        ticket_message = TicketMessage(
            ticket_id=saved_ticket.id,
            from_user_id=user_id,
            message=message,
            is_from_admin=False,
        )
        await self.ticket_repo.save_message(ticket_message)

        return saved_ticket

    async def get_user_tickets(self, user_id: int) -> List[Ticket]:
        """Obtiene tickets del usuario ordenados por fecha."""
        return await self.ticket_repo.get_by_user(user_id)

    async def get_ticket_with_messages(
        self, ticket_id: UUID
    ) -> Optional[Tuple[Ticket, List[TicketMessage]]]:
        """Obtiene ticket con todos sus mensajes."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return None

        messages = await self.ticket_repo.get_messages(ticket_id)
        return (ticket, messages)

    async def get_ticket_by_simple_id(self, simple_id: int) -> Optional[Ticket]:
        """Obtiene ticket por ID simplificado."""
        return await self.ticket_repo.get_by_simple_id(simple_id)

    async def add_user_message(
        self, ticket_id: UUID, user_id: int, message: str
    ) -> Optional[TicketMessage]:
        """Agrega mensaje de usuario a ticket."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket or ticket.user_id != user_id:
            return None

        ticket_message = TicketMessage(
            ticket_id=ticket_id,
            from_user_id=user_id,
            message=message,
            is_from_admin=False,
        )
        saved = await self.ticket_repo.save_message(ticket_message)

        # Update ticket status if it was responded
        if ticket.status == TicketStatus.RESPONDED:
            ticket.status = TicketStatus.OPEN
            await self.ticket_repo.update(ticket)

        return saved

    async def add_admin_response(
        self, ticket_id: UUID, admin_id: int, message: str
    ) -> Optional[TicketMessage]:
        """Agrega respuesta del admin y actualiza estado."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return None

        ticket_message = TicketMessage(
            ticket_id=ticket_id,
            from_user_id=admin_id,
            message=message,
            is_from_admin=True,
        )
        saved = await self.ticket_repo.save_message(ticket_message)

        # Update status to responded
        if ticket.status in [TicketStatus.OPEN, TicketStatus.RESPONDED]:
            ticket.update_status(TicketStatus.RESPONDED)
            await self.ticket_repo.update(ticket)

        logger.info(f"Admin {admin_id} responded to ticket {ticket.ticket_number}")
        return saved

    async def resolve_ticket(
        self, ticket_id: UUID, admin_id: int, notes: Optional[str] = None
    ) -> Optional[Ticket]:
        """Marca ticket como resuelto."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return None

        ticket.update_status(TicketStatus.RESOLVED, admin_id)
        if notes:
            ticket.admin_notes = notes

        updated = await self.ticket_repo.update(ticket)
        logger.info(f"Ticket {ticket.ticket_number} resolved by admin {admin_id}")
        return updated

    async def close_ticket(
        self, ticket_id: UUID, user_id: int, is_admin: bool = False
    ) -> Optional[Ticket]:
        """Cierra ticket (por usuario o admin)."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return None

        # User can only close their own tickets
        if not is_admin and ticket.user_id != user_id:
            return None

        ticket.update_status(TicketStatus.CLOSED, user_id if is_admin else None)
        updated = await self.ticket_repo.update(ticket)
        logger.info(
            f"Ticket {ticket.ticket_number} closed by {'admin' if is_admin else 'user'} {user_id}"
        )
        return updated

    async def reopen_ticket(self, ticket_id: UUID, admin_id: int) -> Optional[Ticket]:
        """Reabre un ticket cerrado (solo admin)."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return None

        if ticket.status != TicketStatus.CLOSED:
            return None

        ticket.update_status(TicketStatus.OPEN)
        updated = await self.ticket_repo.update(ticket)
        logger.info(f"Ticket {ticket.ticket_number} reopened by admin {admin_id}")
        return updated

    async def get_pending_tickets(self) -> List[Ticket]:
        """Obtiene tickets pendientes para admin."""
        return await self.ticket_repo.get_all_open()

    async def get_tickets_by_category(self, category: TicketCategory) -> List[Ticket]:
        """Obtiene tickets por categoría."""
        return await self.ticket_repo.get_by_category(category)

    async def count_open_tickets(self) -> int:
        """Cuenta tickets abiertos."""
        return await self.ticket_repo.count_open()
