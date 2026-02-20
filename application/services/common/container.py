"""
Contenedor de Inyección de Dependencias.

Este módulo configura todas las dependencias de la aplicación
usando el patrón de inyección de dependencias con punq.

Author: uSipipo Team
Version: 2.0.0
"""

from functools import lru_cache
from typing import Callable

import punq

from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import logger
from config import settings

from infrastructure.persistence.database import get_session_factory
from infrastructure.api_clients.client_outline import OutlineClient
from infrastructure.api_clients.client_wireguard import WireGuardClient
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from infrastructure.persistence.postgresql.key_repository import PostgresKeyRepository
from infrastructure.persistence.postgresql.data_package_repository import PostgresDataPackageRepository
from infrastructure.persistence.postgresql.transaction_repository import PostgresTransactionRepository

from domain.interfaces.iuser_repository import IUserRepository
from domain.interfaces.ikey_repository import IKeyRepository
from domain.interfaces.idata_package_repository import IDataPackageRepository
from domain.interfaces.itransaction_repository import ITransactionRepository

from application.services.vpn_service import VpnService
from application.services.payment_service import PaymentService
from application.services.admin_service import AdminService

from telegram_bot.features.vpn_keys import (
    get_vpn_keys_handler,
    get_vpn_keys_handlers,
    get_vpn_keys_callback_handlers
)
from telegram_bot.features.key_management import (
    get_key_management_handlers,
    get_key_management_callback_handlers
)
from telegram_bot.features.payments import (
    get_payments_handlers,
    get_payments_callback_handlers
)
from telegram_bot.features.operations import (
    get_operations_handlers,
    get_operations_callback_handlers
)
from telegram_bot.features.admin import (
    get_admin_handlers,
    get_admin_callback_handlers
)


class SessionManager:
    """
    Gestiona la creación de sesiones de base de datos.

    Esta clase permite obtener sesiones de forma lazy y
    compartir la misma sesión durante una operación.
    """

    def __init__(self):
        self._session: AsyncSession | None = None
        self._factory = get_session_factory()

    async def get_session(self) -> AsyncSession:
        """Obtiene o crea una sesión de base de datos."""
        if self._session is None or not self._session.is_active:
            self._session = self._factory()
        return self._session

    async def close(self):
        """Cierra la sesión actual si existe."""
        if self._session is not None:
            await self._session.close()
            self._session = None


@lru_cache()
def get_container() -> punq.Container:
    """
    Configura y retorna el contenedor de dependencias (Singleton).

    Returns:
        Container con todas las dependencias configuradas.
    """
    container = punq.Container()

    logger.debug("🔧 Configurando contenedor de dependencias...")

    _configure_database_sessions(container)
    _configure_infrastructure_clients(container)
    _configure_repositories(container)
    _configure_application_services(container)
    _configure_handlers(container)

    logger.debug("✅ Contenedor de dependencias configurado")

    return container


def _configure_database_sessions(container: punq.Container) -> None:
    """Configura las sesiones de base de datos en el contenedor."""
    session_manager = SessionManager()
    container.register(SessionManager, instance=session_manager)

    session_factory = get_session_factory()
    container.register(AsyncSession, factory=lambda: session_factory())


def _configure_infrastructure_clients(container: punq.Container) -> None:
    """Configura los clientes de infraestructura en el contenedor."""
    container.register(OutlineClient, scope=punq.Scope.singleton)
    container.register(WireGuardClient, scope=punq.Scope.singleton)


def _configure_repositories(container: punq.Container) -> None:
    """Configura los repositorios en el contenedor."""
    session_factory = get_session_factory()

    def create_user_repo() -> PostgresUserRepository:
        session = session_factory()
        return PostgresUserRepository(session)

    def create_key_repo() -> PostgresKeyRepository:
        session = session_factory()
        return PostgresKeyRepository(session)

    def create_data_package_repo() -> PostgresDataPackageRepository:
        session = session_factory()
        return PostgresDataPackageRepository(session)

    def create_transaction_repo() -> PostgresTransactionRepository:
        session = session_factory()
        return PostgresTransactionRepository(session)

    container.register(IUserRepository, factory=create_user_repo)
    container.register(IKeyRepository, factory=create_key_repo)
    container.register(IDataPackageRepository, factory=create_data_package_repo)
    container.register(ITransactionRepository, factory=create_transaction_repo)


