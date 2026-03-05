"""
Servicio de facturación por consumo (Facade).

⚠️ Este servicio ha sido refactorizado. Las implementaciones se han
movido a submódulos especializados para mantener archivos bajo 300 líneas:
- consumption_billing_dtos.py: DTOs (ConsumptionSummary, ActivationResult, etc.)
- consumption_billing_activation.py: Activación y cancelación del modo consumo
- consumption_billing_cycle.py: Gestión de ciclos (cierre, pago, registro, consultas)

Este archivo mantiene la interfaz pública para compatibilidad hacia atrás.

Author: uSipipo Team
Version: 2.0.0 - Refactored into sub-services
"""

import uuid
from decimal import Decimal
from typing import List, Optional, Tuple

from config import settings
from domain.entities.consumption_billing import ConsumptionBilling
from domain.interfaces.iconsumption_billing_repository import (
    IConsumptionBillingRepository,
)
from domain.interfaces.iuser_repository import IUserRepository

from .consumption_billing_activation import ConsumptionActivationService
from .consumption_billing_cycle import ConsumptionCycleService
from .consumption_billing_dtos import (
    ActivationResult,
    CancellationResult,
    ConsumptionSummary,
)


class ConsumptionBillingService:
    """
    Servicio de aplicación para gestionar ciclos de facturación por consumo (Facade).

    Delega operaciones a servicios especializados para mantener
    SRP (Single Responsibility Principle):
    - ConsumptionActivationService: activar/cancelar modo consumo
    - ConsumptionCycleService: ciclos, registro de uso, consultas
    """

    def __init__(
        self,
        billing_repo: IConsumptionBillingRepository,
        user_repo: IUserRepository,
    ):
        self.billing_repo = billing_repo
        self.user_repo = user_repo
        self.price_per_mb = Decimal(str(settings.CONSUMPTION_PRICE_PER_MB_USD))
        self.cycle_days = settings.CONSUMPTION_CYCLE_DAYS

        self._activation = ConsumptionActivationService(
            billing_repo, user_repo, self.price_per_mb
        )
        self._cycle = ConsumptionCycleService(billing_repo, user_repo, self.cycle_days)

    # ============================================
    # DELEGACIÓN A ConsumptionActivationService
    # ============================================

    async def can_activate_consumption(
        self, user_id: int, current_user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Verifica si un usuario puede activar el modo consumo."""
        return await self._activation.can_activate_consumption(user_id, current_user_id)

    async def activate_consumption_mode(
        self, user_id: int, current_user_id: int
    ) -> ActivationResult:
        """Activa el modo consumo para un usuario."""
        return await self._activation.activate_consumption_mode(
            user_id, current_user_id
        )

    async def can_cancel_consumption(
        self, user_id: int, current_user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Verifica si un usuario puede cancelar el modo consumo."""
        return await self._activation.can_cancel_consumption(user_id, current_user_id)

    async def cancel_consumption_mode(
        self, user_id: int, current_user_id: int
    ) -> CancellationResult:
        """Cancela el modo consumo para un usuario."""
        return await self._activation.cancel_consumption_mode(user_id, current_user_id)

    # ============================================
    # DELEGACIÓN A ConsumptionCycleService
    # ============================================

    async def record_data_usage(
        self, user_id: int, mb_used: float, current_user_id: int
    ) -> bool:
        """Registra consumo de datos para un usuario en modo consumo."""
        return await self._cycle.record_data_usage(user_id, mb_used, current_user_id)

    async def get_current_consumption(
        self, user_id: int, current_user_id: int
    ) -> Optional[ConsumptionSummary]:
        """Obtiene el resumen de consumo actual de un usuario."""
        return await self._cycle.get_current_consumption(user_id, current_user_id)

    async def close_billing_cycle(
        self, billing_id: uuid.UUID, current_user_id: int
    ) -> bool:
        """Cierra un ciclo de facturación."""
        return await self._cycle.close_billing_cycle(billing_id, current_user_id)

    async def mark_cycle_as_paid(
        self, billing_id: uuid.UUID, current_user_id: int
    ) -> bool:
        """Marca un ciclo como pagado."""
        return await self._cycle.mark_cycle_as_paid(billing_id, current_user_id)

    async def get_expired_cycles(
        self, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """Obtiene ciclos que han excedido el tiempo límite."""
        return await self._cycle.get_expired_cycles(current_user_id)

    async def get_user_billing_history(
        self, user_id: int, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """Obtiene el historial de ciclos de un usuario."""
        return await self._cycle.get_user_billing_history(user_id, current_user_id)
