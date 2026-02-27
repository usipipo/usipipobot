from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from domain.entities.balance import Balance


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
        """
        Obtiene el saldo actual de un usuario.

        Args:
            user_id: ID del usuario de Telegram.

        Returns:
            Objeto Balance con el saldo en stars del usuario.
            Retorna Balance con 0 stars si no hay transacciones.
        """
        pass
