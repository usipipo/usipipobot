from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class UserStatus(str, Enum):
    """Estados posibles de un usuario en el sistema."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class UserRole(str, Enum):
    """Roles disponibles en el sistema."""

    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    """
    Entidad fundamental que representa a un usuario del bot/API.

    Esta clase es pura: no depende de ninguna base de datos ni librería externa.
    """

    telegram_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    role: UserRole = UserRole.USER
    max_keys: int = 2
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    referral_code: Optional[str] = None
    referred_by: Optional[int] = None
    referral_credits: int = 0

    keys: List = field(default_factory=list)

    free_data_limit_bytes: int = 10 * 1024**3
    free_data_used_bytes: int = 0

    @property
    def is_active(self) -> bool:
        """Verifica si el usuario está activo."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_blocked(self) -> bool:
        """Verifica si el usuario está bloqueado."""
        return self.status == UserStatus.BLOCKED

    def can_create_more_keys(self) -> bool:
        """
        Lógica de negocio: Verifica si el usuario tiene permiso
        para generar una nueva llave según su límite.
        Los administradores pueden crear ilimitadas.
        """
        if self.role == UserRole.ADMIN:
            return True

        active_keys = [k for k in self.keys if getattr(k, "is_active", True)]
        return len(active_keys) < self.max_keys

    def can_delete_keys(self) -> bool:
        """
        Lógica de negocio: Usuarios con créditos pueden eliminar claves.
        Los administradores pueden eliminar sin restricciones.
        """
        if self.role == UserRole.ADMIN:
            return True

        return self.referral_credits > 0

    @property
    def free_data_remaining_bytes(self) -> int:
        """Calcula los bytes restantes de datos gratuitos."""
        return max(0, self.free_data_limit_bytes - self.free_data_used_bytes)

    def add_free_data_usage(self, bytes_used: int) -> None:
        """Agrega uso a los datos gratuitos."""
        self.free_data_used_bytes += bytes_used

    def __repr__(self):
        return f"<User(id={self.telegram_id}, username={self.username}, status={self.status})>"
