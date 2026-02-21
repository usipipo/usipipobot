from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


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
