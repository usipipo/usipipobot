import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.crypto_order import CryptoOrder


class ICryptoOrderRepository(ABC):
    @abstractmethod
    async def save(self, order: CryptoOrder, current_user_id: int) -> CryptoOrder:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: uuid.UUID) -> Optional[CryptoOrder]:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[CryptoOrder]:
        pass

    @abstractmethod
    async def get_by_wallet(self, wallet_address: str) -> Optional[CryptoOrder]:
        pass

    @abstractmethod
    async def get_pending(self) -> List[CryptoOrder]:
        pass

    @abstractmethod
    async def mark_completed(
        self, order_id: uuid.UUID, tx_hash: str
    ) -> Optional[CryptoOrder]:
        pass

    @abstractmethod
    async def mark_failed(self, order_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def mark_expired(self, order_id: uuid.UUID) -> bool:
        pass
