import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.consumption_billing import BillingStatus, ConsumptionBilling
from domain.interfaces.iconsumption_billing_repository import (
    IConsumptionBillingRepository,
)
from infrastructure.persistence.postgresql.models.consumption_billing import (
    ConsumptionBillingModel,
)


class PostgresConsumptionBillingRepository(IConsumptionBillingRepository):
    """Implementación PostgreSQL del repositorio de billing por consumo."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(
        self, billing: ConsumptionBilling, current_user_id: int
    ) -> ConsumptionBilling:
        """Guarda un nuevo ciclo de facturación o actualiza uno existente."""
        model = ConsumptionBillingModel.from_entity(billing)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

    async def get_by_id(
        self, billing_id: uuid.UUID, current_user_id: int
    ) -> Optional[ConsumptionBilling]:
        """Busca un ciclo de facturación específico por su ID."""
        result = await self.session.execute(
            select(ConsumptionBillingModel).where(
                ConsumptionBillingModel.id == billing_id
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_user(
        self, user_id: int, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """Recupera todos los ciclos de facturación de un usuario."""
        result = await self.session.execute(
            select(ConsumptionBillingModel)
            .where(ConsumptionBillingModel.user_id == user_id)
            .order_by(ConsumptionBillingModel.created_at.desc())
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_active_by_user(
        self, user_id: int, current_user_id: int
    ) -> Optional[ConsumptionBilling]:
        """
        Recupera el ciclo de facturación activo de un usuario.
        Solo puede haber uno activo por usuario.
        """
        result = await self.session.execute(
            select(ConsumptionBillingModel).where(
                ConsumptionBillingModel.user_id == user_id,
                ConsumptionBillingModel.status == BillingStatus.ACTIVE.value,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_status(
        self, status: BillingStatus, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """Recupera todos los ciclos con un estado específico."""
        result = await self.session.execute(
            select(ConsumptionBillingModel)
            .where(ConsumptionBillingModel.status == status.value)
            .order_by(ConsumptionBillingModel.created_at.desc())
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_expired_active_cycles(
        self, days: int, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """
        Recupera ciclos activos que han excedido el límite de días.
        Útil para el cron job de cierre automático.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            select(ConsumptionBillingModel).where(
                ConsumptionBillingModel.status == BillingStatus.ACTIVE.value,
                ConsumptionBillingModel.started_at <= cutoff_date,
            )
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def update_status(
        self, billing_id: uuid.UUID, status: BillingStatus, current_user_id: int
    ) -> bool:
        """Actualiza el estado de un ciclo de facturación."""
        model = await self.session.get(ConsumptionBillingModel, billing_id)
        if not model:
            return False

        model.status = status.value

        if status == BillingStatus.CLOSED and not model.ended_at:
            model.ended_at = datetime.now(timezone.utc)

        await self.session.commit()
        return True

    async def add_consumption(
        self, billing_id: uuid.UUID, mb_used: float, current_user_id: int
    ) -> bool:
        """Agrega consumo a un ciclo activo."""
        model = await self.session.get(ConsumptionBillingModel, billing_id)
        if not model:
            return False

        if model.status != BillingStatus.ACTIVE.value:
            return False

        # Agregar consumo y recalcular costo
        model.mb_consumed += Decimal(str(mb_used))
        # Usar el precio almacenado en el modelo
        model.total_cost_usd = (model.mb_consumed * model.price_per_mb_usd).quantize(
            Decimal("0.000001")
        )

        await self.session.commit()
        return True

    async def delete(self, billing_id: uuid.UUID, current_user_id: int) -> bool:
        """Elimina un ciclo de facturación de la base de datos."""
        model = await self.session.get(ConsumptionBillingModel, billing_id)
        if not model:
            return False

        await self.session.delete(model)
        await self.session.commit()
        return True
