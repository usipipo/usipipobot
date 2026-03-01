"""VpnInfrastructureService - Central service for VPN infrastructure management."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from config import settings
from domain.entities.vpn_key import KeyType, VpnKey
from domain.interfaces.ikey_repository import IKeyRepository
from domain.interfaces.iuser_repository import IUserRepository
from infrastructure.api_clients.client_outline import OutlineClient
from infrastructure.api_clients.client_wireguard import WireGuardClient
from utils.logger import logger


class VpnInfrastructureService:
    """
    Servicio central para gestión de infraestructura VPN.
    Coordina operaciones entre clientes VPN y repositorios.
    """

    def __init__(
        self,
        key_repository: IKeyRepository,
        user_repository: IUserRepository,
        wireguard_client: Optional[WireGuardClient] = None,
        outline_client: Optional[OutlineClient] = None,
    ):
        self.key_repository = key_repository
        self.user_repository = user_repository
        self.wireguard_client = wireguard_client
        self.outline_client = outline_client

    async def enable_key(self, key_id: str, key_type: str) -> Dict[str, Any]:
        """
        Habilita una clave en el servidor VPN y actualiza la base de datos.

        Args:
            key_id: ID interno de la clave (UUID)
            key_type: Tipo de clave ('wireguard' o 'outline')

        Returns:
            Dict con {"success": bool, "error": str|None}
        """
        try:
            key_uuid = uuid.UUID(key_id)
            key = await self.key_repository.get_by_id(key_uuid, settings.ADMIN_ID)

            if not key:
                logger.error(f"Key not found: {key_id}")
                return {"success": False, "error": f"Key not found: {key_id}"}

            server_success = False

            if key_type.lower() == "wireguard" and self.wireguard_client:
                server_success = await self.wireguard_client.enable_peer(
                    key.external_id
                )
            elif key_type.lower() == "outline" and self.outline_client:
                server_success = await self.outline_client.enable_key(key.external_id)
            else:
                return {"success": False, "error": f"Unsupported key type: {key_type}"}

            if server_success:
                key.is_active = True
                await self.key_repository.save(key, settings.ADMIN_ID)
                logger.info(f"Key {key_id} enabled successfully")
                return {"success": True, "error": None}
            else:
                logger.error(f"Failed to enable key {key_id} on server")
                return {"success": False, "error": "Failed to enable key on server"}

        except Exception as e:
            logger.error(f"Error enabling key {key_id}: {e}")
            return {"success": False, "error": str(e)}

    async def disable_key(self, key_id: str, key_type: str) -> Dict[str, Any]:
        """
        Deshabilita una clave en el servidor VPN y actualiza la base de datos.

        Args:
            key_id: ID interno de la clave (UUID)
            key_type: Tipo de clave ('wireguard' o 'outline')

        Returns:
            Dict con {"success": bool, "error": str|None}
        """
        try:
            key_uuid = uuid.UUID(key_id)
            key = await self.key_repository.get_by_id(key_uuid, settings.ADMIN_ID)

            if not key:
                logger.error(f"Key not found: {key_id}")
                return {"success": False, "error": f"Key not found: {key_id}"}

            server_success = False

            if key_type.lower() == "wireguard" and self.wireguard_client:
                server_success = await self.wireguard_client.disable_peer(
                    key.external_id
                )
            elif key_type.lower() == "outline" and self.outline_client:
                server_success = await self.outline_client.disable_key(key.external_id)
            else:
                return {"success": False, "error": f"Unsupported key type: {key_type}"}

            if server_success:
                key.is_active = False
                await self.key_repository.save(key, settings.ADMIN_ID)
                logger.info(f"Key {key_id} disabled successfully")
                return {"success": True, "error": None}
            else:
                logger.error(f"Failed to disable key {key_id} on server")
                return {"success": False, "error": "Failed to disable key on server"}

        except Exception as e:
            logger.error(f"Error disabling key {key_id}: {e}")
            return {"success": False, "error": str(e)}

    async def delete_key_complete(self, key_id: str, key_type: str) -> Dict[str, Any]:
        """
        Elimina una clave completamente: del servidor y de la base de datos.

        Args:
            key_id: ID interno de la clave (UUID)
            key_type: Tipo de clave ('wireguard' o 'outline')

        Returns:
            Dict con {"success": bool, "server_deleted": bool,
                     "db_deleted": bool, "error": str|None}
        """
        try:
            key_uuid = uuid.UUID(key_id)
            key = await self.key_repository.get_by_id(key_uuid, settings.ADMIN_ID)

            if not key:
                logger.error(f"Key not found: {key_id}")
                return {
                    "success": False,
                    "server_deleted": False,
                    "db_deleted": False,
                    "error": f"Key not found: {key_id}",
                }

            server_success = False

            if key_type.lower() == "wireguard" and self.wireguard_client:
                server_success = await self.wireguard_client.delete_client(
                    key.external_id
                )
            elif key_type.lower() == "outline" and self.outline_client:
                server_success = await self.outline_client.delete_key(key.external_id)
            else:
                return {
                    "success": False,
                    "server_deleted": False,
                    "db_deleted": False,
                    "error": f"Unsupported key type: {key_type}",
                }

            db_success = await self.key_repository.delete(key_uuid, settings.ADMIN_ID)

            success = server_success and db_success

            if success:
                logger.info(f"Key {key_id} deleted completely from server and database")
            else:
                logger.warning(
                    f"Partial deletion for key {key_id}: "
                    f"server={server_success}, db={db_success}"
                )

            return {
                "success": success,
                "server_deleted": server_success,
                "db_deleted": db_success,
                "error": None if success else "Partial or failed deletion",
            }

        except Exception as e:
            logger.error(f"Error deleting key {key_id}: {e}")
            return {
                "success": False,
                "server_deleted": False,
                "db_deleted": False,
                "error": str(e),
            }

    async def get_server_metrics(self, server_type: str) -> Dict[str, Any]:
        """
        Obtiene métricas de salud del servidor VPN.

        Args:
            server_type: Tipo de servidor ('wireguard' o 'outline')

        Returns:
            Dict con {"is_healthy": bool, "total_keys": int, "active_keys": int, ...}
        """
        try:
            metrics = {
                "server_type": server_type.lower(),
                "is_healthy": False,
                "total_keys": 0,
                "active_keys": 0,
            }

            if server_type.lower() == "outline" and self.outline_client:
                server_info = await self.outline_client.get_server_info()
                metrics["is_healthy"] = server_info.get("is_healthy", False)
                metrics["server_name"] = server_info.get("name", "Unknown")

            elif server_type.lower() == "wireguard":
                metrics["is_healthy"] = self.wireguard_client is not None

            all_keys = await self.key_repository.get_all_keys(settings.ADMIN_ID)
            type_keys = [k for k in all_keys if k.key_type.value == server_type.lower()]

            metrics["total_keys"] = len(type_keys)
            metrics["active_keys"] = sum(1 for k in type_keys if k.is_active)

            return metrics

        except Exception as e:
            logger.error(f"Error getting server metrics for {server_type}: {e}")
            return {
                "server_type": server_type.lower(),
                "is_healthy": False,
                "total_keys": 0,
                "active_keys": 0,
                "error": str(e),
            }

    async def cleanup_ghost_keys(self, days_inactive: int = 90) -> Dict[str, Any]:
        """
        Encuentra y deshabilita claves no usadas por N días.

        Args:
            days_inactive: Días de inactividad para considerar una clave como fantasma

        Returns:
            Dict con {"total_checked": int, "ghosts_found": int,
                     "disabled_count": int, "errors": list}
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)
            all_active_keys = await self.key_repository.get_all_active(
                settings.ADMIN_ID
            )

            total_checked = len(all_active_keys)
            ghosts_found = 0
            disabled_count = 0
            errors = []

            for key in all_active_keys:
                if self._is_ghost_key(key, cutoff_date):
                    ghosts_found += 1

                    try:
                        if key.key_type == KeyType.OUTLINE and self.outline_client:
                            success = await self.outline_client.disable_key(
                                key.external_id
                            )
                        elif (
                            key.key_type == KeyType.WIREGUARD and self.wireguard_client
                        ):
                            success = await self.wireguard_client.disable_peer(
                                key.external_id
                            )
                        else:
                            continue

                        if success:
                            key.is_active = False
                            await self.key_repository.save(key, settings.ADMIN_ID)
                            disabled_count += 1
                            logger.info(f"Ghost key {key.id} disabled")
                        else:
                            errors.append(f"Failed to disable key {key.id}")

                    except Exception as e:
                        errors.append(f"Error disabling key {key.id}: {str(e)}")

            logger.info(
                f"Ghost key cleanup completed: "
                f"checked={total_checked}, ghosts={ghosts_found}, disabled={disabled_count}"
            )

            return {
                "total_checked": total_checked,
                "ghosts_found": ghosts_found,
                "disabled_count": disabled_count,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error during ghost key cleanup: {e}")
            return {
                "total_checked": 0,
                "ghosts_found": 0,
                "disabled_count": 0,
                "errors": [str(e)],
            }

    def _is_ghost_key(self, key: VpnKey, cutoff_date: datetime) -> bool:
        """
        Determina si una clave es fantasma (no usada por mucho tiempo).

        Args:
            key: La clave VPN a evaluar
            cutoff_date: Fecha límite para considerar inactividad

        Returns:
            True si la clave es fantasma (inactiva por más tiempo que cutoff_date)
        """
        if not key.is_active:
            return False

        if key.last_seen_at is None:
            return False

        last_seen = key.last_seen_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        else:
            last_seen = last_seen.astimezone(timezone.utc)

        return last_seen < cutoff_date

    async def list_server_keys(self, server_type: str) -> List[Dict[str, Any]]:
        """
        Lista todas las claves de un tipo de servidor.

        Args:
            server_type: Tipo de servidor ('wireguard' o 'outline')

        Returns:
            Lista de dicts con {"id": str, "name": str, "is_active": bool, ...}
        """
        try:
            all_keys = await self.key_repository.get_all_keys(settings.ADMIN_ID)
            type_keys = [
                k
                for k in all_keys
                if k.key_type.value == server_type.lower() and k.is_active
            ]

            result = []
            for key in type_keys:
                result.append(
                    {
                        "id": str(key.id) if key.id else None,
                        "name": key.name,
                        "is_active": key.is_active,
                        "key_type": key.key_type.value,
                        "user_id": key.user_id,
                        "external_id": key.external_id,
                        "last_seen_at": (
                            key.last_seen_at.isoformat() if key.last_seen_at else None
                        ),
                        "used_bytes": key.used_bytes,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error listing server keys for {server_type}: {e}")
            return []
