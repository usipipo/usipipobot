import pytest
from unittest.mock import AsyncMock, MagicMock
from application.services.vpn_service import VpnService
from domain.entities.vpn_key import VpnKey, KeyType
from domain.entities.user import User


class TestVpnKeyFlow:
    
    @pytest.fixture
    def mock_user_repo(self):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.save = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_key_repo(self):
        repo = AsyncMock()
        repo.save = AsyncMock()
        repo.get_by_user_id = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_outline_client(self):
        client = AsyncMock()
        client.create_key = AsyncMock(return_value={
            "id": "outline-key-123",
            "access_url": "ss://test@server:1234#TestKey"
        })
        return client
    
    @pytest.fixture
    def mock_wireguard_client(self):
        client = AsyncMock()
        client.create_peer = AsyncMock(return_value={
            "client_name": "wg-client-123",
            "config": "[Interface]\nPrivateKey = xxx\nAddress = 10.0.0.2/24\n"
        })
        return client
    
    @pytest.fixture
    def vpn_service(self, mock_user_repo, mock_key_repo, mock_outline_client, mock_wireguard_client):
        return VpnService(
            user_repo=mock_user_repo,
            key_repo=mock_key_repo,
            outline_client=mock_outline_client,
            wireguard_client=mock_wireguard_client
        )
    
    @pytest.mark.asyncio
    async def test_create_outline_key_success(self, vpn_service, mock_user_repo, mock_key_repo):
        """Flujo completo de creación de clave Outline."""
        telegram_id = 12345
        
        key = await vpn_service.create_key(
            telegram_id=telegram_id,
            key_type="outline",
            key_name="Mi iPhone",
            current_user_id=telegram_id
        )
        
        assert key is not None
        assert key.key_type == "outline"
        assert key.name == "Mi iPhone"
        assert key.user_id == telegram_id
        assert key.key_data.startswith("ss://")
        mock_key_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_wireguard_key_success(self, vpn_service, mock_key_repo):
        """Flujo completo de creación de clave WireGuard."""
        telegram_id = 12345
        
        key = await vpn_service.create_key(
            telegram_id=telegram_id,
            key_type="wireguard",
            key_name="Mi Laptop",
            current_user_id=telegram_id
        )
        
        assert key is not None
        assert key.key_type == "wireguard"
        assert key.name == "Mi Laptop"
        assert "[Interface]" in key.key_data
        mock_key_repo.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cannot_create_key_when_limit_reached(self, vpn_service, mock_user_repo, mock_key_repo):
        """Usuario con 2 claves no puede crear más."""
        telegram_id = 12345
        
        existing_user = User(telegram_id=telegram_id, max_keys=2)
        existing_user.keys = [
            MagicMock(is_active=True),
            MagicMock(is_active=True)
        ]
        mock_user_repo.get_by_id = AsyncMock(return_value=existing_user)
        mock_key_repo.get_by_user_id = AsyncMock(return_value=existing_user.keys)
        
        can_create, message = await vpn_service.can_user_create_key(existing_user, telegram_id)
        
        assert can_create is False
        assert "límite" in message.lower() or "limit" in message.lower()
