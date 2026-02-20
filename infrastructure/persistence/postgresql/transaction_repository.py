"""
Repositorio de transacciones con SQLAlchemy Async para PostgreSQL.

Author: uSipipo Team
Version: 1.0.0
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import logger

from domain.interfaces.itransaction_repository import ITransactionRepository, Transaction
from .models import TransactionModel
from .base_repository import BasePostgresRepository


class PostgresTransactionRepository(BasePostgresRepository, ITransactionRepository):
    """Implementación del repositorio de transacciones usando SQLAlchemy Async."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def record_transaction(
        self,
        user_id: int,
        transaction_type: str,
        amount: int,
        balance_after: int,
        description: str,
        reference_id: str = None,
        telegram_payment_id: str = None
    ) -> Transaction:
        """Registra una nueva transacción."""
        try:
            model = TransactionModel(
                user_id=user_id,
                transaction_type=transaction_type,
                amount=amount,
                balance_after=balance_after,
                description=description,
                reference_id=reference_id,
                telegram_payment_id=telegram_payment_id
            )
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            
            logger.info(f"Transaction recorded: {transaction_type} for user {user_id}")
            return self._model_to_entity(model)
        except Exception as e:
            logger.error(f"Error recording transaction: {e}")
            await self.session.rollback()
            raise

    async def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """Obtiene las transacciones de un usuario."""
        try:
            query = (
                select(TransactionModel)
                .where(TransactionModel.user_id == user_id)
                .order_by(TransactionModel.created_at.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            models = result.scalars().all()
            return [self._model_to_entity(m) for m in models]
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []

    async def get_transactions_by_type(self, transaction_type: str) -> List[Dict]:
        """Obtiene transacciones por tipo."""
        try:
            query = (
                select(TransactionModel)
                .where(TransactionModel.transaction_type == transaction_type)
                .order_by(TransactionModel.created_at.desc())
            )
            result = await self.session.execute(query)
            models = result.scalars().all()
            return [
                {
                    'id': m.id,
                    'user_id': m.user_id,
                    'transaction_type': m.transaction_type,
                    'amount': m.amount,
                    'balance_after': m.balance_after,
                    'description': m.description,
                    'reference_id': m.reference_id,
                    'telegram_payment_id': m.telegram_payment_id,
                    'created_at': m.created_at
                }
                for m in models
            ]
        except Exception as e:
            logger.error(f"Error getting transactions by type: {e}")
            return []

    async def get_balance(self, user_id: int) -> Dict:
        """Obtiene el balance de un usuario (último balance registrado)."""
        try:
            query = (
                select(TransactionModel)
                .where(TransactionModel.user_id == user_id)
                .order_by(TransactionModel.created_at.desc())
                .limit(1)
            )
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            
            if model:
                return {'stars': model.balance_after}
            return {'stars': 0}
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {'stars': 0}

    def _model_to_entity(self, model: TransactionModel) -> Transaction:
        """Convierte el modelo a entidad."""
        return Transaction(
            id=model.id,
            user_id=model.user_id,
            transaction_type=model.transaction_type,
            amount=model.amount,
            balance_after=model.balance_after,
            description=model.description,
            reference_id=model.reference_id,
            telegram_payment_id=model.telegram_payment_id,
            created_at=model.created_at
        )
