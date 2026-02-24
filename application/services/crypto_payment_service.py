from typing import Optional
from domain.entities.crypto_transaction import CryptoTransaction, CryptoTransactionStatus
from domain.interfaces.icrypto_transaction_repository import ICryptoTransactionRepository
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger


GB_PER_USDT = 10


class CryptoPaymentService:
    def __init__(
        self,
        crypto_repo: ICryptoTransactionRepository,
        user_repo: Optional[IUserRepository] = None
    ):
        self.crypto_repo = crypto_repo
        self.user_repo = user_repo

    async def process_webhook_payment(
        self,
        wallet_address: str,
        amount: float,
        tx_hash: str,
        token_symbol: str,
        raw_payload: dict
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
                raw_payload=raw_payload
            )
            return await self.crypto_repo.save(transaction)

        transaction = CryptoTransaction(
            user_id=user_id,
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol=token_symbol,
            status=CryptoTransactionStatus.CONFIRMED,
            raw_payload=raw_payload
        )

        saved_tx = await self.crypto_repo.save(transaction)

        await self._credit_user(user_id, amount, token_symbol)

        logger.info(f"Payment processed: {amount} {token_symbol} for user {user_id}")

        return saved_tx

    async def _find_user_by_wallet(self, wallet_address: str) -> Optional[int]:
        return None

    async def _credit_user(self, user_id: int, amount: float, token_symbol: str) -> bool:
        if token_symbol.upper() != "USDT":
            logger.warning(f"Unsupported token: {token_symbol}")
            return False

        gb_to_credit = int(amount * GB_PER_USDT)

        if gb_to_credit <= 0:
            return False

        try:
            logger.info(f"Crediting {gb_to_credit} GB to user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error crediting user: {e}")
            return False

    async def get_user_transactions(
        self,
        user_id: int,
        limit: int = 50
    ) -> list:
        return await self.crypto_repo.get_by_user(user_id, limit)
