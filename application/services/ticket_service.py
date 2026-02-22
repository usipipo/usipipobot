from typing import List, Optional
import uuid

from domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from domain.interfaces.iticket_repository import ITicketRepository
from utils.logger import logger


class TicketService:
    def __init__(self, ticket_repo: ITicketRepository):
        self.ticket_repo = ticket_repo

    async def create_ticket(
        self,
        user_id: int,
        subject: str,
        message: str,
        current_user_id: int,
        priority: str = "medium",
    ) -> Ticket:
        ticket = Ticket(
            user_id=user_id,
            subject=subject,
            message=message,
            priority=TicketPriority(priority),
        )
        saved = await self.ticket_repo.save(ticket, current_user_id)
        logger.info(f"Ticket {saved.id} created by user {user_id}")
        return saved

    async def get_user_tickets(self, user_id: int, current_user_id: int) -> List[Ticket]:
        return await self.ticket_repo.get_by_user(user_id, current_user_id)

    async def get_ticket(self, ticket_id: uuid.UUID, current_user_id: int) -> Optional[Ticket]:
        return await self.ticket_repo.get_by_id(ticket_id, current_user_id)

    async def get_all_open_tickets(self, current_user_id: int) -> List[Ticket]:
        return await self.ticket_repo.get_all_open(current_user_id)

    async def respond_to_ticket(
        self,
        ticket_id: uuid.UUID,
        response: str,
        admin_id: int,
        current_user_id: int,
    ) -> Ticket:
        ticket = await self.ticket_repo.get_by_id(ticket_id, current_user_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        ticket.add_response(response, admin_id)
        return await self.ticket_repo.update(ticket, current_user_id)

    async def set_in_progress(
        self, ticket_id: uuid.UUID, current_user_id: int
    ) -> Ticket:
        ticket = await self.ticket_repo.get_by_id(ticket_id, current_user_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        ticket.set_in_progress()
        return await self.ticket_repo.update(ticket, current_user_id)
