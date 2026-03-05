"""
Tests for Mini App payment endpoints.

Author: uSipipo Team
Version: 1.0.0
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from infrastructure.api.server import create_app
from miniapp.router import get_current_user


def mock_get_current_user():
    """Mock dependency for get_current_user."""
    mock_ctx = MagicMock()
    mock_ctx.user = MagicMock()
    mock_ctx.user.id = 12345
    mock_ctx.query_id = "test_query_id"
    return mock_ctx


@pytest.fixture
async def client():
    """Test client for the API with mocked auth and user repo."""
    app = create_app()
    # Override the auth dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user

    # Mock the user repository to return a user (required by new user existence checks)
    mock_user = MagicMock()
    mock_user.telegram_id = 12345
    mock_user.max_keys = 2

    with patch("miniapp.routes_payments.PostgresUserRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo_class.return_value = mock_repo

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Mock authentication headers for Mini App."""
    # In a real scenario, this would be a valid initData from Telegram
    return {"X-Telegram-Init-Data": "mock_init_data"}


class TestCreateStarsInvoice:
    """Tests for /api/create-stars-invoice endpoint."""

    @pytest.mark.asyncio
    async def test_create_stars_invoice_package_success(self, client):
        """Test creating a Stars invoice for a package."""
        response = await client.post(
            "/miniapp/api/create-stars-invoice",
            json={"product_type": "package", "product_id": "basic"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "invoice_url" in data
        assert "tg://invoice" in data["invoice_url"]

    @pytest.mark.asyncio
    async def test_create_stars_invoice_slots_success(self, client):
        """Test creating a Stars invoice for slots."""
        response = await client.post(
            "/miniapp/api/create-stars-invoice",
            json={"product_type": "slots", "product_id": "slots_3"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "invoice_url" in data

    @pytest.mark.asyncio
    async def test_create_stars_invoice_invalid_product(self, client):
        """Test creating invoice with invalid product."""
        response = await client.post(
            "/miniapp/api/create-stars-invoice",
            json={"product_type": "package", "product_id": "invalid"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_create_stars_invoice_missing_params(self, client):
        """Test creating invoice without required params - Pydantic validation."""
        response = await client.post(
            "/miniapp/api/create-stars-invoice",
            json={},
        )

        # Pydantic validation returns 422 for missing required fields
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestCreateCryptoOrder:
    """Tests for /api/create-crypto-order endpoint."""

    @pytest.mark.asyncio
    async def test_create_crypto_order_validates_request(self, client):
        """Test that crypto order endpoint validates product_type and product_id."""
        # Valid request structure but invalid product should return 400 (after auth)
        response = await client.post(
            "/miniapp/api/create-crypto-order",
            json={"product_type": "package", "product_id": "invalid"},
        )

        # Should pass auth and Pydantic validation, fail at business logic
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_create_crypto_order_missing_params(self, client):
        """Test creating order without required params - Pydantic validation."""
        response = await client.post(
            "/miniapp/api/create-crypto-order",
            json={},
        )

        # Pydantic validation returns 422 for missing required fields
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_crypto_order_missing_product_type(self, client):
        """Test creating order without product_type - Pydantic validation."""
        response = await client.post(
            "/miniapp/api/create-crypto-order",
            json={"product_id": "basic"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_crypto_order_missing_product_id(self, client):
        """Test creating order without product_id - Pydantic validation."""
        response = await client.post(
            "/miniapp/api/create-crypto-order",
            json={"product_type": "package"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestMiniAppPaymentService:
    """Tests for MiniAppPaymentService."""

    def test_get_package_option_success(self):
        """Test getting a valid package option."""
        from application.services.data_package_service import DataPackageService
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        opt = payment_service.get_package_option("basic")
        assert opt is not None
        assert opt.package_type.value == "basic"
        assert opt.stars == 600

    def test_get_package_option_not_found(self):
        """Test getting an invalid package option."""
        from application.services.data_package_service import DataPackageService
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        opt = payment_service.get_package_option("invalid")
        assert opt is None

    def test_get_slot_option_success(self):
        """Test getting a valid slot option."""
        from application.services.data_package_service import DataPackageService
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        opt = payment_service.get_slot_option(3)
        assert opt is not None
        assert opt.slots == 3
        assert opt.stars == 700

    def test_create_stars_invoice_url_package(self):
        """Test creating Stars invoice URL for package."""
        from application.services.data_package_service import DataPackageService
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService

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
        from application.services.data_package_service import DataPackageService
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService

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
        from application.services.data_package_service import DataPackageService
        from miniapp.services.miniapp_payment_service import MiniAppPaymentService

        mock_service = MagicMock(spec=DataPackageService)
        payment_service = MiniAppPaymentService(mock_service)

        url = payment_service.create_stars_invoice_url(
            user_id=12345,
            product_type="invalid",
            product_id="basic",
        )

        assert url is None
