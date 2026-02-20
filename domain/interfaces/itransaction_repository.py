"""
Interfaz del repositorio de transacciones.

Author: uSipipo Team
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    """Entidad de transacción."""
    id: Optional[int]
    user_id: int
    transaction_type: str
    amount: int
    balance_after: int
    description: str
    reference_id: Optional[str]
    telegram_payment_id: Optional[str]
    created_at: datetime


class ITransactionRepository(ABC):
    """Interfaz para el repositorio de transacciones."""
    
    @abstractmethod
    async def record_transaction(
        self,
        user_id: int,
        transaction_type: str,
        amount: int,
        balance_after: int,
        description: str,
        reference_id: str = None,
        telegram_payment_id: str = None
    ) -> Transaction:
        """Registra una nueva transacción."""
        pass
    
    @abstractmethod
    async def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """Obtiene las transacciones de un usuario."""
        pass
    
    @abstractmethod
    async def get_transactions_by_type(self, transaction_type: str) -> List[Dict]:
        """Obtiene transacciones por tipo."""
        pass
    
    @abstractmethod
    async def get_balance(self, user_id: int) -> Dict:
        """Obtiene el balance de un usuario."""
        pass
