from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

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

    async def block_user_keys(self, user_id: int, current_user_id: int) -> Dict[str, Any]:
        """
        Bloquea todas las claves VPN de un usuario.

        Returns:
            Dict con {"success": bool, "keys_blocked": int,
                      "keys_failed": int, "errors": list}
        """
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                return {
                    "success": False,
                    "keys_blocked": 0,
                    "keys_failed": 0,
                    "errors": ["Usuario no encontrado"],
                }

            keys = await self.key_repo.get_by_user_id(user_id, current_user_id)
            if not keys:
                logger.info(f"User {user_id} has no keys to block")
                # Still mark user as having debt
                user.mark_as_has_debt()
                await self.user_repo.save(user, current_user_id)
                return {
                    "success": True,
                    "keys_blocked": 0,
                    "keys_failed": 0,
                    "errors": [],
                }

            keys_blocked = 0
            keys_failed = 0
            errors = []

            for key in keys:
                try:
                    key_type = key.key_type.value
                    result = await self.vpn_infra_service.disable_key(str(key.id), key_type)

                    if result.get("success"):
                        keys_blocked += 1
                        logger.info(f"Key {key.id} blocked for user {user_id}")
                    else:
                        keys_failed += 1
                        err = result.get("error", "Unknown error")
                        error_msg = f"Failed to block key {key.id}: {err}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                except Exception as e:
                    keys_failed += 1
                    error_msg = f"Exception blocking key {key.id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            # Mark user as having debt
            user.mark_as_has_debt()
            await self.user_repo.save(user, current_user_id)

            return {
                "success": keys_failed == 0,
                "keys_blocked": keys_blocked,
                "keys_failed": keys_failed,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error blocking user keys for user {user_id}: {e}")
            return {
                "success": False,
                "keys_blocked": 0,
                "keys_failed": 0,
                "errors": [f"Error al bloquear claves: {str(e)}"],
            }

    async def unblock_user_keys(self, user_id: int, current_user_id: int) -> Dict[str, Any]:
        """
        Desbloquea todas las claves VPN de un usuario y limpia su deuda.

        Returns:
            Dict con {"success": bool, "keys_unblocked": int,
                      "keys_failed": int, "errors": list}
        """
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                return {
                    "success": False,
                    "keys_unblocked": 0,
                    "keys_failed": 0,
                    "errors": ["Usuario no encontrado"],
                }

            keys = await self.key_repo.get_by_user_id(user_id, current_user_id)
            if not keys:
                logger.info(f"User {user_id} has no keys to unblock")
                # Still mark debt as paid
                user.mark_debt_as_paid()
                await self.user_repo.save(user, current_user_id)
                return {
                    "success": True,
                    "keys_unblocked": 0,
                    "keys_failed": 0,
                    "errors": [],
                }

            keys_unblocked = 0
            keys_failed = 0
            errors = []

            for key in keys:
                try:
                    key_type = key.key_type.value
                    result = await self.vpn_infra_service.enable_key(str(key.id), key_type)

                    if result.get("success"):
                        keys_unblocked += 1
                        logger.info(f"Key {key.id} unblocked for user {user_id}")
                    else:
                        keys_failed += 1
                        err = result.get("error", "Unknown error")
                        error_msg = f"Failed to unblock key {key.id}: {err}"
                        errors.append(error_msg)
                        logger.warning(error_msg)
                except Exception as e:
                    keys_failed += 1
                    error_msg = f"Exception unblocking key {key.id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            # Clear user's debt flag
            user.mark_debt_as_paid()
            await self.user_repo.save(user, current_user_id)

            return {
                "success": keys_failed == 0,
                "keys_unblocked": keys_unblocked,
                "keys_failed": keys_failed,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error unblocking user keys for user {user_id}: {e}")
            return {
                "success": False,
                "keys_unblocked": 0,
                "keys_failed": 0,
                "errors": [f"Error al desbloquear claves: {str(e)}"],
            }

    async def check_can_create_key(
        self, user_id: int, current_user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Verifica si un usuario puede crear una nueva clave VPN."""
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                return False, "Usuario no encontrado"

            if user.has_pending_debt:
                return False, "El usuario tiene deuda pendiente"

            return True, None

        except Exception as e:
            logger.error(f"Error checking can_create_key for user {user_id}: {e}")
            return False, f"Error al verificar permisos: {str(e)}"

    async def route_usage_to_billing(
        self, user_id: int, mb_used: Decimal, current_user_id: int
    ) -> bool:
        """Routes data usage to billing service if user has consumption mode enabled."""
        try:
            user = await self.user_repo.get_by_id(user_id, current_user_id)
            if not user:
                logger.warning(f"User {user_id} not found for usage routing")
                return False

            if not user.consumption_mode_enabled:
                logger.debug(f"User {user_id} does not have consumption mode enabled")
                return False

            result = await self.billing_service.record_data_usage(
                user_id, float(mb_used), current_user_id
            )
            return result

        except Exception as e:
            logger.error(f"Error routing usage to billing for user {user_id}: {e}")
            return False
