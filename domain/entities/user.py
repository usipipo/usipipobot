import uuid
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
    wallet_address: Optional[str] = None

    keys: List = field(default_factory=list)

    free_data_limit_bytes: int = 5 * 1024**3
    free_data_used_bytes: int = 0

    # Bonus tracking fields
    purchase_count: int = 0
    loyalty_bonus_percent: int = 0
    welcome_bonus_used: bool = False
    referred_users_with_purchase: int = 0  # Track referrals who bought

    @property
    def is_active(self) -> bool:
        """Verifica si el usuario está activo."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_blocked(self) -> bool:
        """Verifica si el usuario está bloqueado."""
        return self.status == UserStatus.BLOCKED

    def get_key_count_by_type(self, key_type: str) -> int:
        """
        Cuenta las claves activas de un tipo específico.
        """
        active_keys = [
            k
            for k in self.keys
            if getattr(k, "is_active", True)
            and getattr(k, "key_type", None) == key_type
        ]
        return len(active_keys)

    def can_create_key_type(self, key_type: str) -> bool:
        """
        Lógica de negocio: Verifica si el usuario puede crear una clave
        del tipo especificado. Solo permite 1 clave por tipo de servidor.
        Los administradores pueden crear ilimitadas.
        """
        if self.role == UserRole.ADMIN:
            return True

        # Verificar límite total de claves
        active_keys = [k for k in self.keys if getattr(k, "is_active", True)]
        if len(active_keys) >= self.max_keys:
            return False

        # Verificar que no tenga ya una clave del mismo tipo
        existing_of_type = self.get_key_count_by_type(key_type)
        return existing_of_type == 0

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

    # Consumption billing fields
    consumption_mode_enabled: bool = False
    has_pending_debt: bool = False
    current_billing_id: Optional[uuid.UUID] = None
    consumption_mode_activated_at: Optional[datetime] = None

    @property
    def is_consumption_mode_active(self) -> bool:
        """Verifica si el usuario tiene el modo consumo activo."""
        return self.consumption_mode_enabled

    @property
    def can_activate_consumption_mode(self) -> bool:
        """
        Verifica si el usuario puede activar el modo consumo.
        No puede activar si tiene deuda pendiente o ya tiene modo activo.
        """
        if self.has_pending_debt:
            return False
        if self.consumption_mode_enabled:
            return False
        return True

    def activate_consumption_mode(self, billing_id: uuid.UUID) -> None:
        """
        Activa el modo consumo para el usuario.

        Args:
            billing_id: ID del ciclo de facturación asociado
        """
        if not self.can_activate_consumption_mode:
            raise ValueError("El usuario no puede activar el modo consumo")

        self.consumption_mode_enabled = True
        self.current_billing_id = billing_id
        self.consumption_mode_activated_at = datetime.now(timezone.utc)

    def deactivate_consumption_mode(self) -> None:
        """Desactiva el modo consumo del usuario."""
        self.consumption_mode_enabled = False
        self.current_billing_id = None
        self.consumption_mode_activated_at = None

    def mark_debt_as_paid(self) -> None:
        """Marca la deuda del usuario como pagada."""
        self.has_pending_debt = False

    def mark_as_has_debt(self) -> None:
        """Marca al usuario como teniendo deuda pendiente."""
        self.has_pending_debt = True

    def __repr__(self):
        return f"<User(id={self.telegram_id}, username={self.username}, status={self.status})>"
