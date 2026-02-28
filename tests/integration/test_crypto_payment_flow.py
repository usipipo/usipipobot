import pytest
from unittest.mock import AsyncMock, MagicMock

from application.services.wallet_management_service import WalletManagementService
from domain.entities.user import User


@pytest.mark.asyncio
async def test_wallet_reuse_for_returning_user():
    mock_client = AsyncMock()
    mock_user_repo = AsyncMock()

    existing_user = User(telegram_id=123, wallet_address="0xExistingWallet")

    service = WalletManagementService(mock_client, mock_user_repo)

    wallet = await service.get_or_create_wallet(existing_user)

    assert wallet.address == "0xExistingWallet"
    mock_client.assign_wallet.assert_not_called()


@pytest.mark.asyncio
async def test_wallet_creation_for_new_user():
    mock_client = AsyncMock()
    mock_user_repo = AsyncMock()

    new_user = User(telegram_id=456, wallet_address=None)
    new_wallet = MagicMock(address="0xNewWallet")

    # Setup async context manager mock
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.assign_wallet.return_value = new_wallet
    mock_user_repo.update_wallet_address.return_value = True

    service = WalletManagementService(mock_client, mock_user_repo)

    wallet = await service.get_or_create_wallet(new_user)

    assert wallet.address == "0xNewWallet"
    mock_client.assign_wallet.assert_called_once_with(label="user-456")
