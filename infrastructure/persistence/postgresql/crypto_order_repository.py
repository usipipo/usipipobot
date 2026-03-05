import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
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

    async def get_by_user_paginated(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[CryptoOrder]:
        """Obtener órdenes de un usuario con paginación."""
        result = await self.session.execute(
            select(CryptoOrderModel)
            .where(CryptoOrderModel.user_id == user_id)
            .order_by(CryptoOrderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def count_by_user(self, user_id: int) -> int:
        """Contar total de órdenes de un usuario."""
        result = await self.session.execute(
            select(func.count()).where(CryptoOrderModel.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_expired_orders_with_wallets(
        self, limit: int = 100
    ) -> List[CryptoOrder]:
        """Obtiene órdenes expiradas que tienen wallets asignadas."""
        result = await self.session.execute(
            select(CryptoOrderModel)
            .where(
                CryptoOrderModel.status == "expired",
                CryptoOrderModel.wallet_address.isnot(None),
            )
            .order_by(CryptoOrderModel.expires_at.asc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_reusable_wallet_for_user(self, user_id: int) -> Optional[str]:
        """Busca una wallet reutilizable de una orden expirada del mismo usuario."""
        result = await self.session.execute(
            select(CryptoOrderModel.wallet_address)
            .where(
                CryptoOrderModel.user_id == user_id,
                CryptoOrderModel.status == "expired",
                CryptoOrderModel.wallet_address.isnot(None),
            )
            .order_by(CryptoOrderModel.expires_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row if row else None

    async def get_any_reusable_wallet(self) -> Optional[str]:
        """Busca cualquier wallet reutilizable de órdenes expiradas."""
        from sqlalchemy import not_

        subquery = (
            select(CryptoOrderModel.wallet_address)
            .where(CryptoOrderModel.status.in_(["pending", "completed"]))
            .distinct()
            .scalar_subquery()
        )

        result = await self.session.execute(
            select(CryptoOrderModel.wallet_address)
            .where(
                CryptoOrderModel.status == "expired",
                CryptoOrderModel.wallet_address.isnot(None),
                not_(CryptoOrderModel.wallet_address.in_(subquery)),
            )
            .order_by(CryptoOrderModel.expires_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row if row else None
