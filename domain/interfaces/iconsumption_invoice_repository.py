import uuid
from typing import List, Optional, Protocol

from domain.entities.consumption_invoice import ConsumptionInvoice, InvoiceStatus


class IConsumptionInvoiceRepository(Protocol):
    """
    Contrato para la persistencia de facturas de consumo.
    Define cómo interactuamos con la tabla de invoices en la BD.
    """

    async def save(self, invoice: ConsumptionInvoice, current_user_id: int) -> ConsumptionInvoice:
        """Guarda una nueva factura o actualiza una existente."""
        ...

    async def get_by_id(
        self, invoice_id: uuid.UUID, current_user_id: int
    ) -> Optional[ConsumptionInvoice]:
        """Busca una factura específica por su ID."""
        ...

    async def get_by_billing(
        self, billing_id: uuid.UUID, current_user_id: int
    ) -> List[ConsumptionInvoice]:
        """Recupera todas las facturas asociadas a un ciclo de facturación."""
        ...

    async def get_by_user(self, user_id: int, current_user_id: int) -> List[ConsumptionInvoice]:
        """Recupera todas las facturas de un usuario."""
        ...

    async def get_pending_by_user(
        self, user_id: int, current_user_id: int
    ) -> Optional[ConsumptionInvoice]:
        """
        Recupera la factura pendiente de un usuario.
        Solo puede haber una factura pendiente activa por usuario.
        """
        ...

    async def get_by_status(
        self, status: InvoiceStatus, current_user_id: int
    ) -> List[ConsumptionInvoice]:
        """Recupera todas las facturas con un estado específico."""
        ...

    async def get_expired_pending(self, current_user_id: int) -> List[ConsumptionInvoice]:
        """
        Recupera facturas pendientes que han expirado.
        Útil para limpieza periódica.
        """
        ...

    async def mark_as_paid(
        self, invoice_id: uuid.UUID, transaction_hash: str, current_user_id: int
    ) -> bool:
        """Marca una factura como pagada."""
        ...

    async def mark_as_expired(self, invoice_id: uuid.UUID, current_user_id: int) -> bool:
        """Marca una factura como expirada."""
        ...

    async def update_status(
        self, invoice_id: uuid.UUID, status: InvoiceStatus, current_user_id: int
    ) -> bool:
        """Actualiza el estado de una factura."""
        ...

    async def delete(self, invoice_id: uuid.UUID, current_user_id: int) -> bool:
        """Elimina una factura de la base de datos."""
        ...
