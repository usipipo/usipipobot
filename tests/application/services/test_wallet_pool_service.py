"""
Tests para WalletPoolService.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest

from application.services.wallet_pool_service import WalletPoolService
from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus
from infrastructure.api_clients.client_tron_dealer import BscWallet, WalletStatus


@pytest.fixture
def mock_tron_dealer_client():
    """Mock TronDealerClient."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.fixture
def mock_crypto_order_repo():
    """Mock ICryptoOrderRepository."""
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    """Mock IUserRepository."""
    return AsyncMock()


@pytest.fixture
def wallet_pool_service(mock_tron_dealer_client, mock_crypto_order_repo, mock_user_repo):
    """WalletPoolService instance with mocked dependencies."""
    return WalletPoolService(
        tron_dealer_client=mock_tron_dealer_client,
        crypto_order_repo=mock_crypto_order_repo,
        user_repo=mock_user_repo,
    )


class TestGetOrAssignWallet:
    """Tests for get_or_assign_wallet method."""

    @pytest.mark.asyncio
    async def test_reuses_user_existing_wallet(self, wallet_pool_service, mock_crypto_order_repo):
        """Should reuse wallet from user's expired order."""
        mock_crypto_order_repo.get_reusable_wallet_for_user.return_value = (
            "0x1234567890abcdef1234567890abcdef12345678"
        )

        wallet = await wallet_pool_service.get_or_assign_wallet(user_id=123456, label="test-label")

        assert wallet is not None
        assert wallet.address == "0x1234567890abcdef1234567890abcdef12345678"
        assert wallet.id == "reused"
        assert wallet.status == "active"
        mock_crypto_order_repo.get_reusable_wallet_for_user.assert_called_once_with(123456)

    @pytest.mark.asyncio
    async def test_reuses_any_expired_wallet_when_no_user_wallet(
        self, wallet_pool_service, mock_crypto_order_repo
    ):
        """Should reuse any expired wallet when user has no reusable wallet."""
        mock_crypto_order_repo.get_reusable_wallet_for_user.return_value = None
        mock_crypto_order_repo.get_any_reusable_wallet.return_value = (
            "0xabcdef1234567890abcdef1234567890abcdef12"
        )

        wallet = await wallet_pool_service.get_or_assign_wallet(user_id=123456)

        assert wallet is not None
        assert wallet.address == "0xabcdef1234567890abcdef1234567890abcdef12"
        assert wallet.id == "reused"

    @pytest.mark.asyncio
    async def test_creates_new_wallet_when_no_reusable_available(
        self, wallet_pool_service, mock_crypto_order_repo, mock_tron_dealer_client
    ):
        """Should create new wallet when no reusable wallets available."""
        mock_crypto_order_repo.get_reusable_wallet_for_user.return_value = None
        mock_crypto_order_repo.get_any_reusable_wallet.return_value = None

        new_wallet = BscWallet(
            id="new-wallet-123",
            address="0xnewwallet123456789012345678901234567890",
            label="test-user-123456",
            status=WalletStatus.ACTIVE,
        )
        mock_tron_dealer_client.assign_wallet.return_value = new_wallet

        with patch.object(
            wallet_pool_service.user_repo,
            "update_wallet_address",
            return_value=True,
        ) as mock_update:
            wallet = await wallet_pool_service.get_or_assign_wallet(
                user_id=123456, label="test-label"
            )

        assert wallet is not None
        assert wallet.id == "new-wallet-123"
        assert wallet.address == "0xnewwallet123456789012345678901234567890"
        mock_tron_dealer_client.assign_wallet.assert_called_once_with(label="test-label")

    @pytest.mark.asyncio
    async def test_returns_none_on_error(self, wallet_pool_service, mock_crypto_order_repo):
        """Should return None when an error occurs."""
        mock_crypto_order_repo.get_reusable_wallet_for_user.side_effect = Exception(
            "Database error"
        )

        wallet = await wallet_pool_service.get_or_assign_wallet(user_id=123456)

        assert wallet is None


