import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, CallbackQuery, User, Chat

from application.services.data_package_service import DataPackageService
from telegram_bot.features.buy_gb.handlers_buy_gb import BuyGbHandler


class TestBuyGbHandler:
    """Tests for BuyGbHandler crypto payment functionality."""

    @pytest.fixture
    def data_package_service(self):
        """Mock DataPackageService."""
        return AsyncMock(spec=DataPackageService)

    @pytest.fixture
    def handler(self, data_package_service):
        """Create BuyGbHandler instance."""
        return BuyGbHandler(data_package_service)

    @pytest.fixture
    def mock_update(self):
        """Create mock Update with callback query."""
        update = MagicMock(spec=Update)
        query = MagicMock(spec=CallbackQuery)
        user = MagicMock(spec=User)
        chat = MagicMock(spec=Chat)
        
        user.id = 12345
        chat.id = 12345
        query.data = "select_payment_basic"
        query.from_user = user
        query.message = MagicMock()
        query.message.chat = chat
        
        update.callback_query = query
        update.effective_user = user
        update.effective_chat = chat
        
        return update

    @pytest.mark.asyncio
    async def test_select_payment_method_valid_package(self, handler, mock_update, data_package_service):
        """Test selecting payment method for valid package."""
        # Setup
        mock_update.callback_query.data = "select_payment_basic"
        context = MagicMock()
        
        # Mock the edit_message_text method
        mock_update.callback_query.edit_message_text = AsyncMock()
        
        # Execute
        await handler.select_payment_method(mock_update, context)
        
        # Verify
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_update.callback_query.edit_message_text.call_args
        message = call_args[1]['text']
        
        assert "Seleccionar Método de Pago" in message
        assert "Básico" in message
        assert "10 GB" in message
        assert "50 ⭐" in message
        assert "1.00 USDT" in message

    @pytest.mark.asyncio
    async def test_pay_with_crypto_success(self, handler, mock_update):
        """Test successful crypto payment initiation."""
        from unittest.mock import patch
        
        # Mock the wallet assignment
        with patch('application.services.common.container.get_service') as mock_get_service:
            wallet_service_mock = AsyncMock()
            wallet_mock = MagicMock()
            wallet_mock.address = "0x1234567890abcdef"
            wallet_service_mock.assign_wallet.return_value = wallet_mock
            mock_get_service.return_value = wallet_service_mock
            
            # Setup
            mock_update.callback_query.data = "pay_crypto_basic"
            context = MagicMock()
            
            # Mock the edit_message_text method
            mock_update.callback_query.edit_message_text = AsyncMock()
            
            # Execute
            await handler.pay_with_crypto(mock_update, context)
            
            # Verify
            assert mock_update.callback_query.edit_message_text.call_count >= 1
            calls = mock_update.callback_query.edit_message_text.call_args_list
            
            # Find the crypto payment message
            crypto_call = None
            for call in calls:
                if "Pago con Cryptomoneda" in call[1]['text']:
                    crypto_call = call
                    break
            
            assert crypto_call is not None
            message = crypto_call[1]['text']
            
            assert "Pago con Cryptomoneda" in message
            assert "Básico" in message
            assert "10 GB" in message
            assert "1.00 USDT" in message
            assert "0x1234567890abcdef" in message
            assert "BSC" in message