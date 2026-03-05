import uuid
from typing import List, Optional, Protocol

from domain.entities.consumption_billing import BillingStatus, ConsumptionBilling


class IConsumptionBillingRepository(Protocol):
    """
    Contrato para la persistencia de ciclos de facturación por consumo.
    Define cómo interactuamos con la tabla de billing en la BD.
    """

    async def save(
        self, billing: ConsumptionBilling, current_user_id: int
    ) -> ConsumptionBilling:
        """Guarda un nuevo ciclo de facturación o actualiza uno existente."""
        ...

    async def get_by_id(
        self, billing_id: uuid.UUID, current_user_id: int
    ) -> Optional[ConsumptionBilling]:
        """Busca un ciclo de facturación específico por su ID."""
        ...

    async def get_by_user(
        self, user_id: int, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """Recupera todos los ciclos de facturación de un usuario."""
        ...

    async def get_active_by_user(
        self, user_id: int, current_user_id: int
    ) -> Optional[ConsumptionBilling]:
        """
        Recupera el ciclo de facturación activo de un usuario.
        Solo puede haber uno activo por usuario.
        """
        ...

    async def get_by_status(
        self, status: BillingStatus, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """Recupera todos los ciclos con un estado específico."""
        ...

    async def get_expired_active_cycles(
        self, days: int, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """
        Recupera ciclos activos que han excedido el límite de días.
        Útil para el cron job de cierre automático.
        """
        ...

    async def update_status(
        self, billing_id: uuid.UUID, status: BillingStatus, current_user_id: int
    ) -> bool:
        """Actualiza el estado de un ciclo de facturación."""
        ...

    async def add_consumption(
        self, billing_id: uuid.UUID, mb_used: float, current_user_id: int
    ) -> bool:
        """Agrega consumo a un ciclo activo."""
        ...

    async def delete(self, billing_id: uuid.UUID, current_user_id: int) -> bool:
        """Elimina un ciclo de facturación de la base de datos."""
        ...
