from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from domain.entities.ticket import Ticket


class ITicketRepository(ABC):
    @abstractmethod
    async def save(self, ticket: Ticket, current_user_id: int) -> Ticket:
        pass

    @abstractmethod
    async def get_by_id(self, ticket_id: uuid.UUID, current_user_id: int) -> Optional[Ticket]:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int, current_user_id: int) -> List[Ticket]:
        pass

    @abstractmethod
    async def get_all_open(self, current_user_id: int) -> List[Ticket]:
        pass

    @abstractmethod
    async def update(self, ticket: Ticket, current_user_id: int) -> Ticket:
        pass
