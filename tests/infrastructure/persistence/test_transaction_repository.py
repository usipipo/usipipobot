"""
Tests para PostgresTransactionRepository.

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.balance import Balance
from infrastructure.persistence.postgresql.models import TransactionModel
from infrastructure.persistence.postgresql.transaction_repository import (
    PostgresTransactionRepository,
)


class TestPostgresTransactionRepository:
    """Tests para el repositorio de transacciones."""

    @pytest.fixture
    def mock_session(self):
        """Mock de AsyncSession para pruebas."""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Instancia del repositorio con session mock."""
        return PostgresTransactionRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_balance_with_transactions(self, repository, mock_session):
        """Test get_balance retorna el saldo de la última transacción."""
        user_id = 123456789
        expected_balance = 500

        mock_transaction = MagicMock()
        mock_transaction.balance_after = expected_balance

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_transaction
        mock_session.execute.return_value = mock_result

        balance = await repository.get_balance(user_id)

        assert isinstance(balance, Balance)
        assert balance.user_id == user_id
        assert balance.stars == expected_balance
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_balance_no_transactions(self, repository, mock_session):
        """Test get_balance retorna 0 cuando no hay transacciones."""
        user_id = 123456789

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        balance = await repository.get_balance(user_id)

        assert isinstance(balance, Balance)
        assert balance.user_id == user_id
        assert balance.stars == 0

    @pytest.mark.asyncio
    async def test_get_balance_handles_error(self, repository, mock_session):
        """Test get_balance retorna 0 cuando ocurre un error."""
        user_id = 123456789
        mock_session.execute.side_effect = Exception("Database error")

        balance = await repository.get_balance(user_id)

        assert isinstance(balance, Balance)
        assert balance.user_id == user_id
        assert balance.stars == 0

    @pytest.mark.asyncio
    async def test_get_balance_returns_most_recent(self, repository, mock_session):
        """Test get_balance retorna el saldo de la transacción más reciente."""
        user_id = 123456789
        most_recent_balance = 1000

        mock_transaction = MagicMock()
        mock_transaction.balance_after = most_recent_balance
        mock_transaction.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_transaction
        mock_session.execute.return_value = mock_result

        balance = await repository.get_balance(user_id)

        assert balance.stars == most_recent_balance
