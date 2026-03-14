import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.consumption_invoice import ConsumptionInvoice, InvoiceStatus
from domain.interfaces.iconsumption_invoice_repository import IConsumptionInvoiceRepository
from infrastructure.persistence.postgresql.models.consumption_invoice import ConsumptionInvoiceModel


class PostgresConsumptionInvoiceRepository(IConsumptionInvoiceRepository):
    """Implementación PostgreSQL del repositorio de facturas de consumo."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, invoice: ConsumptionInvoice, current_user_id: int) -> ConsumptionInvoice:
        """Guarda una nueva factura o actualiza una existente."""
        model = ConsumptionInvoiceModel.from_entity(invoice)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

    async def get_by_id(
        self, invoice_id: uuid.UUID, current_user_id: int
    ) -> Optional[ConsumptionInvoice]:
        """Busca una factura específica por su ID."""
        result = await self.session.execute(
            select(ConsumptionInvoiceModel).where(ConsumptionInvoiceModel.id == invoice_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_billing(
        self, billing_id: uuid.UUID, current_user_id: int
    ) -> List[ConsumptionInvoice]:
        """Recupera todas las facturas asociadas a un ciclo de facturación."""
        result = await self.session.execute(
            select(ConsumptionInvoiceModel)
            .where(ConsumptionInvoiceModel.billing_id == billing_id)
            .order_by(ConsumptionInvoiceModel.created_at.desc())
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_user(self, user_id: int, current_user_id: int) -> List[ConsumptionInvoice]:
        """Recupera todas las facturas de un usuario."""
        result = await self.session.execute(
            select(ConsumptionInvoiceModel)
            .where(ConsumptionInvoiceModel.user_id == user_id)
            .order_by(ConsumptionInvoiceModel.created_at.desc())
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_pending_by_user(
        self, user_id: int, current_user_id: int
    ) -> Optional[ConsumptionInvoice]:
        """
        Recupera la factura pendiente de un usuario.
        Solo puede haber una factura pendiente activa por usuario.
        """
        result = await self.session.execute(
            select(ConsumptionInvoiceModel).where(
                ConsumptionInvoiceModel.user_id == user_id,
                ConsumptionInvoiceModel.status == InvoiceStatus.PENDING.value,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_status(
        self, status: InvoiceStatus, current_user_id: int
    ) -> List[ConsumptionInvoice]:
        """Recupera todas las facturas con un estado específico."""
        result = await self.session.execute(
            select(ConsumptionInvoiceModel)
            .where(ConsumptionInvoiceModel.status == status.value)
            .order_by(ConsumptionInvoiceModel.created_at.desc())
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_expired_pending(self, current_user_id: int) -> List[ConsumptionInvoice]:
        """
        Recupera facturas pendientes que han expirado.
        Útil para limpieza periódica.
        """
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(ConsumptionInvoiceModel).where(
                ConsumptionInvoiceModel.status == InvoiceStatus.PENDING.value,
                ConsumptionInvoiceModel.expires_at <= now,
            )
        )
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def mark_as_paid(
        self, invoice_id: uuid.UUID, transaction_hash: str, current_user_id: int
    ) -> bool:
        """Marca una factura como pagada."""
        model = await self.session.get(ConsumptionInvoiceModel, invoice_id)
        if not model:
            return False

        if model.status != InvoiceStatus.PENDING.value:
            return False

        model.status = InvoiceStatus.PAID.value
        model.transaction_hash = transaction_hash
        model.paid_at = datetime.now(timezone.utc)

        await self.session.commit()
        return True

    async def mark_as_expired(self, invoice_id: uuid.UUID, current_user_id: int) -> bool:
        """Marca una factura como expirada."""
        model = await self.session.get(ConsumptionInvoiceModel, invoice_id)
        if not model:
            return False

        if model.status == InvoiceStatus.PAID.value:
            return False

        model.status = InvoiceStatus.EXPIRED.value
        await self.session.commit()
        return True

    async def update_status(
        self, invoice_id: uuid.UUID, status: InvoiceStatus, current_user_id: int
    ) -> bool:
        """Actualiza el estado de una factura."""
        model = await self.session.get(ConsumptionInvoiceModel, invoice_id)
        if not model:
            return False

        model.status = status.value
        await self.session.commit()
        return True

    async def delete(self, invoice_id: uuid.UUID, current_user_id: int) -> bool:
        """Elimina una factura de la base de datos."""
        model = await self.session.get(ConsumptionInvoiceModel, invoice_id)
        if not model:
            return False

        await self.session.delete(model)
        await self.session.commit()
        return True
