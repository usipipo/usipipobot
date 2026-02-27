"""
Contenedor de Inyección de Dependencias.

Este módulo configura todas las dependencias de la aplicación
usando el patrón de inyección de dependencias con punq.

Author: uSipipo Team
Version: 2.0.0
"""

from functools import lru_cache
from typing import TypeVar

import punq
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

from application.services.admin_service import AdminService
from application.services.crypto_payment_service import CryptoPaymentService
from application.services.data_package_service import DataPackageService
from application.services.referral_service import ReferralService
from application.services.ticket_service import TicketService
from application.services.user_profile_service import UserProfileService
from application.services.vpn_service import VpnService
from application.services.wallet_management_service import WalletManagementService
from domain.interfaces.icrypto_order_repository import ICryptoOrderRepository
from domain.interfaces.icrypto_transaction_repository import (
    ICryptoTransactionRepository,
)
from domain.interfaces.idata_package_repository import IDataPackageRepository
from domain.interfaces.ikey_repository import IKeyRepository
from domain.interfaces.iticket_repository import ITicketRepository
from domain.interfaces.itransaction_repository import ITransactionRepository
from domain.interfaces.iuser_repository import IUserRepository
from infrastructure.api_clients.client_outline import OutlineClient
from infrastructure.api_clients.client_wireguard import WireGuardClient
from infrastructure.api_clients.client_tron_dealer import TronDealerClient
from infrastructure.persistence.database import get_session_factory
from infrastructure.persistence.postgresql.crypto_order_repository import (
    PostgresCryptoOrderRepository,
)
from infrastructure.persistence.postgresql.crypto_transaction_repository import (
    PostgresCryptoTransactionRepository,
)
from infrastructure.persistence.postgresql.data_package_repository import (
    PostgresDataPackageRepository,
)
from infrastructure.persistence.postgresql.key_repository import PostgresKeyRepository
from infrastructure.persistence.postgresql.ticket_repository import (
    PostgresTicketRepository,
)
from infrastructure.persistence.postgresql.transaction_repository import (
    PostgresTransactionRepository,
)
from infrastructure.persistence.postgresql.user_repository import PostgresUserRepository
from telegram_bot.features.admin import get_admin_callback_handlers, get_admin_handlers
from telegram_bot.features.key_management import (
    get_key_management_callback_handlers,
    get_key_management_handlers,
)
from telegram_bot.features.tickets import (
    get_ticket_callback_handlers,
    get_ticket_handlers,
)
from telegram_bot.features.vpn_keys import (
    get_vpn_keys_callback_handlers,
    get_vpn_keys_handler,
)
from utils.logger import logger


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

    def create_tron_dealer_client() -> TronDealerClient:
        return TronDealerClient()

    container.register(
        TronDealerClient, factory=create_tron_dealer_client, scope=punq.Scope.singleton
    )


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

    def create_ticket_repo() -> PostgresTicketRepository:
        session = session_factory()
        return PostgresTicketRepository(session)

    def create_crypto_order_repo() -> PostgresCryptoOrderRepository:
        session = session_factory()
        return PostgresCryptoOrderRepository(session)

    container.register(IUserRepository, factory=create_user_repo)
    container.register(IKeyRepository, factory=create_key_repo)
    container.register(IDataPackageRepository, factory=create_data_package_repo)
    container.register(ITransactionRepository, factory=create_transaction_repo)
    container.register(ITicketRepository, factory=create_ticket_repo)
    container.register(ICryptoOrderRepository, factory=create_crypto_order_repo)


def _configure_application_services(container: punq.Container) -> None:
    """Configura los servicios de aplicación en el contenedor."""
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

    def create_vpn_service() -> VpnService:
        return VpnService(
            user_repo=create_user_repo(),
            key_repo=create_key_repo(),
            outline_client=container.resolve(OutlineClient),
            wireguard_client=container.resolve(WireGuardClient),
        )

    def create_admin_service() -> AdminService:
        return AdminService(
            key_repository=create_key_repo(),
            user_repository=create_user_repo(),
            payment_repository=create_transaction_repo(),
        )

    def create_data_package_service() -> DataPackageService:
        return DataPackageService(
            package_repo=create_data_package_repo(), user_repo=create_user_repo()
        )

    def create_referral_service() -> ReferralService:
        return ReferralService(
            user_repo=create_user_repo(),
            transaction_repo=create_transaction_repo(),
        )

    def create_user_profile_service() -> UserProfileService:
        return UserProfileService(
            transaction_repo=create_transaction_repo(),
            data_package_service=container.resolve(DataPackageService),
            referral_service=container.resolve(ReferralService),
            vpn_service=container.resolve(VpnService),
        )

    def create_ticket_repo_inner() -> PostgresTicketRepository:
        session = session_factory()
        return PostgresTicketRepository(session)

    def create_ticket_service() -> TicketService:
        return TicketService(ticket_repo=create_ticket_repo_inner())

    def create_wallet_management_service() -> WalletManagementService:
        return WalletManagementService(
            tron_dealer_client=container.resolve(TronDealerClient),
            user_repo=create_user_repo(),
        )

    def create_crypto_payment_service() -> CryptoPaymentService:
        session = session_factory()
        crypto_repo = PostgresCryptoTransactionRepository(session)
        return CryptoPaymentService(
            crypto_repo=crypto_repo,
            user_repo=create_user_repo(),
            crypto_order_repo=PostgresCryptoOrderRepository(session),
        )

    container.register(VpnService, factory=create_vpn_service)
    container.register(AdminService, factory=create_admin_service)
    container.register(DataPackageService, factory=create_data_package_service)
    container.register(ReferralService, factory=create_referral_service)
    container.register(UserProfileService, factory=create_user_profile_service)
    container.register(TicketService, factory=create_ticket_service)
    container.register(
        WalletManagementService, factory=create_wallet_management_service
    )
    container.register(CryptoPaymentService, factory=create_crypto_payment_service)


def _configure_handlers(container: punq.Container) -> None:
    """Configura los handlers en el contenedor."""

    def create_creation_handlers() -> object:
        return get_vpn_keys_handler(container.resolve(VpnService))

    def create_key_submenu_handlers() -> object:
        return get_key_management_handlers(container.resolve(VpnService))

    def create_admin_handlers() -> list:
        handlers = get_admin_handlers(container.resolve(AdminService))
        return handlers if isinstance(handlers, list) else [handlers]

    def create_inline_callback_handlers_list() -> list:
        handlers = []
        handlers.extend(
            get_admin_callback_handlers(
                container.resolve(AdminService), container.resolve(TicketService)
            )
        )
        handlers.extend(get_vpn_keys_callback_handlers(container.resolve(VpnService)))
        handlers.extend(
            get_key_management_callback_handlers(container.resolve(VpnService))
        )
        handlers.extend(get_ticket_callback_handlers(container.resolve(TicketService)))
        return handlers

    container.register("creation_handlers", factory=create_creation_handlers)
    container.register("key_submenu_handlers", factory=create_key_submenu_handlers)
    container.register("admin_handlers", factory=create_admin_handlers)
    container.register(
        "inline_callback_handlers", factory=create_inline_callback_handlers_list
    )


def get_service(service_class: type[T]) -> T:
    """
    Helper para obtener un servicio del contenedor.

    Args:
        service_class: Clase del servicio a resolver.

    Returns:
        Instancia del servicio configurado.
    """
    container = get_container()
    return container.resolve(service_class)
