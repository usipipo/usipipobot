from typing import List, Optional, Protocol
from uuid import UUID

from domain.entities.ticket import Ticket, TicketCategory, TicketStatus
from domain.entities.ticket_message import TicketMessage


class ITicketRepository(Protocol):
    """Interface para el repositorio de tickets."""

    async def save(self, ticket: Ticket) -> Ticket:
        """Guarda un nuevo ticket."""
        ...

    async def get_by_id(self, ticket_id: UUID) -> Optional[Ticket]:
        """Obtiene un ticket por su ID."""
        ...

    async def get_by_simple_id(self, simple_id: int) -> Optional[Ticket]:
        """Obtiene un ticket por su ID simplificado (int)."""
        ...

    async def get_by_user(self, user_id: int) -> List[Ticket]:
        """Obtiene todos los tickets de un usuario."""
        ...

    async def update(self, ticket: Ticket) -> Ticket:
        """Actualiza un ticket existente."""
        ...

    async def get_by_status(self, status: TicketStatus) -> List[Ticket]:
        """Obtiene tickets por estado."""
        ...

    async def get_by_category(self, category: TicketCategory) -> List[Ticket]:
        """Obtiene tickets por categoría."""
        ...

    async def get_all_open(self) -> List[Ticket]:
        """Obtiene todos los tickets abiertos (OPEN o RESPONDED)."""
        ...

    async def save_message(self, message: TicketMessage) -> TicketMessage:
        """Guarda un mensaje de ticket."""
        ...

    async def get_messages(self, ticket_id: UUID) -> List[TicketMessage]:
        """Obtiene todos los mensajes de un ticket."""
        ...

    async def count_open(self) -> int:
        """Cuenta tickets abiertos."""
        ...
