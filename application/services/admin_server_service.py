"""
Servicio de gestión de servidores administrativos para el bot uSipipo.

Author: uSipipo Team
Version: 1.0.0
"""

from typing import Dict

from domain.entities.admin import ServerStatus
from domain.interfaces.iadmin_service import IAdminServerService
from infrastructure.api_clients.client_outline import OutlineClient
from infrastructure.api_clients.client_wireguard import WireGuardClient
from utils.logger import logger


class AdminServerService(IAdminServerService):
    """Servicio dedicado a la gestión de servidores VPN desde el panel admin."""

    def __init__(
        self,
        user_repository,
        key_repository,
    ):
        self.user_repository = user_repository
        self.key_repository = key_repository
        self.wireguard_client = WireGuardClient()
        self.outline_client = OutlineClient()

    async def get_server_status(self) -> Dict[str, Dict]:
        """Obtener estado de los servidores VPN."""
        try:
            status = {}

            try:
                wg_usage = await self.wireguard_client.get_usage()
                wg_status = ServerStatus(
                    server_type="wireguard",
                    is_healthy=True,
                    total_keys=len(wg_usage),
                    active_keys=len([u for u in wg_usage if u.get("total", 0) > 0]),
                    version="1.0.0",
                    uptime="Unknown",
                    error_message=None,
                )
                status["wireguard"] = wg_status.__dict__
            except Exception as e:
                wg_status = ServerStatus(
                    server_type="wireguard",
                    is_healthy=False,
                    total_keys=0,
                    active_keys=0,
                    version=None,
                    uptime=None,
                    error_message=str(e),
                )
                status["wireguard"] = wg_status.__dict__
                logger.error(f"Error obteniendo estado de WireGuard: {e}")

            try:
                outline_info = await self.outline_client.get_server_info()
                outline_status = ServerStatus(
                    server_type="outline",
                    is_healthy=outline_info.get("is_healthy", False),
                    total_keys=outline_info.get("total_keys", 0),
                    active_keys=outline_info.get("total_keys", 0),
                    version=outline_info.get("version"),
                    uptime="Unknown",
                    error_message=(
                        outline_info.get("error")
                        if not outline_info.get("is_healthy")
                        else None
                    ),
                )
                status["outline"] = outline_status.__dict__
            except Exception as e:
                outline_status = ServerStatus(
                    server_type="outline",
                    is_healthy=False,
                    total_keys=0,
                    active_keys=0,
                    version=None,
                    uptime=None,
                    error_message=str(e),
                )
                status["outline"] = outline_status.__dict__
                logger.error(f"Error obteniendo estado de Outline: {e}")

            return status

        except Exception as e:
            logger.error(f"Error obteniendo estado de servidores: {e}")
            return {}

    async def get_server_stats(self, current_user_id: int) -> Dict:
        """Obtener estadísticas del servidor para el panel admin."""
        try:
            users = await self.user_repository.get_all_users(current_user_id)
            all_keys = await self.key_repository.get_all_keys(current_user_id)
            server_status = await self.get_server_status()

            total_users = len(users)
            active_users = sum(
                1
                for u in users
                if getattr(u, "status", "").lower() == "active"
                or getattr(u, "is_active", False)
            )

            total_keys = len(all_keys)
            active_keys = sum(1 for k in all_keys if k.is_active)

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_keys": total_keys,
                "active_keys": active_keys,
                "storage_usage": "N/A",
                "cpu_usage": "N/A",
                "network_usage": "N/A",
                "server_status": server_status,
            }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del servidor: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "total_keys": 0,
                "active_keys": 0,
                "storage_usage": "N/A",
                "cpu_usage": "N/A",
                "network_usage": "N/A",
            }
