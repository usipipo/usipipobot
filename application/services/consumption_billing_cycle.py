"""
Servicio de gestión de ciclos de facturación por consumo.

Contiene la lógica para cerrar ciclos, registrar consumo,
marcar pagos y consultar historial de facturación.

Author: uSipipo Team
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from domain.entities.consumption_billing import BillingStatus, ConsumptionBilling
from domain.interfaces.iconsumption_billing_repository import IConsumptionBillingRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger

from .consumption_billing_dtos import ConsumptionSummary


class ConsumptionCycleService:
    """
    Servicio para gestionar ciclos de facturación por consumo.

    Responsabilidades:
    - Registrar consumo de datos
    - Cerrar ciclos de facturación
    - Marcar ciclos como pagados
    - Consultar consumo actual e historial
    - Obtener ciclos expirados
    """

    def __init__(
        self,
        billing_repo: IConsumptionBillingRepository,
        user_repo: IUserRepository,
        cycle_days: int,
    ):
        self.billing_repo = billing_repo
        self.user_repo = user_repo
        self.cycle_days = cycle_days

    async def record_data_usage(self, user_id: int, mb_used: float, current_user_id: int) -> bool:
        """
        Registra consumo de datos para un usuario en modo consumo.

        Args:
            user_id: ID del usuario
            mb_used: MB consumidos
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            True si se registró exitosamente
        """
        try:
            # Obtener ciclo activo
            billing = await self.billing_repo.get_active_by_user(user_id, current_user_id)

            if not billing or billing.id is None:
                logger.debug(f"Usuario {user_id} no tiene ciclo de consumo activo")
                return False

            # Agregar consumo
            success = await self.billing_repo.add_consumption(billing.id, mb_used, current_user_id)

            if success:
                logger.debug(
                    f"📊 Consumo registrado - user_id={user_id}, " f"mb_used={mb_used:.2f}"
                )

            return success

        except Exception as e:
            logger.error(f"❌ Error registrando consumo: {e}")
            return False

    async def get_current_consumption(
        self, user_id: int, current_user_id: int
    ) -> Optional[ConsumptionSummary]:
        """
        Obtiene el resumen de consumo actual de un usuario.

        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            ConsumptionSummary o None si no tiene ciclo activo
        """
        try:
            billing = await self.billing_repo.get_active_by_user(user_id, current_user_id)

            if not billing:
                # Verificar si tiene ciclo cerrado (deuda pendiente)
                user = await self.user_repo.get_by_id(user_id, current_user_id)
                if user and user.current_billing_id:
                    billing = await self.billing_repo.get_by_id(
                        user.current_billing_id, current_user_id
                    )

                if not billing:
                    return None

            # Calcular días activos
            days_active = 0
            if billing.started_at:
                delta = datetime.now(timezone.utc) - billing.started_at
                days_active = delta.days

            return ConsumptionSummary(
                billing_id=billing.id,
                mb_consumed=billing.mb_consumed,
                gb_consumed=billing.gb_consumed,
                total_cost_usd=billing.total_cost_usd,
                days_active=days_active,
                is_active=billing.is_active,
                formatted_cost=billing.get_formatted_cost(),
                formatted_consumption=billing.get_formatted_consumption(),
            )

        except Exception as e:
            logger.error(f"❌ Error obteniendo consumo: {e}")
            return None

    async def close_billing_cycle(self, billing_id: uuid.UUID, current_user_id: int) -> bool:
        """
        Cierra un ciclo de facturación.

        Args:
            billing_id: ID del ciclo a cerrar
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            True si se cerró exitosamente
        """
        try:
            billing = await self.billing_repo.get_by_id(billing_id, current_user_id)
            if not billing:
                logger.error(f"Ciclo {billing_id} no encontrado")
                return False

            if not billing.is_active:
                logger.warning(f"Ciclo {billing_id} ya no está activo")
                return False

            # Cerrar ciclo en la entidad
            billing.close_cycle()

            # Actualizar en BD
            success = await self.billing_repo.update_status(
                billing_id, BillingStatus.CLOSED, current_user_id
            )

            if success:
                # Actualizar usuario
                user = await self.user_repo.get_by_id(billing.user_id, current_user_id)
                if user:
                    user.mark_as_has_debt()
                    await self.user_repo.save(user, current_user_id)

                    # Block all user keys
                    from application.services.common.container import get_container
                    from application.services.consumption_vpn_integration_service import (
                        ConsumptionVpnIntegrationService,
                    )

                    container = get_container()
                    if container:
                        vpn_integration = container.resolve(ConsumptionVpnIntegrationService)
                        if vpn_integration:
                            block_result = await vpn_integration.block_user_keys(  # type: ignore
                                billing.user_id, current_user_id
                            )

                            if not block_result["success"]:
                                logger.error(
                                    f"Failed to block keys for user {billing.user_id}: "
                                    f"{block_result['errors']}"
                                )
                        else:
                            logger.error("VPN integration service not available")
                    else:
                        logger.error("Container not available for blocking keys")

                logger.info(
                    f"🔒 Ciclo cerrado - billing_id={billing_id}, "
                    f"user_id={billing.user_id}, "
                    f"cost=${billing.total_cost_usd:.2f}"
                )

            return success

        except Exception as e:
            logger.error(f"❌ Error cerrando ciclo: {e}")
            return False

    async def mark_cycle_as_paid(self, billing_id: uuid.UUID, current_user_id: int) -> bool:
        """
        Marca un ciclo como pagado.

        Args:
            billing_id: ID del ciclo
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            True si se actualizó exitosamente
        """
        try:
            billing = await self.billing_repo.get_by_id(billing_id, current_user_id)
            if not billing:
                return False

            if not billing.is_closed:
                logger.warning(f"No se puede pagar ciclo {billing_id} - no está cerrado")
                return False

            # Actualizar estado
            success = await self.billing_repo.update_status(
                billing_id, BillingStatus.PAID, current_user_id
            )

            if success:
                logger.info(f"💰 Ciclo marcado como pagado - billing_id={billing_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error marcando ciclo como pagado: {e}")
            return False

    async def get_expired_cycles(self, current_user_id: int) -> List[ConsumptionBilling]:
        """
        Obtiene ciclos que han excedido el tiempo límite.

        Returns:
            Lista de ciclos expirados
        """
        return await self.billing_repo.get_expired_active_cycles(self.cycle_days, current_user_id)

    async def get_user_billing_history(
        self, user_id: int, current_user_id: int
    ) -> List[ConsumptionBilling]:
        """
        Obtiene el historial de ciclos de un usuario.

        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            Lista de ciclos de facturación
        """
        return await self.billing_repo.get_by_user(user_id, current_user_id)
