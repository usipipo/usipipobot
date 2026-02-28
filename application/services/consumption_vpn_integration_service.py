from typing import Any, Dict, List, Optional, Tuple

from application.services.consumption_billing_service import ConsumptionBillingService
from application.services.vpn_infrastructure_service import VpnInfrastructureService
from domain.interfaces.ikey_repository import IKeyRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


class ConsumptionVpnIntegrationService:
    """Servicio de integración entre modo consumo e infraestructura VPN."""

    def __init__(
        self,
        user_repo: IUserRepository,
        key_repo: IKeyRepository,
        vpn_infra_service: VpnInfrastructureService,
        billing_service: ConsumptionBillingService,
    ):
        self.user_repo = user_repo
        self.key_repo = key_repo
        self.vpn_infra_service = vpn_infra_service
        self.billing_service = billing_service

    async def block_user_keys(
        self, user_id: int, current_user_id: int
    ) -> Dict[str, Any]:
        """Bloquea todas las claves VPN de un usuario."""
        pass

    async def unblock_user_keys(
        self, user_id: int, current_user_id: int
    ) -> Dict[str, Any]:
        """Desbloquea todas las claves VPN de un usuario."""
        pass

    async def check_can_create_key(
        self, user_id: int, current_user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si el usuario puede crear nuevas claves.

        Returns:
            Tuple[bool, Optional[str]]: (puede_crear, mensaje_error)
        """
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)

            if not user:
                return False, "Usuario no encontrado"

            if user.has_pending_debt:
                return (
                    False,
                    "Tienes una deuda pendiente. Debes pagar antes de crear nuevas claves.",
                )

            return True, None

        except Exception as e:
            logger.error(f"Error checking can_create_key for user {user_id}: {e}")
            return False, f"Error al verificar permisos: {str(e)}"