class TestReleaseWallet:
    """Tests for release_wallet method."""

    @pytest.mark.asyncio
    async def test_releases_wallet_successfully(self, wallet_pool_service):
        """Should release wallet for reuse."""
        result = await wallet_pool_service.release_wallet(
            "0x1234567890abcdef1234567890abcdef12345678"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_handles_release_error(self, wallet_pool_service):
        """Should handle errors during wallet release."""
        # This method is mostly logging, so it should always return True
        result = await wallet_pool_service.release_wallet("invalid-address")

        assert result is True


class TestGetPoolStats:
    """Tests for get_pool_stats method."""

    @pytest.mark.asyncio
    async def test_returns_pool_statistics(self, wallet_pool_service, mock_crypto_order_repo):
        """Should return pool statistics."""
        expired_orders = [
            MagicMock(wallet_address="0x1234..."),
            MagicMock(wallet_address="0x5678..."),
            MagicMock(wallet_address="0x1234..."),  # Duplicate
        ]
        mock_crypto_order_repo.get_expired_orders_with_wallets.return_value = expired_orders

        stats = await wallet_pool_service.get_pool_stats()

        assert stats["expired_orders_count"] == 3
        assert stats["reusable_wallets_count"] == 2  # Unique addresses

    @pytest.mark.asyncio
    async def test_returns_zero_stats_on_error(self, wallet_pool_service, mock_crypto_order_repo):
        """Should return zero stats when error occurs."""
        mock_crypto_order_repo.get_expired_orders_with_wallets.side_effect = Exception(
            "Database error"
        )

        stats = await wallet_pool_service.get_pool_stats()

        assert stats["expired_orders_count"] == 0
        assert stats["reusable_wallets_count"] == 0


class TestCreateNewWallet:
    """Tests for _create_new_wallet method."""

    @pytest.mark.asyncio
    async def test_creates_and_assigns_new_wallet(
        self, wallet_pool_service, mock_tron_dealer_client
    ):
        """Should create new wallet and update user."""
        new_wallet = BscWallet(
            id="wallet-123",
            address="0xnewaddress1234567890123456789012345678",
            label="user-123456",
            status=WalletStatus.ACTIVE,
        )
        mock_tron_dealer_client.assign_wallet.return_value = new_wallet
        wallet_pool_service.user_repo.update_wallet_address.return_value = True

        wallet = await wallet_pool_service._create_new_wallet(user_id=123456, label="user-123456")

        assert wallet is not None
        assert wallet.address == "0xnewaddress1234567890123456789012345678"
        wallet_pool_service.user_repo.update_wallet_address.assert_called_once_with(
            123456, "0xnewaddress1234567890123456789012345678", current_user_id=123456
        )

    @pytest.mark.asyncio
    async def test_returns_none_when_update_fails(
        self, wallet_pool_service, mock_tron_dealer_client
    ):
        """Should return None when user update fails."""
        new_wallet = BscWallet(
            id="wallet-123",
            address="0xnewaddress1234567890123456789012345678",
            label="user-123456",
            status=WalletStatus.ACTIVE,
        )
        mock_tron_dealer_client.assign_wallet.return_value = new_wallet
        wallet_pool_service.user_repo.update_wallet_address.return_value = False

        wallet = await wallet_pool_service._create_new_wallet(user_id=123456)

        assert wallet is None

    @pytest.mark.asyncio
    async def test_handles_trondealer_api_error(self, wallet_pool_service, mock_tron_dealer_client):
        """Should handle TronDealer API errors."""
        from infrastructure.api_clients.client_tron_dealer import TronDealerApiError

        mock_tron_dealer_client.assign_wallet.side_effect = TronDealerApiError(401, "Unauthorized")

        wallet = await wallet_pool_service._create_new_wallet(user_id=123456)

        assert wallet is None
