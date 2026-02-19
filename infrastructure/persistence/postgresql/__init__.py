"""
Modulo de persistencia PostgreSQL auto-alojado.

Este modulo reemplaza completamente la integracion con Supabase,
usando SQLAlchemy 2.0 async con PostgreSQL puro.

Author: uSipipo Team
Version: 2.1.0
"""

from .base_repository import BasePostgresRepository
from .user_repository import PostgresUserRepository
from .key_repository import PostgresKeyRepository
from .data_package_repository import PostgresDataPackageRepository
from .models import Base, UserModel, VpnKeyModel, DataPackageModel

__all__ = [
    "BasePostgresRepository",
    "PostgresUserRepository",
    "PostgresKeyRepository",
    "PostgresDataPackageRepository",
    "Base",
    "UserModel",
    "VpnKeyModel",
    "DataPackageModel",
]
