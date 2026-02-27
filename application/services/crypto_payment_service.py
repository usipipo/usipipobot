import uuid
from typing import Optional

from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus
from domain.entities.crypto_transaction import (
    CryptoTransaction,
    CryptoTransactionStatus,
)
from domain.interfaces.icrypto_order_repository import ICryptoOrderRepository
from domain.interfaces.icrypto_transaction_repository import (
    ICryptoTransactionRepository,
)
from domain.interfaces.iuser_repository import IUserRepository
from utils.logger import logger

GB_PER_USDT = 10
REQUIRED_CONFIRMATIONS = 15


class CryptoPaymentService:
    def __init__(
        self,
        crypto_repo: ICryptoTransactionRepository,
        user_repo: Optional[IUserRepository] = None,
        crypto_order_repo: Optional[ICryptoOrderRepository] = None,
    ):
        self.crypto_repo = crypto_repo
        self.user_repo = user_repo
        self.crypto_order_repo = crypto_order_repo

    async def create_order(
        self,
        user_id: int,
        package_type: str,
        amount_usdt: float,
        wallet_address: str,
    ) -> CryptoOrder:
        order = CryptoOrder(
            user_id=user_id,
            package_type=package_type,
            amount_usdt=amount_usdt,
            wallet_address=wallet_address,
            status=CryptoOrderStatus.PENDING,
        )

        if self.crypto_order_repo:
            order = await self.crypto_order_repo.save(order, current_user_id=user_id)

        logger.info(
            f"Created crypto order {order.id} for user {user_id}: "
            f"{amount_usdt} USDT to {wallet_address}"
        )

        return order

    async def process_webhook_payment(
        self,
        wallet_address: str,
        amount: float,
        tx_hash: str,
        token_symbol: str,
        raw_payload: dict,
        confirmations: int = 0,
    ) -> Optional[CryptoTransaction]:
        if confirmations < REQUIRED_CONFIRMATIONS:
            logger.info(
                f"Transaction {tx_hash} has {confirmations} confirmations, "
                f"need {REQUIRED_CONFIRMATIONS}. Keeping as pending."
            )
            existing = await self.crypto_repo.get_by_tx_hash(tx_hash)
            if existing:
                return existing
            transaction = CryptoTransaction(
                wallet_address=wallet_address,
                amount=amount,
                tx_hash=tx_hash,
                token_symbol=token_symbol,
                status=CryptoTransactionStatus.PENDING,
                raw_payload=raw_payload,
            )
            return await self.crypto_repo.save(transaction)

        existing = await self.crypto_repo.get_by_tx_hash(tx_hash)
        if existing:
            logger.info(f"Transaction already processed: {tx_hash}")
            return existing

        order = None
        if self.crypto_order_repo:
            order = await self.crypto_order_repo.get_by_wallet(wallet_address)

        user_id = await self._find_user_by_wallet(wallet_address)

        if not user_id:
            logger.warning(f"No user found for wallet: {wallet_address}")
            if order:
                await self.crypto_order_repo.mark_failed(order.id)
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

        if order:
            await self.crypto_order_repo.mark_completed(order.id, tx_hash)

        await self._credit_user(
            user_id, amount, token_symbol, order.package_type if order else "basic"
        )

        logger.info(f"Payment processed: {amount} {token_symbol} for user {user_id}")

        return saved_tx

    async def _find_user_by_wallet(self, wallet_address: str) -> Optional[int]:
        if not self.user_repo:
            logger.warning("User repository not available")
            return None

        try:
            user = await self.user_repo.get_by_wallet_address(
                wallet_address, current_user_id=0
            )
            return user.telegram_id if user else None
        except Exception as e:
            logger.error(f"Error finding user by wallet: {e}")
            return None

    async def _credit_user(
        self,
        user_id: int,
        amount: float,
        token_symbol: str,
        package_type: str = "basic",
    ) -> bool:
        if token_symbol.upper() != "USDT":
            logger.warning(f"Unsupported token: {token_symbol}")
            return False

        try:
            from application.services.common.container import get_service
            from application.services.data_package_service import DataPackageService

            data_package_service = get_service(DataPackageService)
            crypto_payment_id = f"crypto_{uuid.uuid4()}"

            # Verificar si es una orden de slots (formato: "slots_X")
            if package_type.startswith("slots_"):
                slots_str = package_type.split("_")[1]
                slots = int(slots_str)

                logger.info(f"Crediting {slots} slots to user {user_id}")

                result = await data_package_service.purchase_key_slots(
                    user_id=user_id,
                    slots=slots,
                    telegram_payment_id=crypto_payment_id,
                    current_user_id=user_id,
                )

                logger.info(
                    f"Successfully credited {slots} slots to user {user_id} via crypto payment. "
                    f"New max_keys: {result['new_max_keys']}"
                )
                return True

            # Es un paquete de datos normal
            gb_to_credit = int(amount * GB_PER_USDT)

            if gb_to_credit <= 0:
                return False

            logger.info(f"Crediting {gb_to_credit} GB to user {user_id}")

            from domain.entities.data_package import PackageType

            bytes_to_credit = gb_to_credit * 1024**3

            pkg_type = PackageType(package_type) if package_type else PackageType.BASIC

            package = await data_package_service.purchase_package(
                user_id=user_id,
                package_type=pkg_type.value,
                telegram_payment_id=crypto_payment_id,
                current_user_id=user_id,
            )

            if package.data_limit_bytes < bytes_to_credit:
                from domain.entities.data_package import DataPackage

                adjusted_package = DataPackage(
                    id=package.id,
                    user_id=user_id,
                    package_type=pkg_type,
                    data_limit_bytes=bytes_to_credit,
                    stars_paid=0,
                    expires_at=package.expires_at,
                    telegram_payment_id=crypto_payment_id,
                )
                from domain.interfaces.idata_package_repository import (
                    IDataPackageRepository,
                )

                package_repo = get_service(IDataPackageRepository)
                await package_repo.save(adjusted_package, user_id)

            logger.info(
                f"Successfully credited {gb_to_credit} GB ({bytes_to_credit} bytes) to user {user_id} via crypto payment"
            )
            return True
        except Exception as e:
            logger.error(f"Error crediting user {user_id}: {e}")
            return False

    async def get_user_orders(self, user_id: int) -> list:
        if not self.crypto_order_repo:
            return []
        return await self.crypto_order_repo.get_by_user(user_id)

    async def get_order(self, order_id: uuid.UUID) -> Optional[CryptoOrder]:
        if not self.crypto_order_repo:
            return None
        return await self.crypto_order_repo.get_by_id(order_id)

    async def get_user_transaction_history(self, user_id: int) -> list:
        """
        Obtiene el historial completo de transacciones de un usuario,
        incluyendo órdenes completadas, fallidas y expiradas.
        """
        if not self.crypto_order_repo:
            return []

        orders = await self.crypto_order_repo.get_by_user(user_id)

        history = []
        for order in orders:
            # Determinar tipo de producto
            product_name = "Paquete de datos"
            if order.package_type.startswith("slots_"):
                slots = order.package_type.split("_")[1]
                product_name = f"+{slots} claves"
            else:
                product_name = f"Paquete {order.package_type.title()}"

            history.append({
                "order_id": str(order.id),
                "product": product_name,
                "amount_usdt": order.amount_usdt,
                "status": order.status.value,
                "created_at": order.created_at,
                "expires_at": order.expires_at,
                "confirmed_at": order.confirmed_at,
                "tx_hash": order.tx_hash,
            })

        return history

    async def check_and_expire_orders(self) -> int:
        if not self.crypto_order_repo:
            return 0

        pending_orders = await self.crypto_order_repo.get_pending()
        expired_count = 0

        for order in pending_orders:
            if order.is_expired:
                await self.crypto_order_repo.mark_expired(order.id)
                expired_count += 1
                logger.info(f"Order {order.id} marked as expired")

        return expired_count
