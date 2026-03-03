"""
Interfaz del servicio de administración para el bot uSipipo.

Author: uSipipo Team
Version: 2.0.0
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from domain.entities.admin import AdminOperationResult
from domain.entities.vpn_key import VpnKey as Key


class IAdminStatsService(ABC):
    """Interfaz para servicio de estadísticas administrativas."""

    @abstractmethod
    async def get_dashboard_stats(self, current_user_id: int) -> Dict:
        """Genera estadísticas completas para el panel de control administrativo."""
        pass


class IAdminUserService(ABC):
    """Interfaz para servicio de gestión de usuarios administrativos."""

    @abstractmethod
    async def get_all_users(self, current_user_id: int) -> List[Dict]:
        """Obtener lista de todos los usuarios registrados."""
        pass

    @abstractmethod
    async def get_users_paginated(
        self, page: int, per_page: int, current_user_id: int
    ) -> Dict:
        """Obtener usuarios paginados."""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Obtener información detallada de un usuario."""
        pass

    @abstractmethod
    async def update_user_status(
        self, user_id: int, status: str
    ) -> AdminOperationResult:
        """Actualizar estado del usuario."""
        pass

    @abstractmethod
    async def delete_user(self, user_id: int, **kwargs) -> AdminOperationResult:
        """Eliminar un usuario y sus claves asociadas."""
        pass

    @abstractmethod
    async def assign_role_to_user(
        self, user_id: int, role: str, duration_days: Optional[int] = None
    ) -> AdminOperationResult:
        """Asignar rol a un usuario."""
        pass

    @abstractmethod
    async def block_user(self, user_id: int) -> AdminOperationResult:
        """Bloquear un usuario."""
        pass

    @abstractmethod
    async def unblock_user(self, user_id: int) -> AdminOperationResult:
        """Desbloquear un usuario."""
        pass


class IAdminKeyService(ABC):
    """Interfaz para servicio de gestión de claves administrativas."""

    @abstractmethod
    async def get_user_keys(self, user_id: int) -> List[Key]:
        """Obtener todas las claves de un usuario específico."""
        pass

    @abstractmethod
    async def get_all_keys(self, current_user_id: int) -> List[Dict]:
        """Obtener todas las claves de todos los usuarios."""
        pass

    @abstractmethod
    async def delete_key_from_servers(self, key_id: str, key_type: str) -> bool:
        """Eliminar una clave de los servidores VPN (WireGuard y Outline)."""
        pass

    @abstractmethod
    async def delete_key_from_db(self, key_id: str) -> bool:
        """Eliminar una clave de la base de datos."""
        pass

    @abstractmethod
    async def delete_user_key_complete(self, key_id: str) -> Dict[str, Any]:
        """Eliminar completamente una clave (servidores + BD)."""
        pass

    @abstractmethod
    async def toggle_key_status(self, key_id: str, active: bool) -> Dict:
        """Activar o desactivar una clave VPN."""
        pass

    @abstractmethod
    async def get_key_usage_stats(self, key_id: str) -> Dict:
        """Obtener estadísticas de uso de una clave."""
        pass


class IAdminServerService(ABC):
    """Interfaz para servicio de gestión de servidores administrativos."""

    @abstractmethod
    async def get_server_status(self) -> Dict[str, Dict]:
        """Obtener estado de los servidores VPN."""
        pass

    @abstractmethod
    async def get_server_stats(self, current_user_id: int) -> Dict:
        """Obtener estadísticas del servidor para el panel admin."""
        pass


class IAdminService(
    IAdminStatsService,
    IAdminUserService,
    IAdminKeyService,
    IAdminServerService,
):
    """
    Interfaz combinada del servicio de administración.
    
    Mantiene compatibilidad hacia atrás con código existente.
    Las nuevas implementaciones deben usar las interfaces especializadas.
    """
    pass
