import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.crypto_transaction import CryptoTransaction, WebhookToken


class ICryptoTransactionRepository(ABC):
    @abstractmethod
    async def save(self, transaction: CryptoTransaction) -> CryptoTransaction:
        pass

    @abstractmethod
    async def get_by_tx_hash(self, tx_hash: str) -> Optional[CryptoTransaction]:
        pass

    @abstractmethod
    async def get_by_user(
        self, user_id: int, limit: int = 50
    ) -> List[CryptoTransaction]:
        pass

    @abstractmethod
    async def update_status(self, tx_id: uuid.UUID, status: str) -> bool:
        pass


class IWebhookTokenRepository(ABC):
    @abstractmethod
    async def save(self, token: WebhookToken) -> WebhookToken:
        pass

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> Optional[WebhookToken]:
        pass

    @abstractmethod
    async def mark_used(self, token_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        pass
