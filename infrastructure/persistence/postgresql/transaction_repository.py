"""
Repositorio de transacciones con SQLAlchemy Async para PostgreSQL.

Author: uSipipo Team
Version: 2.1.0
"""

import uuid
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import logger

from domain.interfaces.itransaction_repository import ITransactionRepository
from .models import TransactionModel
from .base_repository import BasePostgresRepository


class PostgresTransactionRepository(BasePostgresRepository, ITransactionRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def record_transaction(self, user_id: int, transaction_type: str, amount: int,
                                 balance_after: int, description: str, reference_id: str = None,
                                 telegram_payment_id: str = None, current_user_id: int = None) -> uuid.UUID:
        if current_user_id is None:
            current_user_id = user_id
        await self._set_current_user(current_user_id)
        try:
            transaction_id = uuid.uuid4()
            model = TransactionModel(
                id=transaction_id, user_id=user_id, transaction_type=transaction_type,
                amount=amount, balance_after=balance_after, reference_id=reference_id,
                description=description, telegram_payment_id=telegram_payment_id,
                created_at=datetime.now(timezone.utc)
            )
            self.session.add(model)
            await self.session.commit()
            logger.info(f"Transaccion registrada: {transaction_id}")
            return transaction_id
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error al registrar transaccion: {e}")
            raise

    async def get_user_transactions(self, user_id: int, current_user_id: int) -> List[dict]:
        await self._set_current_user(current_user_id)
        try:
            query = select(TransactionModel).where(
                TransactionModel.user_id == user_id).order_by(TransactionModel.created_at.desc())
            result = await self.session.execute(query)
            return [{"id": m.id, "user_id": m.user_id, "transaction_type": m.transaction_type,
                     "amount": m.amount, "balance_after": m.balance_after, "reference_id": m.reference_id,
                     "description": m.description, "telegram_payment_id": m.telegram_payment_id,
                     "created_at": m.created_at} for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al obtener transacciones del usuario {user_id}: {e}")
            return []

    async def get_transaction_by_id(self, transaction_id: uuid.UUID, current_user_id: int) -> Optional[dict]:
        await self._set_current_user(current_user_id)
        try:
            model = await self.session.get(TransactionModel, transaction_id)
            if model is None:
                return None
            return {"id": model.id, "user_id": model.user_id, "transaction_type": model.transaction_type,
                    "amount": model.amount, "balance_after": model.balance_after, "reference_id": model.reference_id,
                    "description": model.description, "telegram_payment_id": model.telegram_payment_id,
                    "created_at": model.created_at}
        except Exception as e:
            logger.error(f"Error al obtener transaccion {transaction_id}: {e}")
            return None

    async def get_transactions_by_type(self, transaction_type: str, current_user_id: int) -> List[dict]:
        await self._set_current_user(current_user_id)
        try:
            query = select(TransactionModel).where(
                TransactionModel.transaction_type == transaction_type).order_by(TransactionModel.created_at.desc())
            result = await self.session.execute(query)
            return [{"id": m.id, "user_id": m.user_id, "transaction_type": m.transaction_type,
                     "amount": m.amount, "balance_after": m.balance_after, "reference_id": m.reference_id,
                     "description": m.description, "telegram_payment_id": m.telegram_payment_id,
                     "created_at": m.created_at} for m in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error al obtener transacciones del tipo {transaction_type}: {e}")
            return []
