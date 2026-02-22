from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Balance:
    stars: int = 0


class ITransactionRepository(ABC):
    @abstractmethod
    async def record_transaction(
        self,
        user_id: int,
        transaction_type: str,
        amount: int,
        balance_after: int,
        description: str,
        reference_id: Optional[str] = None,
        telegram_payment_id: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    async def get_user_transactions(self, user_id: int, limit: int = 10) -> list:
        pass

    @abstractmethod
    async def get_balance(self, user_id: int) -> Balance:
        """Get the balance for a user."""
        pass

    @abstractmethod
    async def get_transactions_by_type(self, transaction_type: str) -> List[Dict[str, Any]]:
        """Get all transactions of a specific type."""
        pass
