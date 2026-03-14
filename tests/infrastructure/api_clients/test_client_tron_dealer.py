from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.api_clients.client_tron_dealer import (
    BscWallet,
    TransactionResponse,
    TransactionStatus,
    TronDealerApiError,
    TronDealerClient,
    WalletBalance,
)


class TestTronDealerClient:
    """Tests for TronDealer API client."""

    @pytest.fixture
    def client(self):
        """Fixture to create TronDealerClient instance."""
        return TronDealerClient(api_key="test_api_key")

    @pytest.mark.asyncio
    async def test_assign_wallet_success(self, client, monkeypatch):
        """Test successful wallet assignment."""
        # Mock API response
        mock_response = {
            "success": True,
            "wallet": {
                "id": "d1bcd54d-7f01-4d1b-9097-e2550cec3659",
                "address": "0xbf1Ce072C22FcD4cb85Dab46BeB5ef4e5C456269",
                "label": "test-wallet",
                "status": "active",
                "created_at": "2026-02-26T00:59:01.157845+00:00",
            },
        }

        # Create mock async client
        mock_async_client = AsyncMock()

        async def mock_post(url, **kwargs):
            mock_response_obj = AsyncMock()
            mock_response_obj.json = MagicMock(return_value=mock_response)
            mock_response_obj.status_code = 201
            return mock_response_obj

        mock_async_client.post = mock_post

        # Patch the client creation
        monkeypatch.setattr(client, "_client", mock_async_client)

        # Test
        wallet = await client.assign_wallet(label="test-wallet")

        assert wallet is not None
        assert isinstance(wallet, BscWallet)
        assert wallet.address == "0xbf1Ce072C22FcD4cb85Dab46BeB5ef4e5C456269"
        assert wallet.label == "test-wallet"
        assert wallet.status == "active"
        assert wallet.id == "d1bcd54d-7f01-4d1b-9097-e2550cec3659"

    @pytest.mark.asyncio
    async def test_get_balance_success(self, client, monkeypatch):
        """Test successful balance retrieval."""
        # Mock API response
        mock_response = {
            "success": True,
            "wallet": {
                "address": "0xbf1Ce072C22FcD4cb85Dab46BeB5ef4e5C456269",
                "label": "test-wallet",
                "status": "active",
            },
            "balances": {"BNB": 0.1, "USDT": 100.50, "USDC": 50.0},
        }

        # Create mock async client
        mock_async_client = AsyncMock()

        async def mock_post(url, **kwargs):
            mock_response_obj = AsyncMock()
            mock_response_obj.json = MagicMock(return_value=mock_response)
            mock_response_obj.status_code = 200
            return mock_response_obj

        mock_async_client.post = mock_post

        # Patch the client creation
        monkeypatch.setattr(client, "_client", mock_async_client)

        # Test
        balance = await client.get_balance("0xbf1Ce072C22FcD4cb85Dab46BeB5ef4e5C456269")

        assert balance is not None
        assert isinstance(balance, WalletBalance)
        assert balance.address == "0xbf1Ce072C22FcD4cb85Dab46BeB5ef4e5C456269"
        assert balance.bnb == 0.1
        assert balance.usdt == 100.50
        assert balance.usdc == 50.0

    @pytest.mark.asyncio
    async def test_get_transactions_success(self, client, monkeypatch):
        """Test successful transactions retrieval."""
        # Mock API response
        mock_response = {
            "success": True,
            "wallet": {
                "address": "0xbf1Ce072C22FcD4cb85Dab46BeB5ef4e5C456269",
                "label": "test-wallet",
            },
            "total": 2,
            "limit": 50,
            "offset": 0,
            "transactions": [
                {
                    "tx_hash": "0xabc123...",
                    "log_index": 0,
                    "block_number": 123456,
                    "from_address": "0x1234...",
                    "to_address": "0x5678...",
                    "asset": "USDT",
                    "amount": "100.00",
                    "confirmations": 12,
                    "status": "confirmed",
                    "detected_at": "2026-02-26T01:05:44.688Z",
                    "created_at": "2026-02-26T01:05:44.688Z",
                }
            ],
        }

        # Create mock async client
        mock_async_client = AsyncMock()

        async def mock_post(url, **kwargs):
            mock_response_obj = AsyncMock()
            mock_response_obj.json = MagicMock(return_value=mock_response)
            mock_response_obj.status_code = 200
            return mock_response_obj

        mock_async_client.post = mock_post

        # Patch the client creation
        monkeypatch.setattr(client, "_client", mock_async_client)

        # Test
        transactions = await client.get_transactions("0xbf1Ce072C22FcD4cb85Dab46BeB5ef4e5C456269")

        assert transactions is not None
        assert isinstance(transactions, TransactionResponse)
        assert transactions.total == 2
        assert len(transactions.transactions) == 1
        assert transactions.transactions[0].asset == "USDT"
        assert transactions.transactions[0].status == TransactionStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_api_error(self, client, monkeypatch):
        """Test handling API errors."""
        # Mock API response
        mock_response = {"error": "Invalid API key"}

        # Create mock async client
        mock_async_client = AsyncMock()

        async def mock_post(url, **kwargs):
            mock_response_obj = AsyncMock()
            mock_response_obj.json = MagicMock(return_value=mock_response)
            mock_response_obj.status_code = 401
            return mock_response_obj

        mock_async_client.post = mock_post

        # Patch the client creation
        monkeypatch.setattr(client, "_client", mock_async_client)

        # Test
        with pytest.raises(TronDealerApiError) as exc_info:
            await client.assign_wallet()

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_request_error(self, client, monkeypatch):
        """Test handling request errors."""
        # Create mock async client that raises an exception
        mock_async_client = AsyncMock()
        mock_async_client.post.side_effect = Exception("Connection error")

        # Patch the client creation
        monkeypatch.setattr(client, "_client", mock_async_client)

        # Test
        with pytest.raises(TronDealerApiError) as exc_info:
            await client.assign_wallet()

        assert exc_info.value.status_code == 500
        assert "Unexpected error" in exc_info.value.message


