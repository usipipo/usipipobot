from typing import Protocol, List, Optional
from domain.entities.data_package import DataPackage
import uuid


class IDataPackageRepository(Protocol):
    """
    Contrato para la persistencia de paquetes de datos.
    Define cómo interactuamos con la tabla de paquetes en la BD.
    """

    async def save(self, data_package: DataPackage, current_user_id: int) -> DataPackage:
        """Guarda un nuevo paquete de datos o actualiza uno existente."""
        ...

    async def get_by_id(self, package_id: uuid.UUID, current_user_id: int) -> Optional[DataPackage]:
        """Busca un paquete específico por su ID."""
        ...

    async def get_by_user(self, telegram_id: int, current_user_id: int) -> List[DataPackage]:
        """Recupera todos los paquetes de un usuario."""
        ...

    async def get_active_by_user(self, telegram_id: int, current_user_id: int) -> List[DataPackage]:
        """Recupera solo los paquetes activos de un usuario."""
        ...

    async def get_valid_by_user(self, telegram_id: int, current_user_id: int) -> List[DataPackage]:
        """Recupera los paquetes activos y no expirados de un usuario."""
        ...

    async def update_usage(self, package_id: uuid.UUID, bytes_used: int, current_user_id: int) -> bool:
        """Actualiza el uso de datos de un paquete."""
        ...

    async def deactivate(self, package_id: uuid.UUID, current_user_id: int) -> bool:
        """Desactiva un paquete."""
        ...

    async def delete(self, package_id: uuid.UUID, current_user_id: int) -> bool:
        """Elimina un paquete de la base de datos."""
        ...

    async def get_expired_packages(self, current_user_id: int) -> List[DataPackage]:
        """Recupera todos los paquetes activos que han expirado."""
        ...
