from typing import Any, Dict, List, Optional, Protocol

from domain.entities.user import User


class IUserRepository(Protocol):
    """
    Este es el 'contrato' para el manejo de usuarios.
    Cualquier base de datos que usemos (Supabase, SQL, etc.)
    DEBE cumplir con estos métodos.
    """

    async def get_by_id(self, telegram_id: int, current_user_id: int) -> Optional[User]:
        """Busca un usuario por su ID de Telegram."""
        ...

    async def save(self, user: User, current_user_id: int) -> User:
        """Guarda un usuario nuevo o actualiza uno existente."""
        ...

    async def exists(self, telegram_id: int, current_user_id: int) -> bool:
        """Verifica si el usuario ya está registrado."""
        ...

    async def get_by_referral_code(
        self, referral_code: str, current_user_id: int
    ) -> Optional[User]:
        """Busca un usuario por su código de referido."""
        ...

    async def get_referrals_by_user(
        self, telegram_id: int, current_user_id: int
    ) -> List[User]:
        """Obtiene la lista de usuarios referidos por un usuario."""
        ...

    async def get_referrals(self, referrer_id: int, current_user_id: int) -> List[Dict[str, Any]]:
        """Obtiene todos los usuarios referidos por este usuario como lista de dicts."""
        ...

    async def get_user(self, telegram_id: int, current_user_id: int) -> Optional[User]:
        """Busca un usuario por su ID de Telegram (alias de get_by_id)."""
        ...

    async def create_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        referral_code: Optional[str] = None,
        referred_by: Optional[int] = None,
        current_user_id: Optional[int] = None,
    ) -> User:
        """Crea un nuevo usuario."""
        ...

    async def get_all_users(self, current_user_id: int) -> List[User]:
        """Obtiene todos los usuarios registrados."""
        ...
