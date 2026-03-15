"""
Servicio de administración para el bot uSipipo (Facade).

⚠️ DEPRECATED: Este servicio se mantiene por compatibilidad.
Usar los servicios especializados:
- AdminStatsService
- AdminUserService
- AdminKeyService
- AdminServerService

Author: uSipipo Team
Version: 2.0.0
"""

from typing import Any, Dict, List, Optional

from domain.entities.admin import AdminOperationResult
from domain.entities.vpn_key import VpnKey as Key
from domain.interfaces.iadmin_service import IAdminService
from domain.interfaces.iticket_repository import ITicketRepository

from .admin_key_service import AdminKeyService
from .admin_server_service import AdminServerService
from .admin_stats_service import AdminStatsService
from .admin_user_service import AdminUserService


class AdminService(IAdminService):
    """
    Implementación del servicio de administración (Facade).

    Delega operaciones a servicios especializados para mantener
    SRP (Single Responsibility Principle).
    """

    def __init__(
        self,
        key_repository,
        user_repository,
        payment_repository,
        ticket_repo: ITicketRepository | None = None,
    ):
        self._stats_service = AdminStatsService(user_repository, key_repository, payment_repository)
        self._user_service = AdminUserService(user_repository, key_repository, payment_repository)
        self._key_service = AdminKeyService(key_repository, user_repository)
        self._server_service = AdminServerService(user_repository, key_repository)
        self.ticket_repo = ticket_repo

    # ============================================
    # DELEGACIÓN A AdminStatsService
    # ============================================

    async def get_dashboard_stats(self, current_user_id: int) -> Dict:
        """Genera estadísticas completas para el panel de control administrativo."""
        return await self._stats_service.get_dashboard_stats(current_user_id)

    # ============================================
    # DELEGACIÓN A AdminUserService
    # ============================================

    async def get_all_users(self, current_user_id: int) -> List[Dict]:
        """Obtener lista de todos los usuarios registrados."""
        return await self._user_service.get_all_users(current_user_id)

    async def get_users_paginated(
        self, page: int = 1, per_page: int = 10, current_user_id: int | None = None
    ) -> Dict:
        """Obtener usuarios paginados."""
        return await self._user_service.get_users_paginated(page, per_page, current_user_id)

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Obtener información detallada de un usuario."""
        return await self._user_service.get_user_by_id(user_id)

    async def update_user_status(self, user_id: int, status: str) -> AdminOperationResult:
        """Actualizar estado del usuario (ACTIVE, SUSPENDED, BLOCKED)."""
        return await self._user_service.update_user_status(user_id, status)

    async def assign_role_to_user(
        self, user_id: int, role: str, duration_days: Optional[int] = None
    ) -> AdminOperationResult:
        """Asignar rol a un usuario."""
        return await self._user_service.assign_role_to_user(user_id, role, duration_days)

    async def block_user(self, user_id: int) -> AdminOperationResult:
        """Bloquear un usuario."""
        return await self._user_service.block_user(user_id)

    async def unblock_user(self, user_id: int) -> AdminOperationResult:
        """Desbloquear un usuario."""
        return await self._user_service.unblock_user(user_id)

    async def delete_user(self, user_id: int) -> AdminOperationResult:
        """Eliminar un usuario y sus claves asociadas."""
        return await self._user_service.delete_user(user_id, self._key_service)

    # ============================================
    # DELEGACIÓN A AdminKeyService
    # ============================================

    async def get_user_keys(self, user_id: int) -> List[Key]:
        """Obtener todas las claves de un usuario específico."""
        return await self._key_service.get_user_keys(user_id)

    async def get_all_keys(self, current_user_id: int) -> List[Dict]:
        """Obtener todas las claves de todos los usuarios."""
        return await self._key_service.get_all_keys(current_user_id)

    async def delete_key_from_servers(self, key_id: str, key_type: str) -> bool:
        """Eliminar una clave de los servidores VPN (WireGuard y Outline)."""
        return await self._key_service.delete_key_from_servers(key_id, key_type)

    async def delete_key_from_db(self, key_id: str) -> bool:
        """Eliminar una clave de la base de datos."""
        return await self._key_service.delete_key_from_db(key_id)

    async def delete_user_key_complete(self, key_id: str) -> Dict[str, Any]:
        """Eliminar completamente una clave (servidores + BD)."""
        return await self._key_service.delete_user_key_complete(key_id)

    async def toggle_key_status(self, key_id: str, active: bool = True) -> Dict[str, Any]:
        """Activa o desactiva una llave VPN sin eliminarla."""
        return await self._key_service.toggle_key_status(key_id, active)

    async def get_key_usage_stats(self, key_id: str) -> Dict:
        """Obtener estadísticas de uso de una clave."""
        return await self._key_service.get_key_usage_stats(key_id)

    # ============================================
    # DELEGACIÓN A AdminServerService
    # ============================================

    async def get_server_status(self) -> Dict[str, Dict]:
        """Obtener estado de los servidores VPN."""
        return await self._server_service.get_server_status()

    async def get_server_stats(self, current_user_id: int) -> Dict:
        """Obtener estadísticas del servidor para el panel admin."""
        return await self._server_service.get_server_stats(current_user_id)
