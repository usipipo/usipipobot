"""
Wallet Pool Service - Gestión de reutilización de wallets.

Este servicio implementa un pool de wallets reutilizables para evitar
crear wallets innecesarias cuando las órdenes expiran.
"""

from typing import Optional

from domain.interfaces.icrypto_order_repository import ICryptoOrderRepository
from domain.interfaces.iuser_repository import IUserRepository
from infrastructure.api_clients.client_tron_dealer import (
    BscWallet,
    TronDealerApiError,
    TronDealerClient,
    WalletStatus,
)
from utils.logger import logger


class WalletPoolService:
    """
    Servicio para gestionar un pool de wallets reutilizables.

    Estrategia:
    1. Primero busca wallets expiradas del mismo usuario
    2. Si no hay, busca cualquier wallet expirada no en uso
    3. Si no hay disponibles, crea una nueva wallet
    """

    def __init__(
        self,
        tron_dealer_client: TronDealerClient,
        crypto_order_repo: ICryptoOrderRepository,
        user_repo: IUserRepository,
    ):
        self.tron_dealer_client = tron_dealer_client
        self.crypto_order_repo = crypto_order_repo
        self.user_repo = user_repo

    async def get_or_assign_wallet(
        self, user_id: int, label: Optional[str] = None
    ) -> Optional[BscWallet]:
        """
        Obtiene una wallet para el usuario, reutilizando si es posible.

        Args:
            user_id: Telegram user ID
            label: Optional wallet label

        Returns:
            BscWallet: Wallet existente reutilizada o nueva
        """
        try:
            # Paso 1: Buscar wallet reutilizable del mismo usuario
            existing_wallet = await self.crypto_order_repo.get_reusable_wallet_for_user(
                user_id
            )

            if existing_wallet:
                logger.info(
                    f"Reutilizando wallet {existing_wallet[:10]}... "
                    f"de orden expirada para usuario {user_id}"
                )
                return BscWallet(
                    id="reused",
                    address=existing_wallet,
                    label=label or f"user-{user_id}",
                    status=WalletStatus.ACTIVE,
                )

            # Paso 2: Buscar cualquier wallet expirada no en uso
            any_reusable = await self.crypto_order_repo.get_any_reusable_wallet()

            if any_reusable:
                logger.info(
                    f"Reutilizando wallet {any_reusable[:10]}... "
                    f"de pool general para usuario {user_id}"
                )
                return BscWallet(
                    id="reused",
                    address=any_reusable,
                    label=label or f"user-{user_id}",
                    status=WalletStatus.ACTIVE,
                )

            # Paso 3: Crear nueva wallet si no hay reutilizables
            logger.info(
                f"No hay wallets reutilizables, creando nueva para user {user_id}"
            )
            return await self._create_new_wallet(user_id, label)

        except Exception as e:
            logger.error(f"Error en get_or_assign_wallet para user {user_id}: {e}")
            return None

    async def _create_new_wallet(
        self, user_id: int, label: Optional[str] = None
    ) -> Optional[BscWallet]:
        """Crea una nueva wallet para el usuario."""
        try:
            async with self.tron_dealer_client as client:
                wallet = await client.assign_wallet(label=label)

            logger.info(
                f"Nueva wallet {wallet.address[:10]}... " f"creada para user {user_id}"
            )

            # Actualizar dirección del usuario
            success = await self.user_repo.update_wallet_address(
                user_id, wallet.address, current_user_id=user_id
            )

            if not success:
                logger.error(f"Falló actualización de wallet para user {user_id}")
                return None

            return wallet

        except TronDealerApiError as e:
            if e.status_code == 401:
                logger.error("TronDealer API auth failed: API key inválida")
            else:
                logger.error(f"TronDealer API error {e.status_code}: {e.message}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado creando wallet para user {user_id}: {e}")
            return None

    async def release_wallet(self, wallet_address: str) -> bool:
        """
        Libera una wallet para reutilización.

        Args:
            wallet_address: Dirección de la wallet a liberar

        Returns:
            bool: True si se liberó correctamente
        """
        try:
            logger.info(f"Liberando wallet {wallet_address[:10]}... para reutilización")
            # La wallet se marca como reutilizable automáticamente
            # cuando la orden asociada está en estado 'expired'
            return True
        except Exception as e:
            logger.error(f"Error liberando wallet {wallet_address}: {e}")
            return False

    async def get_pool_stats(self) -> dict:
        """
        Obtiene estadísticas del pool de wallets.

        Returns:
            dict: Estadísticas del pool
        """
        try:
            expired_orders = (
                await self.crypto_order_repo.get_expired_orders_with_wallets(limit=1000)
            )

            unique_wallets = set(order.wallet_address for order in expired_orders)

            return {
                "expired_orders_count": len(expired_orders),
                "reusable_wallets_count": len(unique_wallets),
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del pool: {e}")
            return {"expired_orders_count": 0, "reusable_wallets_count": 0}
