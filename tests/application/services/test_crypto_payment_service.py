import pytest
from unittest.mock import AsyncMock, MagicMock
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
    def service(self, mock_crypto_repo, mock_user_repo):
        """Fixture to create CryptoPaymentService instance."""
        return CryptoPaymentService(
            crypto_repo=mock_crypto_repo,
            user_repo=mock_user_repo
        )

    @pytest.mark.asyncio
    async def test_process_webhook_payment_with_user(self, service, mock_crypto_repo, mock_user_repo):
        """Test that webhook payment process finds user by wallet address."""
        # Arrange
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        tx_hash = "0xabc123..."
        amount = 10.5
        
        # Test
        result = await service.process_webhook_payment(
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol="USDT",
            raw_payload={"test": "data"}
        )
        
        # Assert
        assert result is not None
        mock_user_repo.get_by_wallet_address.assert_called_once_with(
            wallet_address, current_user_id=0
        )
        mock_crypto_repo.save.assert_called_once()
        
        # Verify the created transaction
        saved_tx = mock_crypto_repo.save.call_args[0][0]
        assert isinstance(saved_tx, CryptoTransaction)
        assert saved_tx.user_id == 12345
        assert saved_tx.wallet_address == wallet_address
        assert saved_tx.amount == amount
        assert saved_tx.tx_hash == tx_hash
        assert saved_tx.token_symbol == "USDT"
        assert saved_tx.status == CryptoTransactionStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_process_webhook_payment_no_wallet_match(self, service, mock_crypto_repo, mock_user_repo):
        """Test payment processing when no user matches the wallet address."""
        # Arrange
        wallet_address = "0x9999999999abcdef1234567890abcdef12345678"
        tx_hash = "0xabc123..."
        amount = 10.5
        
        # Mock user not found
        mock_user_repo.get_by_wallet_address.return_value = None
        
        # Test
        result = await service.process_webhook_payment(
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol="USDT",
            raw_payload={"test": "data"}
        )
        
        # Assert
        assert result is not None
        mock_user_repo.get_by_wallet_address.assert_called_once_with(
            wallet_address, current_user_id=0
        )
        mock_crypto_repo.save.assert_called_once()
        
        # Verify transaction is pending
        saved_tx = mock_crypto_repo.save.call_args[0][0]
        assert saved_tx.user_id == 0
        assert saved_tx.status == CryptoTransactionStatus.PENDING

    @pytest.mark.asyncio
    async def test_process_webhook_payment_existing_transaction(self, service, mock_crypto_repo):
        """Test that existing transactions are not reprocessed."""
        # Arrange
        wallet_address = "0x1234567890abcdef1234567890abcdef12345678"
        tx_hash = "0xabc123..."
        amount = 10.5
        
        # Mock existing transaction
        existing_tx = AsyncMock()
        mock_crypto_repo.get_by_tx_hash.return_value = existing_tx
        
        # Test
        result = await service.process_webhook_payment(
            wallet_address=wallet_address,
            amount=amount,
            tx_hash=tx_hash,
            token_symbol="USDT",
            raw_payload={"test": "data"}
        )
        
        # Assert
        assert result == existing_tx
        mock_crypto_repo.get_by_tx_hash.assert_called_once_with(tx_hash)
        mock_crypto_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_credit_user_with_usdt(self, service):
        """Test that users are credited for USDT payments."""
        # Test
        result = await service._credit_user(
            user_id=12345,
            amount=5.0,
            token_symbol="USDT"
        )
        
        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_credit_user_with_other_token(self, service):
        """Test that unsupported tokens are rejected."""
        # Test
        result = await service._credit_user(
            user_id=12345,
            amount=5.0,
            token_symbol="ETH"
        )
        
        # Assert
        assert result is False