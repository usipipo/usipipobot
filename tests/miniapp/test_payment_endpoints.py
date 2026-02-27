"""
Tests for Mini App payment endpoints.

Author: uSipipo Team
Version: 1.0.0
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.api.server import create_app


@pytest.fixture
async def client():
    """Test client for the API."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Mock authentication headers for Mini App."""
    # In a real scenario, this would be a valid initData from Telegram
    return {
        "X-Telegram-Init-Data": "mock_init_data"
    }


class TestCreateStarsInvoice:
    """Tests for /api/create-stars-invoice endpoint."""

    @pytest.mark.asyncio
    @patch("miniapp.router.MiniAppAuthService")
    async def test_create_stars_invoice_package_success(self, mock_auth, client):
        """Test creating a Stars invoice for a package."""
        # Setup mock auth
        mock_auth_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.user = MagicMock()
        mock_result.user.id = 12345
        mock_auth_instance.validate_init_data.return_value = mock_result
        mock_auth.return_value = mock_auth_instance

        response = await client.post(
            "/miniapp/api/create-stars-invoice",
            json={"product_type": "package", "product_id": "basic"},
            headers={"X-Telegram-Init-Data": "mock_data"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "invoice_url" in data
        assert "tg://invoice" in data["invoice_url"]

    @pytest.mark.asyncio
    @patch("miniapp.router.MiniAppAuthService")
    async def test_create_stars_invoice_slots_success(self, mock_auth, client):
        """Test creating a Stars invoice for slots."""
        # Setup mock auth
        mock_auth_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.user = MagicMock()
        mock_result.user.id = 12345
        mock_auth_instance.validate_init_data.return_value = mock_result
        mock_auth.return_value = mock_auth_instance

        response = await client.post(
            "/miniapp/api/create-stars-invoice",
            json={"product_type": "slots", "product_id": "slots_3"},
            headers={"X-Telegram-Init-Data": "mock_data"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "invoice_url" in data

    @pytest.mark.asyncio
    @patch("miniapp.router.MiniAppAuthService")
    async def test_create_stars_invoice_invalid_product(self, mock_auth, client):
        """Test creating invoice with invalid product."""
        # Setup mock auth
        mock_auth_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.user = MagicMock()
        mock_result.user.id = 12345
        mock_auth_instance.validate_init_data.return_value = mock_result
        mock_auth.return_value = mock_auth_instance

        response = await client.post(
            "/miniapp/api/create-stars-invoice",
            json={"product_type": "package", "product_id": "invalid"},
            headers={"X-Telegram-Init-Data": "mock_data"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch("miniapp.router.MiniAppAuthService")
    async def test_create_stars_invoice_missing_params(self, mock_auth, client):
        """Test creating invoice without required params."""
        # Setup mock auth
        mock_auth_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.user = MagicMock()
        mock_result.user.id = 12345
        mock_auth_instance.validate_init_data.return_value = mock_result
        mock_auth.return_value = mock_auth_instance

        response = await client.post(
            "/miniapp/api/create-stars-invoice",
            json={},
            headers={"X-Telegram-Init-Data": "mock_data"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


class TestCreateCryptoOrder:
    """Tests for /api/create-crypto-order endpoint."""

    @pytest.mark.asyncio
    @patch("miniapp.router.MiniAppAuthService")
    @patch("miniapp.services.miniapp_payment_service.WalletManagementService")
    @patch("miniapp.services.miniapp_payment_service.CryptoPaymentService")
    async def test_create_crypto_order_package_success(
        self, mock_crypto_service, mock_wallet_service, mock_auth, client
    ):
        """Test creating a crypto order for a package."""
        # Setup mock auth
        mock_auth_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.user = MagicMock()
        mock_result.user.id = 12345
        mock_auth_instance.validate_init_data.return_value = mock_result
        mock_auth.return_value = mock_auth_instance

        # Setup mocks for wallet and payment
        mock_wallet = MagicMock()
        mock_wallet.address = "0x1234567890abcdef"
        mock_wallet_service.return_value.assign_wallet = AsyncMock(return_value=mock_wallet)

        mock_order = MagicMock()
        mock_order.id = "test-order-id"
        mock_order.expires_at = None
        mock_crypto_service.return_value.create_order = AsyncMock(return_value=mock_order)

        with patch("miniapp.services.miniapp_payment_service.QrGenerator.generate_payment_qr", return_value="/path/to/qr.png"):
            response = await client.post(
                "/miniapp/api/create-crypto-order",
                json={"product_type": "package", "product_id": "basic"},
                headers={"X-Telegram-Init-Data": "mock_data"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "order_id" in data
        assert "wallet_address" in data
        assert "amount_usdt" in data
        assert data["amount_usdt"] == 0.5  # 5 GB / 10

    @pytest.mark.asyncio
    @patch("miniapp.router.MiniAppAuthService")
    @patch("miniapp.services.miniapp_payment_service.WalletManagementService")
    @patch("miniapp.services.miniapp_payment_service.CryptoPaymentService")
    async def test_create_crypto_order_slots_success(
        self, mock_crypto_service, mock_wallet_service, mock_auth, client
    ):
        """Test creating a crypto order for slots."""
        # Setup mock auth
        mock_auth_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.user = MagicMock()
        mock_result.user.id = 12345
        mock_auth_instance.validate_init_data.return_value = mock_result
        mock_auth.return_value = mock_auth_instance

        # Setup mocks for wallet and payment
        mock_wallet = MagicMock()
        mock_wallet.address = "0x1234567890abcdef"
        mock_wallet_service.return_value.assign_wallet = AsyncMock(return_value=mock_wallet)

        mock_order = MagicMock()
        mock_order.id = "test-order-id"
        mock_order.expires_at = None
        mock_crypto_service.return_value.create_order = AsyncMock(return_value=mock_order)

        with patch("miniapp.services.miniapp_payment_service.QrGenerator.generate_payment_qr", return_value="/path/to/qr.png"):
            response = await client.post(
                "/miniapp/api/create-crypto-order",
                json={"product_type": "slots", "product_id": "slots_3"},
                headers={"X-Telegram-Init-Data": "mock_data"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "order_id" in data
        assert data["amount_usdt"] == 6.0  # 600 stars / 100

    @pytest.mark.asyncio
    @patch("miniapp.router.MiniAppAuthService")
    async def test_create_crypto_order_invalid_product(self, mock_auth, client):
        """Test creating order with invalid product."""
        # Setup mock auth
        mock_auth_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.user = MagicMock()
        mock_result.user.id = 12345
        mock_auth_instance.validate_init_data.return_value = mock_result
        mock_auth.return_value = mock_auth_instance

        response = await client.post(
            "/miniapp/api/create-crypto-order",
            json={"product_type": "package", "product_id": "invalid"},
            headers={"X-Telegram-Init-Data": "mock_data"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


class TestMiniAppPaymentService:
    """Tests for MiniAppPaymentService."""

    def test_get_package_option_success(self):
        """Test getting a valid package option."""
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService
        from application.services.data_package_service import DataPackageService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        opt = payment_service.get_package_option("basic")
        assert opt is not None
        assert opt.package_type.value == "basic"
        assert opt.stars == 500

    def test_get_package_option_not_found(self):
        """Test getting an invalid package option."""
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService
        from application.services.data_package_service import DataPackageService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        opt = payment_service.get_package_option("invalid")
        assert opt is None

    def test_get_slot_option_success(self):
        """Test getting a valid slot option."""
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService
        from application.services.data_package_service import DataPackageService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        opt = payment_service.get_slot_option(3)
        assert opt is not None
        assert opt.slots == 3
        assert opt.stars == 600

    def test_create_stars_invoice_url_package(self):
        """Test creating Stars invoice URL for package."""
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService
        from application.services.data_package_service import DataPackageService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        url = payment_service.create_stars_invoice_url(
            user_id=12345,
            product_type="package",
            product_id="basic",
        )

        assert url is not None
        assert "tg://invoice" in url
        assert "XTR" in url
        assert "data_package_basic_12345" in url

    def test_create_stars_invoice_url_slots(self):
        """Test creating Stars invoice URL for slots."""
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService
        from application.services.data_package_service import DataPackageService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        url = payment_service.create_stars_invoice_url(
            user_id=12345,
            product_type="slots",
            product_id="slots_3",
        )

        assert url is not None
        assert "tg://invoice" in url
        assert "key_slots_3_12345" in url

    def test_create_stars_invoice_url_invalid_type(self):
        """Test creating Stars invoice URL with invalid type."""
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService
        from application.services.data_package_service import DataPackageService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        url = payment_service.create_stars_invoice_url(
            user_id=12345,
            product_type="invalid",
            product_id="basic",
        )

        assert url is None