def _configure_application_services(container: punq.Container) -> None:
    """Configura los servicios de aplicación en el contenedor."""
    session_factory = get_session_factory()

    def create_user_repo() -> PostgresUserRepository:
        session = session_factory()
        return PostgresUserRepository(session)

    def create_key_repo() -> PostgresKeyRepository:
        session = session_factory()
        return PostgresKeyRepository(session)

    def create_transaction_repo() -> PostgresTransactionRepository:
        session = session_factory()
        return PostgresTransactionRepository(session)

    def create_vpn_service() -> VpnService:
        return VpnService(
            user_repo=create_user_repo(),
            key_repo=create_key_repo(),
            outline_client=container.resolve(OutlineClient),
            wireguard_client=container.resolve(WireGuardClient)
        )

    def create_payment_service() -> PaymentService:
        return PaymentService(
            user_repo=create_user_repo(),
            transaction_repo=create_transaction_repo()
        )

    def create_admin_service() -> AdminService:
        return AdminService(
            key_repository=create_key_repo(),
            user_repository=create_user_repo(),
            payment_repository=create_transaction_repo()
        )

    container.register(VpnService, factory=create_vpn_service)
    container.register(PaymentService, factory=create_payment_service)
    container.register(AdminService, factory=create_admin_service)


def _configure_handlers(container: punq.Container) -> None:
    """Configura los handlers en el contenedor."""
    session_factory = get_session_factory()

    def create_user_repo() -> PostgresUserRepository:
        session = session_factory()
        return PostgresUserRepository(session)

    def create_key_repo() -> PostgresKeyRepository:
        session = session_factory()
        return PostgresKeyRepository(session)

    def create_transaction_repo() -> PostgresTransactionRepository:
        session = session_factory()
        return PostgresTransactionRepository(session)

    def create_vpn_service() -> VpnService:
        return VpnService(
            user_repo=create_user_repo(),
            key_repo=create_key_repo(),
            outline_client=container.resolve(OutlineClient),
            wireguard_client=container.resolve(WireGuardClient)
        )

    def create_payment_service() -> PaymentService:
        return PaymentService(
            user_repo=create_user_repo(),
            transaction_repo=create_transaction_repo()
        )

    def create_admin_service() -> AdminService:
        return AdminService(
            key_repository=create_key_repo(),
            user_repository=create_user_repo(),
            payment_repository=create_transaction_repo()
        )

    def create_creation_handlers() -> object:
        return get_vpn_keys_handler(create_vpn_service())

    def create_key_submenu_handlers() -> object:
        return get_key_management_handlers(create_vpn_service())

    def create_payment_handlers_list() -> list:
        return get_payments_handlers(
            payment_service=create_payment_service(),
            vpn_service=create_vpn_service()
        )

    def create_monitoring_handlers_list() -> list:
        return get_operations_handlers(
            vpn_service=create_vpn_service()
        )

    def create_admin_handlers() -> list:
        handlers = get_admin_handlers(create_admin_service())
        return handlers if isinstance(handlers, list) else [handlers]

    def create_inline_callback_handlers_list() -> list:
        handlers = []
        handlers.extend(get_admin_callback_handlers(create_admin_service()))
        handlers.extend(get_payments_callback_handlers(
            create_payment_service(), create_vpn_service()
        ))
        handlers.extend(get_vpn_keys_callback_handlers(create_vpn_service()))
        handlers.extend(get_key_management_callback_handlers(create_vpn_service()))
        handlers.extend(get_operations_callback_handlers(
            create_vpn_service()
        ))
        return handlers

    container.register("creation_handlers", factory=create_creation_handlers)
    container.register("key_submenu_handlers", factory=create_key_submenu_handlers)
    container.register("payment_handlers", factory=create_payment_handlers_list)
    container.register("monitoring_handlers", factory=create_monitoring_handlers_list)
    container.register("admin_handlers", factory=create_admin_handlers)
    container.register("inline_callback_handlers", factory=create_inline_callback_handlers_list)


def get_service(service_class):
    """
    Helper para obtener un servicio del contenedor.

    Args:
        service_class: Clase del servicio a resolver.

    Returns:
        Instancia del servicio configurado.
    """
    container = get_container()
    return container.resolve(service_class)
