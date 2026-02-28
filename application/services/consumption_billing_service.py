import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from config import settings
from domain.entities.consumption_billing import BillingStatus, ConsumptionBilling
from domain.interfaces.iconsumption_billing_repository import (
    IConsumptionBillingRepository,
)
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


@dataclass
class ConsumptionSummary:
    """DTO para resumen de consumo actual."""

    billing_id: Optional[uuid.UUID]
    mb_consumed: Decimal
    gb_consumed: Decimal
    total_cost_usd: Decimal
    days_active: int
    is_active: bool
    formatted_cost: str
    formatted_consumption: str


@dataclass
class ActivationResult:
    """DTO para resultado de activación del modo consumo."""

    success: bool
    billing_id: Optional[uuid.UUID] = None
    error_message: Optional[str] = None


class ConsumptionBillingService:
    """
    Servicio de aplicación para gestionar ciclos de facturación por consumo.

    Responsabilidades:
    - Activar modo consumo para usuarios
    - Registrar consumo de datos
    - Cerrar ciclos de facturación
    - Consultar estado de consumo
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

    async def can_activate_consumption(
        self, user_id: int, current_user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un usuario puede activar el modo consumo.

        Returns:
            Tuple de (puede_activar, mensaje_error)
        """
        user = await self.user_repo.get_by_id(user_id, current_user_id)
        if not user:
            return False, "Usuario no encontrado"

        if user.has_pending_debt:
            return False, (
                "Tienes una deuda pendiente. "
                "Debes pagarla antes de activar el modo consumo."
            )

        if user.consumption_mode_enabled:
            return False, "Ya tienes el modo consumo activo"

        # Verificar si ya tiene un ciclo activo
        existing_billing = await self.billing_repo.get_active_by_user(
            user_id, current_user_id
        )
        if existing_billing:
            return False, "Ya tienes un ciclo de consumo activo"

        return True, None

    async def activate_consumption_mode(
        self, user_id: int, current_user_id: int
    ) -> ActivationResult:
        """
        Activa el modo consumo para un usuario.

        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            ActivationResult con éxito o error
        """
        logger.info(f"🔄 Activando modo consumo para usuario {user_id}")

        try:
            # Validar que puede activar
            can_activate, error_msg = await self.can_activate_consumption(
                user_id, current_user_id
            )
            if not can_activate:
                logger.warning(f"⚠️ No se puede activar modo consumo: {error_msg}")
                return ActivationResult(success=False, error_message=error_msg)

            # Crear nuevo ciclo de facturación
            billing = ConsumptionBilling(
                user_id=user_id,
                started_at=datetime.now(timezone.utc),
                status=BillingStatus.ACTIVE,
                price_per_mb_usd=self.price_per_mb,
            )

            saved_billing = await self.billing_repo.save(billing, current_user_id)

            # Verificar que el billing tiene ID
            if saved_billing.id is None:
                return ActivationResult(
                    success=False,
                    error_message="Error al crear el ciclo de facturación"
                )

            billing_id = saved_billing.id  # type: ignore  # ya verificamos que no es None

            # Actualizar usuario
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if user:
                user.activate_consumption_mode(billing_id)
                await self.user_repo.save(user, current_user_id)

            logger.info(
                f"✅ Modo consumo activado - user_id={user_id}, "
                f"billing_id={saved_billing.id}"
            )

            return ActivationResult(
                success=True,
                billing_id=saved_billing.id
            )

        except Exception as e:
            logger.error(f"❌ Error activando modo consumo: {e}")
            return ActivationResult(
                success=False,
                error_message="Error interno al activar el modo consumo"
            )

    async def record_data_usage(
        self,
        user_id: int,
        mb_used: float,
        current_user_id: int
    ) -> bool:
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
            billing = await self.billing_repo.get_active_by_user(
                user_id, current_user_id
            )

            if not billing or billing.id is None:
                logger.debug(f"Usuario {user_id} no tiene ciclo de consumo activo")
                return False

            # Agregar consumo
            success = await self.billing_repo.add_consumption(
                billing.id, mb_used, current_user_id
            )

            if success:
                logger.debug(
                    f"📊 Consumo registrado - user_id={user_id}, "
                    f"mb_used={mb_used:.2f}"
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
            billing = await self.billing_repo.get_active_by_user(
                user_id, current_user_id
            )

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

    async def close_billing_cycle(
        self,
        billing_id: uuid.UUID,
        current_user_id: int
    ) -> bool:
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

                logger.info(
                    f"🔒 Ciclo cerrado - billing_id={billing_id}, "
                    f"user_id={billing.user_id}, "
                    f"cost=${billing.total_cost_usd:.2f}"
                )

            return success

        except Exception as e:
            logger.error(f"❌ Error cerrando ciclo: {e}")
            return False

    async def mark_cycle_as_paid(
        self,
        billing_id: uuid.UUID,
        current_user_id: int
    ) -> bool:
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

    async def get_expired_cycles(
        self,
        current_user_id: int
    ) -> List[ConsumptionBilling]:
        """
        Obtiene ciclos que han excedido el tiempo límite.

        Returns:
            Lista de ciclos expirados
        """
        return await self.billing_repo.get_expired_active_cycles(
            self.cycle_days, current_user_id
        )

    async def get_user_billing_history(
        self,
        user_id: int,
        current_user_id: int
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
