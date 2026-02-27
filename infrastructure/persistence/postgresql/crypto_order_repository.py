import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus
from domain.interfaces.icrypto_order_repository import ICryptoOrderRepository
from infrastructure.persistence.postgresql.models.crypto_order import CryptoOrderModel


class PostgresCryptoOrderRepository(ICryptoOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, order: CryptoOrder, current_user_id: int) -> CryptoOrder:
        model = CryptoOrderModel.from_entity(order)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

    async def get_by_id(self, order_id: uuid.UUID) -> Optional[CryptoOrder]:
        result = await self.session.execute(
            select(CryptoOrderModel).where(CryptoOrderModel.id == order_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_user(self, user_id: int) -> List[CryptoOrder]:
        result = await self.session.execute(
            select(CryptoOrderModel)
            .where(CryptoOrderModel.user_id == user_id)
            .order_by(CryptoOrderModel.created_at.desc())
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_wallet(self, wallet_address: str) -> Optional[CryptoOrder]:
        result = await self.session.execute(
            select(CryptoOrderModel)
            .where(
                CryptoOrderModel.wallet_address == wallet_address,
                CryptoOrderModel.status == "pending",
            )
            .order_by(CryptoOrderModel.created_at.desc())
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_pending(self) -> List[CryptoOrder]:
        result = await self.session.execute(
            select(CryptoOrderModel)
            .where(CryptoOrderModel.status == "pending")
            .order_by(CryptoOrderModel.created_at.asc())
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def mark_completed(
        self, order_id: uuid.UUID, tx_hash: str
    ) -> Optional[CryptoOrder]:
        model = await self.session.get(CryptoOrderModel, order_id)
        if not model:
            return None
        model.status = CryptoOrderStatus.COMPLETED.value
        model.tx_hash = tx_hash
        model.confirmed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

    async def mark_failed(self, order_id: uuid.UUID) -> bool:
        model = await self.session.get(CryptoOrderModel, order_id)
        if not model:
            return False
        model.status = CryptoOrderStatus.FAILED.value
        await self.session.commit()
        return True

    async def mark_expired(self, order_id: uuid.UUID) -> bool:
        model = await self.session.get(CryptoOrderModel, order_id)
        if not model:
            return False
        model.status = CryptoOrderStatus.EXPIRED.value
        await self.session.commit()
        return True
