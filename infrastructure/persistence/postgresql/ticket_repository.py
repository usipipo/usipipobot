from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.ticket import Ticket, TicketStatus, TicketPriority
from domain.interfaces.iticket_repository import ITicketRepository
from infrastructure.persistence.postgresql.models.ticket import TicketModel


class PostgresTicketRepository(ITicketRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, ticket: Ticket, current_user_id: int) -> Ticket:
        model = TicketModel(
            user_id=ticket.user_id,
            subject=ticket.subject,
            message=ticket.message,
            status=ticket.status.value,
            priority=ticket.priority.value,
        )
        self.session.add(model)
        await self.session.commit()
        return Ticket(
            id=model.id,
            user_id=model.user_id,
            subject=model.subject,
            message=model.message,
            status=TicketStatus(model.status),
            priority=TicketPriority(model.priority),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, ticket_id: uuid.UUID, current_user_id: int) -> Optional[Ticket]:
        result = await self.session.execute(
            select(TicketModel).where(TicketModel.id == ticket_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_user(self, user_id: int, current_user_id: int) -> List[Ticket]:
        result = await self.session.execute(
            select(TicketModel)
            .where(TicketModel.user_id == user_id)
            .order_by(TicketModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_all_open(self, current_user_id: int) -> List[Ticket]:
        result = await self.session.execute(
            select(TicketModel)
            .where(TicketModel.status.in_(["open", "in_progress"]))
            .order_by(TicketModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, ticket: Ticket, current_user_id: int) -> Ticket:
        result = await self.session.execute(
            select(TicketModel).where(TicketModel.id == ticket.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = ticket.status.value
            model.response = ticket.response
            model.resolved_by = ticket.resolved_by
            model.resolved_at = ticket.resolved_at
            await self.session.commit()
        return ticket

    def _to_entity(self, model: TicketModel) -> Ticket:
        return Ticket(
            id=model.id,
            user_id=model.user_id,
            subject=model.subject,
            message=model.message,
            status=TicketStatus(model.status),
            priority=TicketPriority(model.priority),
            created_at=model.created_at,
            updated_at=model.updated_at,
            resolved_at=model.resolved_at,
            resolved_by=model.resolved_by,
            response=model.response,
        )