class TestWalletManagementService:
    """Tests for WalletManagementService."""

    @pytest.fixture
    def mock_tron_dealer_client(self):
        """Mock TronDealerClient instance."""
        client = AsyncMock(spec=TronDealerClient)
        client.__aenter__.return_value = client
        client.__aexit__.return_value = AsyncMock()
        return client

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository."""
        repo = AsyncMock()
        repo.update_wallet_address.return_value = True
        repo.get_by_wallet_address.return_value = None
        return repo

    @pytest.fixture
    def service(self, mock_tron_dealer_client, mock_user_repo):
        """Fixture to create WalletManagementService instance."""
        from application.services.wallet_management_service import WalletManagementService

        return WalletManagementService(mock_tron_dealer_client, mock_user_repo)

    @pytest.mark.asyncio
    async def test_assign_wallet(self, service, mock_tron_dealer_client):
        """Test wallet assignment."""
        # Mock API response
        from infrastructure.api_clients.client_tron_dealer import WalletStatus

        mock_wallet = BscWallet(
            id="test-id",
            address="0x1234...",
            label="test-wallet",
            status=WalletStatus.ACTIVE,
        )
        mock_tron_dealer_client.assign_wallet.return_value = mock_wallet

        # Test
        result = await service.assign_wallet(user_id=12345)

        assert result is not None
        assert result.address == "0x1234..."
        mock_tron_dealer_client.assign_wallet.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_balance(self, service, mock_tron_dealer_client):
        """Test balance retrieval."""
        # Mock API response
        mock_balance = WalletBalance(address="0x1234...", bnb=0.1, usdt=100.50, usdc=50.0)
        mock_tron_dealer_client.get_balance.return_value = mock_balance

        # Create mock user
        mock_user = MagicMock()
        mock_user.telegram_id = 12345
        mock_user.wallet_address = "0x1234..."

        # Test
        result = await service.get_wallet_balance(mock_user)

        assert result is not None
        assert result.bnb == 0.1
        assert result.usdt == 100.50
        mock_tron_dealer_client.get_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transactions(self, service, mock_tron_dealer_client):
        """Test transactions retrieval."""
        # Mock API response
        mock_response = TransactionResponse(total=1, limit=50, offset=0, transactions=[])
        mock_tron_dealer_client.get_transactions.return_value = mock_response

        # Create mock user
        mock_user = MagicMock()
        mock_user.telegram_id = 12345
        mock_user.wallet_address = "0x1234..."

        # Test
        result = await service.get_wallet_transactions(mock_user)

        assert result is not None
        assert result.total == 1
        mock_tron_dealer_client.get_transactions.assert_called_once()
