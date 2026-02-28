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
        """Verifica si el usuario puede crear nuevas claves."""
        pass

    async def route_usage_to_billing(
        self, user_id: int, mb_used: float, current_user_id: int
    ) -> bool:
        """Registra consumo de datos en el ciclo de facturación activo."""
        pass
