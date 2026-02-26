from typing import Optional
import uuid

from domain.entities.crypto_transaction import (
    CryptoTransaction,
    CryptoTransactionStatus,
)
from domain.interfaces.icrypto_transaction_repository import (
    ICryptoTransactionRepository,
)
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger

GB_PER_USDT = 10


class CryptoPaymentService:
    def __init__(
        self,
        crypto_repo: ICryptoTransactionRepository,
        user_repo: Optional[IUserRepository] = None,
    ):
        self.crypto_repo = crypto_repo
        self.user_repo = user_repo

    async def process_webhook_payment(
        self,
        wallet_address: str,
        amount: float,
        tx_hash: str,
        token_symbol: str,
        raw_payload: dict,
    ) -> Optional[CryptoTransaction]:
        existing = await self.crypto_repo.get_by_tx_hash(tx_hash)
        if existing:
            logger.info(f"Transaction already processed: {tx_hash}")
            return existing

        user_id = await self._find_user_by_wallet(wallet_address)
        if not user_id:
            logger.warning(f"No user found for wallet: {wallet_address}")
            transaction = CryptoTransaction(
                wallet_address=wallet_address,
                amount=amount,
                tx_hash=tx_hash,
                token_symbol=token_symbol,
                status=CryptoTransactionStatus.PENDING,
                raw_payload=raw_payload,
            )
            return await self.crypto_repo.save(transaction)

        transaction = CryptoTransaction(
            user_id=user_id,
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol=token_symbol,
            status=CryptoTransactionStatus.CONFIRMED,
            raw_payload=raw_payload,
        )

        saved_tx = await self.crypto_repo.save(transaction)

        await self._credit_user(user_id, amount, token_symbol)

        logger.info(f"Payment processed: {amount} {token_symbol} for user {user_id}")

        return saved_tx

    async def _find_user_by_wallet(self, wallet_address: str) -> Optional[int]:
        if not self.user_repo:
            logger.warning("User repository not available")
            return None
        
        try:
            user = await self.user_repo.get_by_wallet_address(wallet_address, current_user_id=0)
            return user.telegram_id if user else None
        except Exception as e:
            logger.error(f"Error finding user by wallet: {e}")
            return None

    async def _credit_user(
        self, user_id: int, amount: float, token_symbol: str
    ) -> bool:
        if token_symbol.upper() != "USDT":
            logger.warning(f"Unsupported token: {token_symbol}")
            return False

        gb_to_credit = int(amount * GB_PER_USDT)

        if gb_to_credit <= 0:
            return False

        try:
            logger.info(f"Crediting {gb_to_credit} GB to user {user_id}")
            
            # Import here to avoid circular imports
            from application.services.data_package_service import DataPackageService
            from application.services.common.container import get_service
            from domain.entities.data_package import PackageType
            
            # Get DataPackageService from container
            data_package_service = get_service(DataPackageService)
            
            # Convert GB to bytes
            bytes_to_credit = gb_to_credit * 1024**3
            
            # Create a crypto payment package (similar to Telegram Stars purchase)
            # Use a unique payment ID for crypto transactions
            crypto_payment_id = f"crypto_{uuid.uuid4()}"
            
            # Create package with crypto payment
            package = await data_package_service.purchase_package(
                user_id=user_id,
                package_type=PackageType.BASIC.value,  # Use BASIC as base type
                telegram_payment_id=crypto_payment_id,
                current_user_id=user_id
            )
            
            # Override the data limit to match crypto payment
            if package.data_limit_bytes < bytes_to_credit:
                # Adjust the package data limit for crypto payment
                from domain.entities.data_package import DataPackage
                adjusted_package = DataPackage(
                    id=package.id,
                    user_id=user_id,
                    package_type=PackageType.BASIC,
                    data_limit_bytes=bytes_to_credit,
                    stars_paid=0,  # No stars for crypto
                    expires_at=package.expires_at,
                    telegram_payment_id=crypto_payment_id
                )
                # Update in repository
                from application.services.common.container import get_service
                from domain.interfaces.idata_package_repository import IDataPackageRepository
                package_repo = get_service(IDataPackageRepository)
                await package_repo.save(adjusted_package, user_id)
            
            logger.info(f"Successfully credited {gb_to_credit} GB ({bytes_to_credit} bytes) to user {user_id} via crypto payment")
            return True
        except Exception as e:
            logger.error(f"Error crediting user {user_id}: {e}")
            return False

    async def get_user_transactions(self, user_id: int, limit: int = 50) -> list:
        return await self.crypto_repo.get_by_user(user_id, limit)
