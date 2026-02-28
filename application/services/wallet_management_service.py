from typing import List, Optional

from domain.entities.user import User
from domain.interfaces.icrypto_order_repository import ICryptoOrderRepository
from domain.interfaces.iuser_repository import IUserRepository
from infrastructure.api_clients.client_tron_dealer import (
    BscWallet,
    TransactionResponse,
    TransactionStatus,
    TronDealerApiError,
    TronDealerClient,
    WalletBalance,
    WalletStatus,
)
from utils.logger import logger


class WalletManagementService:
    """
    Service for managing BSC wallet operations via TronDealer API.

    Ahora incluye soporte para reutilización de wallets mediante
    el WalletPoolService integrado.
    """

    def __init__(
        self,
        tron_dealer_client: TronDealerClient,
        user_repo: IUserRepository,
        crypto_order_repo: Optional[ICryptoOrderRepository] = None,
    ):
        self.tron_dealer_client = tron_dealer_client
        self.user_repo = user_repo
        self.crypto_order_repo = crypto_order_repo
        self.crypto_order_repo = crypto_order_repo

    async def assign_wallet(
        self, user_id: int, label: Optional[str] = None
    ) -> Optional[BscWallet]:
        """
        Assign a BSC wallet to a user and update their profile.

        Intenta reutilizar wallets de órdenes expiradas antes de crear una nueva.

        Args:
            user_id: Telegram user ID
            label: Optional wallet label

        Returns:
            BscWallet: Reused or newly created wallet, or None if failed
        """
        try:
            logger.info(f"Assigning BSC wallet to user {user_id}")

            # Intentar reutilizar wallet del pool primero
            if self.crypto_order_repo:
                reused_wallet = await self._try_reuse_wallet(user_id, label)
                if reused_wallet:
                    logger.info(
                        f"Reutilizando wallet {reused_wallet.address[:10]}... "
                        f"para usuario {user_id}"
                    )
                    # Actualizar dirección del usuario
                    await self.user_repo.update_wallet_address(
                        user_id, reused_wallet.address, current_user_id=user_id
                    )
                    return reused_wallet

            # Crear nueva wallet si no hay reutilizables
            async with self.tron_dealer_client as client:
                wallet = await client.assign_wallet(label=label)

            logger.info(f"Nueva wallet {wallet.address[:10]}... creada para user {user_id}")

            # Update user's wallet address
            success = await self.user_repo.update_wallet_address(
                user_id, wallet.address, current_user_id=user_id
            )

            if not success:
                logger.error(f"Failed to update user {user_id} with wallet address")
                return None

            return wallet

        except TronDealerApiError as e:
            if e.status_code == 401:
                logger.error(f"TronDealer API authentication failed for user {user_id}: API key not configured or invalid")
            else:
                logger.error(f"TronDealer API error {e.status_code} assigning wallet to user {user_id}: {e.message}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error assigning wallet to user {user_id}: {e}", exc_info=True)
            return None

    async def _try_reuse_wallet(
        self, user_id: int, label: Optional[str] = None
    ) -> Optional[BscWallet]:
        """
        Intenta reutilizar una wallet de una orden expirada.

        Args:
            user_id: Telegram user ID
            label: Optional wallet label

        Returns:
            BscWallet: Wallet reutilizable o None
        """
        if not self.crypto_order_repo:
            return None

        # Primero buscar wallet del mismo usuario
        existing_wallet = await self.crypto_order_repo.get_reusable_wallet_for_user(
            user_id
        )

        if existing_wallet:
            return BscWallet(
                id="reused",
                address=existing_wallet,
                label=label or f"user-{user_id}",
                status=WalletStatus.ACTIVE,
            )

        # Luego buscar cualquier wallet expirada no en uso
        any_reusable = await self.crypto_order_repo.get_any_reusable_wallet()

        if any_reusable:
            return BscWallet(
                id="reused",
                address=any_reusable,
                label=label or f"user-{user_id}",
                status=WalletStatus.ACTIVE,
            )

        return None

    async def get_wallet_balance(self, user: User) -> Optional[WalletBalance]:
        """
        Get the current balance of a user's wallet.

        Args:
            user: User entity

        Returns:
            WalletBalance: Wallet with balances or None if failed
        """
        if not user.wallet_address:
            logger.warning(f"User {user.telegram_id} has no wallet address")
            return None

        try:
            async with self.tron_dealer_client as client:
                balance = await client.get_balance(user.wallet_address)

            logger.debug(
                f"Wallet {user.wallet_address} balance: "
                f"BNB={balance.bnb}, USDT={balance.usdt}, USDC={balance.usdc}"
            )

            return balance

        except TronDealerApiError as e:
            logger.error(f"TronDealer API error getting balance: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting balance for user {user.telegram_id}: {e}")
            return None

    async def get_wallet_transactions(
        self,
        user: User,
        limit: int = 50,
        offset: int = 0,
        status: Optional[TransactionStatus] = None,
    ) -> Optional[TransactionResponse]:
        """
        Get the transaction history of a user's wallet.

        Args:
            user: User entity
            limit: Number of transactions per page
            offset: Number of records to skip
            status: Optional status filter

        Returns:
            TransactionResponse: Paginated transactions or None if failed
        """
        if not user.wallet_address:
            logger.warning(f"User {user.telegram_id} has no wallet address")
            return None

        try:
            async with self.tron_dealer_client as client:
                transactions = await client.get_transactions(
                    user.wallet_address, limit=limit, offset=offset, status=status
                )

            logger.debug(
                f"Found {transactions.total} transactions for wallet {user.wallet_address}"
            )

            return transactions

        except TronDealerApiError as e:
            logger.error(f"TronDealer API error getting transactions: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting transactions for user {user.telegram_id}: {e}")
            return None

    async def get_or_create_wallet(self, user: User) -> Optional[BscWallet]:
        """
        Get existing wallet or create a new one if user doesn't have one.

        Args:
            user: User entity

        Returns:
            BscWallet: Wallet instance
        """
        if user.wallet_address:
            # TODO: Verify existing wallet is valid
            logger.debug(
                f"User {user.telegram_id} already has wallet {user.wallet_address}"
            )
            # For now, return a minimal wallet object with existing address
            from infrastructure.api_clients.client_tron_dealer import WalletStatus

            return BscWallet(
                id="existing",
                address=user.wallet_address,
                label=f"user-{user.telegram_id}",
                status=WalletStatus.ACTIVE,
            )

        return await self.assign_wallet(
            user.telegram_id, label=f"user-{user.telegram_id}"
        )
