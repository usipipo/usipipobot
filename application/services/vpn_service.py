"""Module for VPN service operations."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from config import settings
from domain.entities.user import User, UserRole
from domain.entities.vpn_key import KeyType, VpnKey
from domain.interfaces.idata_package_repository import IDataPackageRepository
from domain.interfaces.ikey_repository import IKeyRepository
from domain.interfaces.iuser_repository import IUserRepository
from infrastructure.api_clients.client_outline import OutlineClient
from infrastructure.api_clients.client_wireguard import WireGuardClient
from utils.logger import logger


class VpnService:
    """Service for managing VPN keys and user operations."""

    def __init__(
        self,
        user_repo: IUserRepository,
        key_repo: IKeyRepository,
        package_repo: IDataPackageRepository,
        outline_client: OutlineClient,
        wireguard_client: WireGuardClient,
        vpn_integration_service=None,
    ):
        self.user_repo = user_repo
        self.key_repo = key_repo
        self.package_repo = package_repo
        self.outline_client = outline_client
        self.wireguard_client = wireguard_client
        self.vpn_integration_service = vpn_integration_service

    async def create_key(
        self, telegram_id: int, key_type: str, key_name: str, current_user_id: int
    ) -> VpnKey:
        """Orquesta la creación de una llave VPN."""
        logger.info(
            f"🔑 Iniciando creación de llave {key_type} para usuario {telegram_id}"
        )
        user = await self.user_repo.get_by_id(telegram_id, current_user_id)
        if not user:
            user = User(telegram_id=telegram_id)
            await self.user_repo.save(user, current_user_id)

        # Check for pending debt
        if self.vpn_integration_service is not None:
            can_create, error_msg = (
                await self.vpn_integration_service.check_can_create_key(
                    telegram_id, current_user_id
                )
            )
            if not can_create:
                raise ValueError(error_msg)

        # Verificar si el usuario puede crear más llaves (incluye regla para admins)
        if not user.can_create_more_keys():
            if user.role == UserRole.ADMIN:
                raise ValueError(
                    "Error inesperado: los administradores deberían poder crear ilimitadas"
                )
            raise ValueError(f"Límite de llaves alcanzado ({user.max_keys})")

        # Verificar que no tenga ya una clave del mismo tipo
        if not user.can_create_key_type(key_type.lower()):
            raise ValueError(
                f"Ya tienes una clave {key_type.title()}. Solo se permite una clave por tipo de servidor."
            )

        if key_type.lower() == "outline":
            infra_data = await self.outline_client.create_key(key_name)
            access_data = infra_data["access_url"]
            external_id = infra_data["id"]
        elif key_type.lower() == "wireguard":
            infra_data = await self.wireguard_client.create_peer(telegram_id, key_name)
            access_data = infra_data["config"]
            # create_peer devuelve 'client_name' en su diccionario de respuesta
            external_id = infra_data["client_name"]
        else:
            raise ValueError("Tipo de llave no soportado")

        # Determinar límite de datos según plan
        data_limit_bytes = self._get_user_data_limit(user)

        new_key = VpnKey(
            id=str(uuid.uuid4()),
            user_id=telegram_id,
            key_type=KeyType(key_type.lower()),
            name=key_name,
            key_data=access_data,
            external_id=external_id,
            data_limit_bytes=data_limit_bytes,
            billing_reset_at=datetime.now(timezone.utc),
        )
        await self.key_repo.save(new_key, current_user_id)

        logger.info(
            f"🔑 Llave creada exitosamente - Tipo: {key_type}, ID: {new_key.id}, Usuario: {telegram_id}, Nombre: '{key_name}'"
        )
        return new_key

    async def get_all_active_keys(self) -> List[VpnKey]:
        """Obtiene todas las llaves activas de todos los usuarios para sincronizar."""
        return await self.key_repo.get_all_active(settings.ADMIN_ID)

    async def fetch_real_usage(self, key: VpnKey) -> int:
        """Abstrae la consulta de consumo según el tipo de llave."""
        try:
            if key.key_type == "outline":
                metrics = await self.outline_client.get_metrics()
                return metrics.get(str(key.external_id), 0)

            if key.key_type == "wireguard":
                peer_data = await self.wireguard_client.get_peer_metrics(
                    key.external_id
                )
                return peer_data.get("transfer_total", 0)

            return 0
        except Exception as e:
            logger.error(f"Error consultando métricas reales para llave {key.id}: {e}")
            return 0

    async def update_key_usage(self, key_id: uuid.UUID, used_bytes: int):
        """Persiste el consumo actualizado en la base de datos."""
        # For usage updates, we need to determine the user. Since this is called from jobs/sync,
        # it might be admin, but let's get the key first to know the user
        key = await self.key_repo.get_by_id(
            key_id, settings.ADMIN_ID
        )  # Use admin to get the key
        if key and key.user_id is not None:
            await self.key_repo.update_usage(key_id, used_bytes, key.user_id)
        else:
            # Fallback to admin if key not found or no user_id
            await self.key_repo.update_usage(key_id, used_bytes, settings.ADMIN_ID)

    def _get_user_data_limit(self, user: User) -> int:
        """Retorna el límite de datos en bytes según el plan del usuario."""
        return settings.FREE_PLAN_DATA_LIMIT_GB * (1024**3)

    async def can_user_create_key(
        self, user: User, current_user_id: int, key_type: Optional[str] = None
    ) -> tuple[bool, str]:
        """Verifica si el usuario puede crear una nueva llave."""
        logger.debug(
            f"🔍 Verificando si usuario {user.telegram_id} puede crear llave (tipo: {key_type or 'any'})"
        )
        keys = await self.key_repo.get_by_user_id(user.telegram_id, current_user_id)
        if len(keys) >= user.max_keys:
            return False, f"Has alcanzado el límite de {user.max_keys} llaves."

        # Verificar que no tenga ya una clave del mismo tipo
        if key_type:
            existing_of_type = [
                k for k in keys if k.key_type.value == key_type.lower() and k.is_active
            ]
            if existing_of_type:
                return (
                    False,
                    f"Ya tienes una clave {key_type.title()}. Solo se permite una clave por tipo de servidor.",
                )

        result = True, ""
        logger.debug(f"✅ Usuario {user.telegram_id} puede crear llave: {result[0]}")
        return result

    async def get_user_status(self, telegram_id: int, current_user_id: int) -> dict:
        """Obtiene un resumen del estado del usuario y sus llaves."""
        logger.debug(f"📊 Consultando estado de usuario {telegram_id}")
        user = await self.user_repo.get_by_id(telegram_id, current_user_id)
        keys = await self.key_repo.get_by_user_id(telegram_id, current_user_id)

        # Calcular consumo total de llaves
        total_used_bytes = sum(k.used_bytes for k in keys)
        keys_data_limit = sum(k.data_limit_bytes for k in keys)

        # Obtener paquetes de datos activos y sumar sus límites
        packages = await self.package_repo.get_valid_by_user(
            telegram_id, current_user_id
        )
        packages_data_limit = sum(p.data_limit_bytes for p in packages)
        packages_used_bytes = sum(p.data_used_bytes for p in packages)

        # Límite total = llaves + paquetes comprados (Opción B)
        total_data_limit = keys_data_limit + packages_data_limit
        total_used_including_packages = total_used_bytes + packages_used_bytes

        return {
            "user": user,
            "keys_count": len(keys),
            "keys": keys,
            "total_used_gb": total_used_including_packages / (1024**3),
            "total_limit_gb": total_data_limit / (1024**3),
            "remaining_gb": max(0, total_data_limit - total_used_including_packages)
            / (1024**3),
            "keys_limit_gb": keys_data_limit / (1024**3),
            "packages_limit_gb": packages_data_limit / (1024**3),
        }

    async def check_and_reset_billing_cycle(self, key: VpnKey) -> bool:
        """Verifica si el ciclo de facturación debe resetearse y lo hace si es necesario."""
        if key.needs_reset():
            if key.id is None or key.user_id is None:
                return False
            await self.key_repo.reset_data_usage(uuid.UUID(key.id), key.user_id)
            return True
        return False

    async def get_user_keys(
        self, telegram_id: int, current_user_id: int
    ) -> List[VpnKey]:
        """Obtiene todas las llaves activas de un usuario."""
        keys = await self.key_repo.get_by_user_id(telegram_id, current_user_id)
        logger.debug(f"🔑 Usuario {telegram_id} tiene {len(keys)} llave(s)")
        return keys

    async def revoke_key(self, key_id: uuid.UUID, current_user_id: int) -> bool:
        """Elimina una llave de la infraestructura y la marca como inactiva en BD."""
        key = await self.key_repo.get_by_id(key_id, current_user_id)
        if not key:
            logger.warning(f"Intentando revocar llave inexistente: {key_id}")
            return False

        # Verificar si el usuario puede eliminar (tiene créditos)
        key_user_id = key.user_id
        if key_user_id is None:
            raise ValueError("La llave no tiene usuario asignado.")
        user = await self.user_repo.get_by_id(key_user_id, current_user_id)
        if not user or not user.can_delete_keys():
            raise ValueError("Necesitas tener créditos para eliminar claves.")

        try:
            # 1. Eliminar de la infraestructura real
            if key.key_type == KeyType.OUTLINE:
                await self.outline_client.delete_key(key.external_id)
            if key.key_type == KeyType.WIREGUARD:
                await self.wireguard_client.delete_client(key.external_id)

            # 2. Marcar como inactiva en Repositorio (Soft Delete)
            return await self.key_repo.delete(key_id, current_user_id)

        except Exception as e:
            logger.error(f"❌ Error al revocar llave {key_id}: {e}")
            return False

    async def rename_key(
        self, key_id: str, new_name: str, current_user_id: int
    ) -> bool:
        """Renombra una llave VPN."""
        try:
            key_uuid = uuid.UUID(key_id)

            key = await self.key_repo.get_by_id(key_uuid, current_user_id)
            if not key:
                logger.warning(f"Intentando renombrar llave inexistente: {key_id}")
                return False

            old_name = key.name
            key.name = new_name
            await self.key_repo.save(key, current_user_id)

            logger.info(
                f"🏷️ Llave renombrada - ID: {key_id}, Usuario: {key.user_id}, '{old_name}' → '{new_name}'"
            )
            return True

        except (Exception, ValueError) as e:
            logger.error(f"❌ Error al renombrar llave {key_id}: {e}")
            return False

    async def get_wireguard_config(self, key_id: str, current_user_id: int) -> dict:
        """Obtiene la configuración de WireGuard de una llave."""
        try:
            key_uuid = uuid.UUID(key_id)

            key = await self.key_repo.get_by_id(key_uuid, current_user_id)
            if not key or key.key_type != "wireguard":
                return {"config_string": "Configuración no disponible"}

            return {"config_string": key.key_data, "external_id": key.external_id}

        except (Exception, ValueError) as e:
            logger.error(f"Error obteniendo configuración WireGuard para {key_id}: {e}")
            return {"config_string": "Error al obtener configuración"}

    async def get_outline_config(self, key_id: str, current_user_id: int) -> dict:
        """Obtiene la configuración de Outline de una llave."""
        try:
            key_uuid = uuid.UUID(key_id)

            key = await self.key_repo.get_by_id(key_uuid, current_user_id)
            if not key or key.key_type != "outline":
                return {"access_url": "Configuración no disponible"}

            return {"access_url": key.key_data, "external_id": key.external_id}

        except (Exception, ValueError) as e:
            logger.error(f"Error obteniendo configuración Outline para {key_id}: {e}")
            return {"access_url": "Error al obtener configuración"}

    async def get_server_status(self, server_type: str) -> dict:
        """
        Obtiene información de estado del servidor (ubicación, ping, carga).
        Centraliza la obtención de métricas para ser consumidas por los handlers.
        """
        try:
            # Valores por defecto
            location = "Miami, USA"  # Podría moverse a configuración
            ping = 45
            load = 0

            if server_type.lower() == "outline":
                # Intentar obtener carga real de Outline
                try:
                    info = await self.outline_client.get_server_info()
                    # Usamos el conteo de llaves como proxy de carga si no hay métrica de CPU
                    # Normalizamos a un porcentaje (ej: 100 llaves = 100% carga es un ejemplo simple)
                    key_count = info.get("total_keys", 0)
                    load = min(key_count, 100)
                    if info.get("is_healthy"):
                        ping = 35  # Si está healthy asumimos buen ping
                except Exception as e:
                    logger.warning(f"No se pudo obtener estado real de Outline: {e}")

            elif server_type.lower() == "wireguard":
                # Intentar obtener carga real de WireGuard
                try:
                    usage = await self.wireguard_client.get_usage()
                    # Proxy de carga: número de peers activos
                    active_peers = len(usage)
                    load = min(
                        active_peers * 2, 100
                    )  # Asumimos 50 usuarios = 100% carga
                except Exception as e:
                    logger.warning(f"No se pudo obtener estado real de WireGuard: {e}")

            return {"location": location, "ping": ping, "load": load}
        except Exception as e:
            logger.error(
                f"Error general obteniendo estado de servidor {server_type}: {e}"
            )
            return {"location": "Desconocida", "ping": 0, "load": 0}

    async def get_key_by_id(
        self, key_id: str, current_user_id: int
    ) -> Optional[VpnKey]:
        """Obtiene una llave por su ID."""
        try:
            key_uuid = uuid.UUID(key_id)
            return await self.key_repo.get_by_id(key_uuid, current_user_id)
        except (Exception, ValueError) as e:
            logger.error(f"Error obteniendo llave por ID {key_id}: {e}")
            return None

    async def update_key(self, key: VpnKey, current_user_id: int) -> bool:
        """Actualiza una llave en la base de datos."""
        try:
            await self.key_repo.save(key, current_user_id)
            logger.info(
                f"📝 Llave actualizada - ID: {key.id}, Usuario: {key.user_id}, Tipo: {key.key_type}, Activa: {key.is_active}"
            )
            return True
        except Exception as e:
            logger.error(f"Error actualizando llave {key.id}: {e}")
            return False

    async def delete_key(self, key_id: str, current_user_id: int) -> bool:
        """Elimina una llave (usa revoke_key para consistencia)."""
        logger.warning(
            f"⚠️ ELIMINANDO LLAVE PERMANENTEMENTE - ID: {key_id}, Usuario solicitante: {current_user_id}"
        )
        try:
            key_uuid = uuid.UUID(key_id)
            result = await self.revoke_key(key_uuid, current_user_id)
            if result:
                logger.warning(f"✅ Llave {key_id} eliminada permanentemente")
            return result
        except (Exception, ValueError) as e:
            logger.error(f"Error eliminando llave {key_id}: {e}")
            raise

    async def deactivate_inactive_key(
        self, key_id: uuid.UUID, current_user_id: int
    ) -> bool:
        """Desactiva una llave por inactividad (soft delete)."""
        try:
            key = await self.key_repo.get_by_id(key_id, current_user_id)
            if not key:
                return False
            key.is_active = False
            await self.key_repo.save(key, current_user_id)
            return True
        except Exception as e:
            logger.error(f"Error al desactivar llave {key_id}: {e}")
            return False

    async def sync_usage(self, current_user_id: int) -> dict:
        """Sincroniza el consumo de datos de todas las llaves activas."""
        logger.info("🔄 Iniciando sincronización de consumo de datos VPN")

        keys = await self.get_all_active_keys()
        synced_count = 0
        error_count = 0
        total_bytes_synced = 0

        for key in keys:
            try:
                current_usage = await self.fetch_real_usage(key)
                if key.id is not None:
                    await self.update_key_usage(uuid.UUID(key.id), current_usage)
                    synced_count += 1
                    total_bytes_synced += current_usage
                else:
                    logger.warning(f"⚠️ Llave sin ID, omitiendo: {key.name}")
                    error_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error sincronizando llave {key.id}: {e}")

        summary = {
            "total_keys": len(keys),
            "synced": synced_count,
            "errors": error_count,
            "total_bytes_synced": total_bytes_synced,
        }
        logger.info(
            f"✅ Sincronización completada - Total: {summary['total_keys']}, "
            f"Exitosas: {summary['synced']}, Errores: {summary['errors']}, "
            f"Bytes sincronizados: {summary['total_bytes_synced']}"
        )
        return summary
