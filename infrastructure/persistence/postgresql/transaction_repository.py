"""
Repositorio de transacciones con SQLAlchemy Async para PostgreSQL.

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.interfaces.itransaction_repository import ITransactionRepository
from utils.logger import logger

from .base_repository import BasePostgresRepository
from .models import TransactionModel


class PostgresTransactionRepository(BasePostgresRepository, ITransactionRepository):
    """
    Implementación del repositorio de transacciones usando SQLAlchemy Async con PostgreSQL.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def record_transaction(
        self,
        user_id: int,
        transaction_type: str,
        amount: int,
        balance_after: int,
        description: str,
        reference_id: Optional[str] = None,
        telegram_payment_id: Optional[str] = None,
    ) -> None:
        try:
            transaction = TransactionModel(
                user_id=user_id,
                transaction_type=transaction_type,
                amount=amount,
                balance_after=balance_after,
                description=description,
                reference_id=reference_id,
                telegram_payment_id=telegram_payment_id,
            )
            self.session.add(transaction)
            await self.session.commit()
            logger.info(
                f"Transacción registrada: user={user_id}, type={transaction_type}, amount={amount}"
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al registrar transacción: {e}")
            raise

    async def get_user_transactions(
        self, user_id: int, limit: int = 10
    ) -> List[dict]:
        try:
            query = (
                select(TransactionModel)
                .where(TransactionModel.user_id == user_id)
                .order_by(TransactionModel.created_at.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            models = result.scalars().all()
            return [
                {
                    "id": str(m.id),
                    "user_id": m.user_id,
                    "transaction_type": m.transaction_type,
                    "amount": m.amount,
                    "balance_after": m.balance_after,
                    "description": m.description,
                    "reference_id": m.reference_id,
                    "telegram_payment_id": m.telegram_payment_id,
                    "created_at": m.created_at,
                }
                for m in models
            ]
        except Exception as e:
            logger.error(f"Error al obtener transacciones del usuario {user_id}: {e}")
            return []

    async def get_transactions_by_type(
        self, transaction_type: str, limit: int = 100
    ) -> List[dict]:
        try:
            query = (
                select(TransactionModel)
                .where(TransactionModel.transaction_type == transaction_type)
                .order_by(TransactionModel.created_at.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            models = result.scalars().all()
            return [
                {
                    "id": str(m.id),
                    "user_id": m.user_id,
                    "transaction_type": m.transaction_type,
                    "amount": m.amount,
                    "balance_after": m.balance_after,
                    "description": m.description,
                    "reference_id": m.reference_id,
                    "telegram_payment_id": m.telegram_payment_id,
                    "created_at": m.created_at,
                }
                for m in models
            ]
        except Exception as e:
            logger.error(
                f"Error al obtener transacciones de tipo {transaction_type}: {e}"
            )
            return []
