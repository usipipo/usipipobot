"""Interface for subscription transaction repository."""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.subscription_transaction import SubscriptionTransaction


class ISubscriptionTransactionRepository(ABC):
    """Interface for subscription transaction persistence."""

    @abstractmethod
    async def save(self, transaction: SubscriptionTransaction) -> SubscriptionTransaction:
        """Save a subscription transaction."""
        pass

    @abstractmethod
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[SubscriptionTransaction]:
        """Get transaction by ID."""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int, limit: int = 50) -> List[SubscriptionTransaction]:
        """Get transactions by user ID."""
        pass

    @abstractmethod
    async def mark_completed(self, transaction_id: str) -> bool:
        """Mark transaction as completed (prevent double-processing)."""
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired pending transactions. Returns count of cleaned transactions."""
        pass
