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


@dataclass
class CancellationResult:
    """DTO para resultado de cancelación del modo consumo."""

    success: bool
    billing_id: Optional[uuid.UUID] = None
    mb_consumed: Decimal = Decimal("0")
    total_cost_usd: Decimal = Decimal("0")
    days_active: int = 0
    had_debt: bool = False
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

                    # Block all user keys
                    from application.services.consumption_vpn_integration_service import (
                        ConsumptionVpnIntegrationService,
                    )
                    from application.services.common.container import get_container

                    container = get_container()
                    if container:
                        vpn_integration = container.resolve(
                            ConsumptionVpnIntegrationService
                        )
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
                            logger.error(
                                "VPN integration service not available"
                            )
                    else:
                        logger.error("Container not available for blocking keys")
                        # Continue anyway, don't fail the billing cycle

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

    async def can_cancel_consumption(
        self, user_id: int, current_user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un usuario puede cancelar el modo consumo.

        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            Tuple de (puede_cancelar, mensaje_error)
        """
        user = await self.user_repo.get_by_id(user_id, current_user_id)
        if not user:
            return False, "Usuario no encontrado"

        # Verificar que tiene un ciclo activo (fuente de verdad principal)
        billing = await self.billing_repo.get_active_by_user(
            user_id, current_user_id
        )
        if not billing:
            return False, "No tienes un ciclo de consumo activo"

        if user.has_pending_debt:
            return (
                False,
                "Ya tienes una deuda pendiente. "
                "Debes pagarla antes de cancelar."
            )

        return True, None

    async def cancel_consumption_mode(
        self, user_id: int, current_user_id: int
    ) -> CancellationResult:
        """
        Cancela el modo consumo para un usuario, cerrando el ciclo anticipadamente.

        Args:
            user_id: ID del usuario
            current_user_id: ID del usuario actual (para auditoría)

        Returns:
            CancellationResult con éxito o error y detalles del ciclo
        """
        logger.info(f"🔄 Cancelando modo consumo para usuario {user_id}")

        try:
            # Validar que puede cancelar
            can_cancel, error_msg = await self.can_cancel_consumption(
                user_id, current_user_id
            )
            if not can_cancel:
                logger.warning(f"⚠️ No se puede cancelar modo consumo: {error_msg}")
                return CancellationResult(
                    success=False, error_message=error_msg
                )

            # Obtener ciclo activo
            billing = await self.billing_repo.get_active_by_user(
                user_id, current_user_id
            )
            if not billing or billing.id is None:
                return CancellationResult(
                    success=False,
                    error_message="No se encontró el ciclo de consumo activo"
                )

            billing_id = billing.id

            # Calcular días activos antes de cerrar
            days_active = 0
            if billing.started_at:
                delta = datetime.now(timezone.utc) - billing.started_at
                days_active = delta.days

            # Guardar datos antes de cerrar
            mb_consumed = billing.mb_consumed
            total_cost = billing.total_cost_usd

            # Determinar si hay deuda real
            has_debt = mb_consumed > 0 or total_cost > 0

            # Cerrar ciclo (misma lógica que close_billing_cycle)
            billing.close_cycle()
            success = await self.billing_repo.update_status(
                billing_id, BillingStatus.CLOSED, current_user_id
            )

            if not success:
                return CancellationResult(
                    success=False,
                    error_message="Error al cerrar el ciclo de facturación"
                )

            # Solo bloquear claves y marcar deuda si realmente hay algo que cobrar
            if has_debt:
                # Actualizar usuario como deudor
                user = await self.user_repo.get_by_id(user_id, current_user_id)
                if user:
                    user.mark_as_has_debt()
                    await self.user_repo.save(user, current_user_id)

                    # Bloquear todas las claves del usuario
                    from application.services.consumption_vpn_integration_service import (
                        ConsumptionVpnIntegrationService,
                    )
                    from application.services.common.container import get_container

                    container = get_container()
                    if container:
                        vpn_integration = container.resolve(
                            ConsumptionVpnIntegrationService
                        )
                        if vpn_integration:
                            block_result = await vpn_integration.block_user_keys(  # type: ignore
                                user_id, current_user_id
                            )

                            if not block_result["success"]:
                                logger.error(
                                    f"Failed to block keys for user {user_id}: "
                                    f"{block_result['errors']}"
                                )
                        else:
                            logger.error(
                                "VPN integration service not available"
                            )
                    else:
                        logger.error("Container not available for blocking keys")
                        # Continuar de todos modos

                logger.info(
                    f"🔒 Modo consumo cancelado con deuda - billing_id={billing_id}, "
                    f"user_id={user_id}, "
                    f"mb_consumed={mb_consumed:.2f}, "
                    f"cost=${total_cost:.2f}, "
                    f"days_active={days_active}"
                )
            else:
                # No hay deuda - solo desactivar modo consumo del usuario
                user = await self.user_repo.get_by_id(user_id, current_user_id)
                if user:
                    user.deactivate_consumption_mode()
                    await self.user_repo.save(user, current_user_id)

                logger.info(
                    f"✅ Modo consumo cancelado sin deuda - billing_id={billing_id}, "
                    f"user_id={user_id}, "
                    f"days_active={days_active}. "
                    f"Claves VPN NO bloqueadas."
                )

            return CancellationResult(
                success=True,
                billing_id=billing_id,
                mb_consumed=mb_consumed,
                total_cost_usd=total_cost,
                days_active=days_active,
                had_debt=has_debt
            )

        except Exception as e:
            logger.error(f"❌ Error cancelando modo consumo: {e}")
            return CancellationResult(
                success=False,
                error_message="Error interno al cancelar el modo consumo"
            )
