from unittest.mock import AsyncMock, MagicMock

import pytest

from application.services.crypto_payment_service import CryptoPaymentService
from domain.entities.crypto_transaction import (
    CryptoTransaction,
    CryptoTransactionStatus,
)


class TestCryptoPaymentService:
    """Tests for CryptoPaymentService with wallet integration."""

    @pytest.fixture
    def mock_crypto_repo(self):
        """Mock crypto transaction repository."""
        repo = AsyncMock()
        repo.get_by_tx_hash.return_value = None
        repo.save.return_value = AsyncMock()
        return repo

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository with wallet support."""
        repo = AsyncMock()
        mock_user = MagicMock()
        mock_user.telegram_id = 12345
        repo.get_by_wallet_address.return_value = mock_user
        return repo

    @pytest.fixture
    def mock_order_repo(self):
        """Mock crypto order repository."""
        repo = AsyncMock()
        repo.get_by_wallet.return_value = None
        return repo

    @pytest.fixture
    def service(self, mock_crypto_repo, mock_user_repo, mock_order_repo):
        """Fixture to create CryptoPaymentService instance."""
        return CryptoPaymentService(
            crypto_repo=mock_crypto_repo,
            user_repo=mock_user_repo,
            crypto_order_repo=mock_order_repo,
        )

    @pytest.mark.asyncio
    async def test_process_webhook_payment_with_user(
        self, service, mock_crypto_repo, mock_user_repo
    ):
        """Test that webhook payment process finds user by wallet address."""
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        tx_hash = "0xabc123def456789..."
        amount = 10.5

        result = await service.process_webhook_payment(
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol="USDT",
            raw_payload={"test": "data"},
            confirmations=15,
        )

        assert result is not None
        mock_user_repo.get_by_wallet_address.assert_called_once_with(
            wallet_address, current_user_id=0
        )
        mock_crypto_repo.save.assert_called_once()

        saved_tx = mock_crypto_repo.save.call_args[0][0]
        assert isinstance(saved_tx, CryptoTransaction)
        assert saved_tx.user_id == 12345
        assert saved_tx.wallet_address == wallet_address
        assert saved_tx.amount == amount
        assert saved_tx.tx_hash == tx_hash
        assert saved_tx.token_symbol == "USDT"
        assert saved_tx.status == CryptoTransactionStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_process_webhook_payment_no_wallet_match(
        self, service, mock_crypto_repo, mock_user_repo
    ):
        """Test payment processing when no user matches the wallet address."""
        wallet_address = "0x9999999999abcdef1234567890abcdef12345678"
        tx_hash = "0xabc123def456789..."
        amount = 10.5

        mock_user_repo.get_by_wallet_address.return_value = None

        result = await service.process_webhook_payment(
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol="USDT",
            raw_payload={"test": "data"},
            confirmations=15,
        )

        assert result is not None
        mock_user_repo.get_by_wallet_address.assert_called_once_with(
            wallet_address, current_user_id=0
        )
        mock_crypto_repo.save.assert_called_once()

        saved_tx = mock_crypto_repo.save.call_args[0][0]
        assert saved_tx.user_id == 0
        assert saved_tx.status == CryptoTransactionStatus.PENDING

    @pytest.mark.asyncio
    async def test_process_webhook_payment_existing_transaction(
        self, service, mock_crypto_repo
    ):
        """Test that existing transactions are not reprocessed."""
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        tx_hash = "0xabc123def456789..."
        amount = 10.5

        existing_tx = AsyncMock()
        mock_crypto_repo.get_by_tx_hash.return_value = existing_tx

        result = await service.process_webhook_payment(
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol="USDT",
            raw_payload={"test": "data"},
            confirmations=15,
        )

        assert result == existing_tx
        mock_crypto_repo.get_by_tx_hash.assert_called_once_with(tx_hash)
        mock_crypto_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_webhook_payment_insufficient_confirmations(
        self, service, mock_crypto_repo
    ):
        """Test that payments with less than 15 confirmations are kept pending."""
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        tx_hash = "0xabc123def456789..."
        amount = 10.5

        result = await service.process_webhook_payment(
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol="USDT",
            raw_payload={"test": "data"},
            confirmations=5,
        )

        assert result is not None
        mock_crypto_repo.save.assert_called_once()
        saved_tx = mock_crypto_repo.save.call_args[0][0]
        assert saved_tx.status == CryptoTransactionStatus.PENDING
