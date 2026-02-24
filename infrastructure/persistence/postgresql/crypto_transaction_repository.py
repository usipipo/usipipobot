from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.crypto_transaction import CryptoTransaction, WebhookToken
from domain.interfaces.icrypto_transaction_repository import (
    ICryptoTransactionRepository,
    IWebhookTokenRepository
)
from infrastructure.persistence.postgresql.models.crypto_transaction import (
    CryptoTransactionModel,
    WebhookTokenModel
)


class PostgresCryptoTransactionRepository(ICryptoTransactionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, transaction: CryptoTransaction) -> CryptoTransaction:
        model = CryptoTransactionModel.from_entity(transaction)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

    async def get_by_tx_hash(self, tx_hash: str) -> Optional[CryptoTransaction]:
        result = await self.session.execute(
            select(CryptoTransactionModel).where(
                CryptoTransactionModel.tx_hash == tx_hash
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_user(self, user_id: int, limit: int = 50) -> List[CryptoTransaction]:
        result = await self.session.execute(
            select(CryptoTransactionModel)
            .where(CryptoTransactionModel.user_id == user_id)
            .order_by(CryptoTransactionModel.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def update_status(self, tx_id: uuid.UUID, status: str) -> bool:
        model = await self.session.get(CryptoTransactionModel, tx_id)
        if not model:
            return False
        model.status = status
        if status == "confirmed":
            model.confirmed_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True


class PostgresWebhookTokenRepository(IWebhookTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, token: WebhookToken) -> WebhookToken:
        model = WebhookTokenModel.from_entity(token)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

    async def get_by_hash(self, token_hash: str) -> Optional[WebhookToken]:
        result = await self.session.execute(
            select(WebhookTokenModel).where(
                WebhookTokenModel.token_hash == token_hash
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def mark_used(self, token_id: uuid.UUID) -> bool:
        model = await self.session.get(WebhookTokenModel, token_id)
        if not model:
            return False
        model.used_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def cleanup_expired(self) -> int:
        result = await self.session.execute(
            delete(WebhookTokenModel).where(
                WebhookTokenModel.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.session.commit()
        return result.rowcount
