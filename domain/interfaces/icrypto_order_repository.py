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
    async def mark_completed(self, order_id: uuid.UUID, tx_hash: str) -> Optional[CryptoOrder]:
        pass

    @abstractmethod
    async def mark_failed(self, order_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def mark_expired(self, order_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def get_expired_orders_with_wallets(self, limit: int = 100) -> List[CryptoOrder]:
        """Obtiene órdenes expiradas que tienen wallets asignadas."""
        pass

    @abstractmethod
    async def get_reusable_wallet_for_user(self, user_id: int) -> Optional[str]:
        """Busca una wallet reutilizable de una orden expirada del usuario."""
        pass

    @abstractmethod
    async def get_any_reusable_wallet(self) -> Optional[str]:
        """Busca cualquier wallet reutilizable de órdenes expiradas."""
        pass

    @abstractmethod
    async def get_by_tron_dealer_order_id(
        self, tron_dealer_order_id: str, current_user_id: int
    ) -> Optional[CryptoOrder]:
        """Busca una orden por el ID de orden de TronDealer."""
        pass

    async def get_by_user_paginated(
        self, user_id: int, limit: int = 10, offset: int = 0, current_user_id: int = 0
    ) -> List[CryptoOrder]:
        """Get crypto orders for a user with pagination."""
        pass

    async def count_by_user(self, user_id: int, current_user_id: int = 0) -> int:
        """Count total crypto orders for a user."""
        pass
