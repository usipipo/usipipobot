from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.ticket import Ticket, TicketCategory, TicketStatus
from domain.entities.ticket_message import TicketMessage
from domain.interfaces.iticket_repository import ITicketRepository
from infrastructure.persistence.postgresql.models.ticket import TicketModel
from infrastructure.persistence.postgresql.models.ticket_message import TicketMessageModel


class TicketRepository(ITicketRepository):
    """Implementación PostgreSQL del repositorio de tickets."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: TicketModel) -> Ticket:
        """Convierte modelo a entidad."""
        return Ticket(
            id=model.id,
            user_id=model.user_id,
            category=TicketCategory(model.category),
            priority=model.priority,
            status=TicketStatus(model.status),
            subject=model.subject,
            created_at=model.created_at,
            updated_at=model.updated_at,
            resolved_at=model.resolved_at,
            resolved_by=model.resolved_by,
            admin_notes=model.admin_notes
        )

    def _to_message_entity(self, model: TicketMessageModel) -> TicketMessage:
        """Convierte modelo de mensaje a entidad."""
        return TicketMessage(
            id=model.id,
            ticket_id=model.ticket_id,
            from_user_id=model.from_user_id,
            message=model.message,
            is_from_admin=model.is_from_admin,
            created_at=model.created_at
        )

    async def save(self, ticket: Ticket) -> Ticket:
        """Guarda un nuevo ticket."""
        model = TicketModel(
            id=ticket.id,
            user_id=ticket.user_id,
            category=ticket.category.value,
            priority=ticket.priority.value,
            status=ticket.status.value,
            subject=ticket.subject,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            resolved_at=ticket.resolved_at,
            resolved_by=ticket.resolved_by,
            admin_notes=ticket.admin_notes
        )
        self.session.add(model)
        await self.session.commit()
        return ticket

    async def get_by_id(self, ticket_id: UUID) -> Optional[Ticket]:
        """Obtiene un ticket por su ID."""
        result = await self.session.execute(
            select(TicketModel).where(TicketModel.id == ticket_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user(self, user_id: int) -> List[Ticket]:
        """Obtiene todos los tickets de un usuario."""
        result = await self.session.execute(
            select(TicketModel)
            .where(TicketModel.user_id == user_id)
            .order_by(TicketModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, ticket: Ticket) -> Ticket:
        """Actualiza un ticket existente."""
        result = await self.session.execute(
            select(TicketModel).where(TicketModel.id == ticket.id)
        )
        model = result.scalar_one()
        
        model.category = ticket.category.value
        model.priority = ticket.priority.value
        model.status = ticket.status.value
        model.subject = ticket.subject
        model.updated_at = ticket.updated_at
        model.resolved_at = ticket.resolved_at
        model.resolved_by = ticket.resolved_by
        model.admin_notes = ticket.admin_notes
        
        await self.session.commit()
        return ticket

    async def get_by_status(self, status: TicketStatus) -> List[Ticket]:
        """Obtiene tickets por estado."""
        result = await self.session.execute(
            select(TicketModel)
            .where(TicketModel.status == status.value)
            .order_by(TicketModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_category(self, category: TicketCategory) -> List[Ticket]:
        """Obtiene tickets por categoría."""
        result = await self.session.execute(
            select(TicketModel)
            .where(TicketModel.category == category.value)
            .order_by(TicketModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_all_open(self) -> List[Ticket]:
        """Obtiene todos los tickets abiertos."""
        result = await self.session.execute(
            select(TicketModel)
            .where(TicketModel.status.in_(['open', 'responded']))
            .order_by(
                TicketModel.priority.desc(),  # HIGH first
                TicketModel.created_at.asc()   # Oldest first
            )
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save_message(self, message: TicketMessage) -> TicketMessage:
        """Guarda un mensaje de ticket."""
        model = TicketMessageModel(
            id=message.id,
            ticket_id=message.ticket_id,
            from_user_id=message.from_user_id,
            message=message.message,
            is_from_admin=message.is_from_admin,
            created_at=message.created_at
        )
        self.session.add(model)
        await self.session.commit()
        return message

    async def get_messages(self, ticket_id: UUID) -> List[TicketMessage]:
        """Obtiene todos los mensajes de un ticket."""
        result = await self.session.execute(
            select(TicketMessageModel)
            .where(TicketMessageModel.ticket_id == ticket_id)
            .order_by(TicketMessageModel.created_at.asc())
        )
        return [self._to_message_entity(m) for m in result.scalars().all()]

    async def count_open(self) -> int:
        """Cuenta tickets abiertos."""
        result = await self.session.execute(
            select(func.count()).select_from(TicketModel)
            .where(TicketModel.status.in_(['open', 'responded']))
        )
        return result.scalar() or 0
