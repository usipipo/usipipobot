"""
Repositorio de tickets con SQLAlchemy Async para PostgreSQL.

Author: uSipipo Team
Version: 2.1.0
"""

from typing import Optional, List
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import logger

from domain.entities.ticket import Ticket
from .models import TicketModel
from .base_repository import BasePostgresRepository


class PostgresTicketRepository(BasePostgresRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def _model_to_entity(self, model: TicketModel) -> Ticket:
        return Ticket(id=model.id, user_id=model.user_id, user_name=model.user_name,
                     status=model.status, created_at=model.created_at, last_message_at=model.last_message_at)

    def _entity_to_model(self, entity: Ticket) -> TicketModel:
        return TicketModel(id=entity.id if entity.id else uuid.uuid4(), user_id=entity.user_id,
                          user_name=entity.user_name, status=entity.status,
                          created_at=entity.created_at, last_message_at=entity.last_message_at)

    async def get_open_by_user(self, user_id: int, current_user_id: int) -> Optional[Ticket]:
        await self._set_current_user(current_user_id)
        try:
            query = select(TicketModel).where(
                (TicketModel.user_id == user_id) & (TicketModel.status == "open"))
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error al obtener ticket abierto del usuario {user_id}: {e}")
            return None

    async def save(self, ticket: Ticket, current_user_id: int) -> Ticket:
        await self._set_current_user(current_user_id)
        try:
            if ticket.id:
                existing = await self.session.get(TicketModel, ticket.id)
                if existing:
                    existing.status, existing.last_message_at = ticket.status, ticket.last_message_at
                else:
                    self.session.add(self._entity_to_model(ticket))
            else:
                ticket.id = uuid.uuid4()
                self.session.add(self._entity_to_model(ticket))
            await self.session.commit()
            logger.debug(f"Ticket {ticket.id} guardado correctamente.")
            return ticket
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al guardar ticket: {e}")
            raise

    async def get_all_open(self, current_user_id: int) -> List[Ticket]:
        await self._set_current_user(current_user_id)
        try:
            query = select(TicketModel).where(TicketModel.status == "open")
            result = await self.session.execute(query)
            return [self._model_to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al obtener tickets abiertos: {e}")
            return []

    async def close_ticket(self, ticket_id: uuid.UUID, current_user_id: int) -> bool:
        await self._set_current_user(current_user_id)
        try:
            query = update(TicketModel).where(TicketModel.id == ticket_id).values(status="closed")
            await self.session.execute(query)
            await self.session.commit()
            logger.debug(f"Ticket {ticket_id} cerrado.")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al cerrar ticket {ticket_id}: {e}")
            return False

    async def get_by_id(self, ticket_id: uuid.UUID, current_user_id: int) -> Optional[Ticket]:
        await self._set_current_user(current_user_id)
        try:
            model = await self.session.get(TicketModel, ticket_id)
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Error al obtener ticket {ticket_id}: {e}")
            return None
