"""
Servicio de gestión de claves administrativas para el bot uSipipo.

Author: uSipipo Team
Version: 1.0.0
"""

from typing import Any, Dict, List

from domain.entities.admin import AdminKeyInfo
from domain.entities.vpn_key import VpnKey as Key
from domain.interfaces.iadmin_service import IAdminKeyService
from infrastructure.api_clients.client_outline import OutlineClient
from infrastructure.api_clients.client_wireguard import WireGuardClient
from utils.logger import logger


class AdminKeyService(IAdminKeyService):
    """Servicio dedicado a la gestión de claves VPN desde el panel admin."""

    def __init__(
        self,
        key_repository,
        user_repository,
    ):
        self.key_repository = key_repository
        self.user_repository = user_repository
        self.wireguard_client = WireGuardClient()
        self.outline_client = OutlineClient()

    async def get_user_keys(self, user_id: int) -> List[Key]:
        """Obtener todas las claves de un usuario específico."""
        try:
            return await self.key_repository.get_user_keys(user_id)
        except Exception as e:
            logger.error(f"Error obteniendo claves del usuario {user_id}: {e}")
            return []

    async def get_all_keys(self, current_user_id: int) -> List[Dict]:
        """Obtener todas las claves de todos los usuarios."""
        try:
            all_keys = await self.key_repository.get_all_keys(current_user_id)

            key_list = []
            for key in all_keys:
                user = await self.user_repository.get_by_id(key.user_id, current_user_id)
                user_name = user.full_name or "Unknown" if user else "Unknown"

                usage_stats = await self.get_key_usage_stats(str(key.id))

                key_info = AdminKeyInfo(
                    key_id=str(key.id),
                    user_id=key.user_id,
                    user_name=user_name,
                    key_type=(
                        key.key_type.value if hasattr(key.key_type, "value") else str(key.key_type)
                    ),
                    key_name=key.name,
                    access_url=key.key_data,
                    created_at=key.created_at,
                    last_used=key.last_seen_at,
                    data_limit=key.data_limit_bytes,
                    data_used=usage_stats.get("data_used", 0),
                    is_active=key.is_active,
                    server_status=usage_stats.get("server_status", "unknown"),
                )
                key_list.append(key_info.__dict__)

            return key_list

        except Exception as e:
            logger.error(f"Error obteniendo todas las claves: {e}")
            return []

    async def delete_key_from_servers(self, key_id: str, key_type: str) -> bool:
        """Eliminar una clave de los servidores VPN (WireGuard y Outline)."""
        try:
            key = await self.key_repository.get_key(key_id)
            if not key:
                logger.error(f"Clave {key_id} no encontrada en BD")
                return False

            success = True

            if key_type.lower() == "wireguard":
                wg_result = await self.wireguard_client.delete_client(key.name)
                if not wg_result:
                    logger.error(f"Error eliminando clave {key_id} de WireGuard")
                    success = False
                else:
                    logger.info(f"Clave {key_id} eliminada de WireGuard")

            elif key_type.lower() == "outline":
                outline_result = await self.outline_client.delete_key(key_id)
                if not outline_result:
                    logger.error(f"Error eliminando clave {key_id} de Outline")
                    success = False
                else:
                    logger.info(f"Clave {key_id} eliminada de Outline")

            return success

        except Exception as e:
            logger.error(f"Error eliminando clave {key_id} de servidores: {e}")
            return False

    async def delete_key_from_db(self, key_id: str) -> bool:
        """Eliminar una clave de la base de datos."""
        try:
            result = await self.key_repository.delete_key(key_id)
            if result:
                logger.info(f"Clave {key_id} eliminada de la base de datos")
            else:
                logger.error(f"Error eliminando clave {key_id} de la base de datos")
            return result
        except Exception as e:
            logger.error(f"Error eliminando clave {key_id} de BD: {e}")
            return False

    async def delete_user_key_complete(self, key_id: str) -> Dict[str, Any]:
        """Eliminar completamente una clave (servidores + BD)."""
        try:
            key = await self.key_repository.get_key(key_id)
            if not key:
                return {
                    "success": False,
                    "server_deleted": False,
                    "db_deleted": False,
                    "error": "Clave no encontrada",
                }

            server_deleted = await self.delete_key_from_servers(key_id, key.key_type)
            db_deleted = await self.delete_key_from_db(key_id)

            success = server_deleted and db_deleted

            result = {
                "success": success,
                "server_deleted": server_deleted,
                "db_deleted": db_deleted,
                "key_type": key.key_type,
                "key_name": key.name,
            }

            if success:
                logger.info(f"Clave {key_id} eliminada completamente")
            else:
                logger.error(f"Error en eliminación completa de clave {key_id}: {result}")

            return result

        except Exception as e:
            logger.error(f"Error en eliminación completa de clave {key_id}: {e}")
            return {
                "success": False,
                "server_deleted": False,
                "db_deleted": False,
                "error": str(e),
            }

    async def toggle_key_status(self, key_id: str, active: bool = True) -> Dict[str, Any]:
        """Activa o desactiva una llave VPN sin eliminarla."""
        try:
            key = await self.key_repository.get_key(key_id)
            if not key:
                return {
                    "success": False,
                    "error": "Clave no encontrada",
                }

            if active:
                success = await self._reactivate_key_on_servers(key)
            else:
                success = await self._suspend_key_on_servers(key)

            if success:
                key.is_active = active
                await self.key_repository.save(key, key.user_id or 1)
                logger.info(f"Clave {key_id} {'reactivada' if active else 'suspendida'}")
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": f"Error al {'reactivar' if active else 'suspender'} en servidores",
                }

        except Exception as e:
            logger.error(f"Error al cambiar estado de clave {key_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _suspend_key_on_servers(self, key) -> bool:
        """Suspende una llave en los servidores VPN."""
        try:
            success = True
            key_type = str(key.key_type).lower() if key.key_type else ""

            if key_type == "wireguard":
                result = await self.wireguard_client.disable_peer(key.name or key.external_id)
                if not result:
                    success = False
            elif key_type == "outline":
                result = await self.outline_client.disable_key(key.id or key.external_id)
                if not result:
                    success = False

            return success
        except Exception as e:
            logger.error(f"Error suspendiendo llave en servidores: {e}")
            return False

    async def _reactivate_key_on_servers(self, key) -> bool:
        """Reactiva una llave en los servidores VPN."""
        try:
            success = True
            key_type = str(key.key_type).lower() if key.key_type else ""

            if key_type == "wireguard":
                result = await self.wireguard_client.enable_peer(key.name or key.external_id)
                if not result:
                    success = False
            elif key_type == "outline":
                result = await self.outline_client.enable_key(key.id or key.external_id)
                if not result:
                    success = False

            return success
        except Exception as e:
            logger.error(f"Error reactivando llave en servidores: {e}")
            return False

    async def get_key_usage_stats(self, key_id: str) -> Dict:
        """Obtener estadísticas de uso de una clave."""
        try:
            key = await self.key_repository.get_key(key_id)
            if not key:
                return {"data_used": 0, "server_status": "not_found"}

            data_used = 0
            server_status = "unknown"

            if key.key_type.lower() == "wireguard":
                try:
                    metrics = await self.wireguard_client.get_peer_metrics(key.external_id)
                    data_used = metrics.get("transfer_total", 0)
                    server_status = "active" if data_used > 0 else "inactive"
                except Exception as e:
                    logger.error(f"Error obteniendo métricas WireGuard para {key_id}: {e}")
                    server_status = "error"

            elif key.key_type.lower() == "outline":
                try:
                    metrics = await self.outline_client.get_key_usage(key_id)
                    data_used = metrics.get("bytes", 0)
                    server_status = "active" if data_used > 0 else "inactive"
                except Exception as e:
                    logger.error(f"Error obteniendo métricas Outline para {key_id}: {e}")
                    server_status = "error"

            return {
                "data_used": data_used,
                "server_status": server_status,
                "last_updated": __import__("datetime").datetime.now(),
            }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de uso para {key_id}: {e}")
            return {"data_used": 0, "server_status": "error"}
