"""
Tests for Mini App payment endpoints.

Author: uSipipo Team
Version: 1.0.0
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from infrastructure.api.routes.miniapp_user import get_current_user
from infrastructure.api.server import create_app


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

    # Mock the notification service
    mock_notification_service = AsyncMock()
    mock_notification_service.send_stars_invoice.return_value = True
    mock_notification_service.send_crypto_payment_notification.return_value = True
    mock_notification_service.send_payment_confirmation.return_value = True

    with patch(
        "infrastructure.api.routes.miniapp_payments.PostgresUserRepository"
    ) as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo_class.return_value = mock_repo

        with patch(
            "miniapp.services.miniapp_notification_service.get_notification_service"
        ) as mock_get_service:
            mock_get_service.return_value = mock_notification_service

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
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
            "/api/v1/miniapp/api/create-stars-invoice",
            json={"product_type": "package", "product_id": "basic"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "transaction_id" in data
        assert "Telegram" in data["message"]

    @pytest.mark.asyncio
    async def test_create_stars_invoice_slots_success(self, client):
        """Test creating a Stars invoice for slots."""
        response = await client.post(
            "/api/v1/miniapp/api/create-stars-invoice",
            json={"product_type": "slots", "product_id": "slots_3"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "transaction_id" in data

    @pytest.mark.asyncio
    async def test_create_stars_invoice_invalid_product(self, client):
        """Test creating invoice with invalid product."""
        response = await client.post(
            "/api/v1/miniapp/api/create-stars-invoice",
            json={"product_type": "package", "product_id": "invalid"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_create_stars_invoice_missing_params(self, client):
        """Test creating invoice without required params - Pydantic validation."""
        response = await client.post(
            "/api/v1/miniapp/api/create-stars-invoice",
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
            "/api/v1/miniapp/api/create-crypto-order",
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
            "/api/v1/miniapp/api/create-crypto-order",
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
            "/api/v1/miniapp/api/create-crypto-order",
            json={"product_id": "basic"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_create_crypto_order_missing_product_id(self, client):
        """Test creating order without product_id - Pydantic validation."""
        response = await client.post(
            "/api/v1/miniapp/api/create-crypto-order",
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
        assert opt.stars == 250  # Nuevo precio: $2.50 USD

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


class TestConfirmPayment:
    """Tests for /api/confirm-payment endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_payment_package_success(self, client):
        """Test confirming payment for a package creates the package."""
        # Mock the data_package_service.purchase_package to return success
        mock_package = MagicMock()
        mock_package.id = "pkg_123"
        mock_package.remaining_bytes = 1073741824  # 1 GB
        mock_package.expires_at.isoformat.return_value = "2025-04-04T12:00:00"

        with patch(
            "infrastructure.api.routes.miniapp_payments.DataPackageService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.purchase_package.return_value = (mock_package, {})
            mock_service_class.return_value = mock_service

            response = await client.post(
                "/api/v1/miniapp/api/confirm-payment",
                json={
                    "product_type": "package",
                    "product_id": "basic",
                    "transaction_id": "txn_123abc",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Paquete comprado exitosamente"
        assert data["package_id"] == "pkg_123"

    @pytest.mark.asyncio
    async def test_confirm_payment_slots_success(self, client):
        """Test confirming payment for slots adds the slots."""
        with patch(
            "infrastructure.api.routes.miniapp_payments.DataPackageService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.purchase_key_slots.return_value = {
                "slots_added": 3,
                "new_max_keys": 5,
                "stars_paid": 700,
            }
            mock_service_class.return_value = mock_service

            response = await client.post(
                "/api/v1/miniapp/api/confirm-payment",
                json={
                    "product_type": "slots",
                    "product_id": "slots_3",
                    "transaction_id": "txn_456def",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Slots comprados exitosamente"
        assert data["slots_added"] == 3
        assert data["new_max_keys"] == 5

    @pytest.mark.asyncio
    async def test_confirm_payment_invalid_product(self, client):
        """Test confirming payment with invalid product returns error."""
        response = await client.post(
            "/api/v1/miniapp/api/confirm-payment",
            json={
                "product_type": "package",
                "product_id": "invalid_package",
                "transaction_id": "txn_789ghi",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_confirm_payment_missing_transaction_id(self, client):
        """Test confirming payment without transaction_id fails validation."""
        response = await client.post(
            "/api/v1/miniapp/api/confirm-payment",
            json={
                "product_type": "package",
                "product_id": "basic",
            },
        )

        # Pydantic validation returns 422 for missing required fields
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_confirm_payment_service_error(self, client):
        """Test handling of service errors during payment confirmation."""
        with patch(
            "infrastructure.api.routes.miniapp_payments.DataPackageService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.purchase_package.side_effect = Exception("Database error")
            mock_service_class.return_value = mock_service

            response = await client.post(
                "/api/v1/miniapp/api/confirm-payment",
                json={
                    "product_type": "package",
                    "product_id": "basic",
                    "transaction_id": "txn_999xyz",
                },
            )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data


class TestPaymentStatus:
    """Tests for /api/payment-status/{transaction_id} endpoint."""

    @pytest.mark.asyncio
    async def test_payment_status_pending(self, client):
        """Test that transaction not found returns pending status."""
        # Mock repositories to return None (no transaction found)
        with (
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresDataPackageRepository"
            ) as mock_pkg_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresCryptoOrderRepository"
            ) as mock_crypto_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresSubscriptionRepository"
            ) as mock_sub_repo,
        ):
            # Setup mocks to return None
            mock_pkg_repo.return_value.get_by_telegram_payment_id = AsyncMock(return_value=None)
            mock_crypto_repo.return_value.get_by_tron_dealer_order_id = AsyncMock(return_value=None)
            mock_sub_repo.return_value.get_by_payment_id = AsyncMock(return_value=None)

            response = await client.get("/api/v1/miniapp/api/payment-status/txn_nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "pending"
        assert "message" in data
        assert "Payment not yet detected" in data["message"]

    @pytest.mark.asyncio
    async def test_payment_status_completed_package(self, client):
        """Test that completed package returns correct data."""
        from datetime import datetime, timezone
        from uuid import uuid4

        from domain.entities.data_package import DataPackage, PackageType

        # Mock a completed package
        mock_package = DataPackage(
            id=uuid4(),
            user_id=12345,
            package_type=PackageType.BASIC,
            data_limit_bytes=10737418240,  # 10 GB
            data_used_bytes=0,
            stars_paid=250,
            telegram_payment_id="miniapp_txn_123abc",
            purchased_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
            is_active=True,
        )

        with (
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresDataPackageRepository"
            ) as mock_pkg_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresCryptoOrderRepository"
            ) as mock_crypto_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresSubscriptionRepository"
            ) as mock_sub_repo,
        ):
            # Package repo returns the package
            mock_pkg_repo.return_value.get_by_telegram_payment_id = AsyncMock(
                return_value=mock_package
            )
            mock_crypto_repo.return_value.get_by_tron_dealer_order_id = AsyncMock(return_value=None)
            mock_sub_repo.return_value.get_by_payment_id = AsyncMock(return_value=None)

            response = await client.get("/api/v1/miniapp/api/payment-status/txn_123abc")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "completed"
        assert data["type"] == "package"
        assert data["product_id"] == "basic"
        assert data["data_gb"] == 10
        assert "activated_at" in data

    @pytest.mark.asyncio
    async def test_payment_status_completed_crypto(self, client):
        """Test that completed crypto order returns correct data."""
        from datetime import datetime, timezone
        from uuid import uuid4

        from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus

        # Mock a completed crypto order
        mock_crypto_order = CryptoOrder(
            id=uuid4(),
            user_id=12345,
            package_type="basic",
            amount_usdt=3.00,
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            tron_dealer_order_id="txn_crypto_456def",
            status=CryptoOrderStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
            tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            confirmed_at=datetime.now(timezone.utc),
        )

        with (
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresDataPackageRepository"
            ) as mock_pkg_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresCryptoOrderRepository"
            ) as mock_crypto_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresSubscriptionRepository"
            ) as mock_sub_repo,
        ):
            # Package repo returns None
            mock_pkg_repo.return_value.get_by_telegram_payment_id = AsyncMock(return_value=None)
            # Crypto repo returns the completed order
            mock_crypto_repo.return_value.get_by_tron_dealer_order_id = AsyncMock(
                return_value=mock_crypto_order
            )
            mock_sub_repo.return_value.get_by_payment_id = AsyncMock(return_value=None)

            response = await client.get("/api/v1/miniapp/api/payment-status/txn_crypto_456def")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "completed"
        assert data["type"] == "crypto"
        assert data["amount_usdt"] == 3.00
        assert "confirmed_at" in data

    @pytest.mark.asyncio
    async def test_payment_status_pending_crypto(self, client):
        """Test that pending crypto order returns pending status."""
        from datetime import datetime, timezone
        from uuid import uuid4

        from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus

        # Mock a pending crypto order
        mock_crypto_order = CryptoOrder(
            id=uuid4(),
            user_id=12345,
            package_type="basic",
            amount_usdt=3.00,
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            tron_dealer_order_id="txn_pending_789ghi",
            status=CryptoOrderStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
            tx_hash=None,
            confirmed_at=None,
        )

        with (
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresDataPackageRepository"
            ) as mock_pkg_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresCryptoOrderRepository"
            ) as mock_crypto_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresSubscriptionRepository"
            ) as mock_sub_repo,
        ):
            mock_pkg_repo.return_value.get_by_telegram_payment_id = AsyncMock(return_value=None)
            mock_crypto_repo.return_value.get_by_tron_dealer_order_id = AsyncMock(
                return_value=mock_crypto_order
            )
            mock_sub_repo.return_value.get_by_payment_id = AsyncMock(return_value=None)

            response = await client.get("/api/v1/miniapp/api/payment-status/txn_pending_789ghi")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "pending"
        assert data["type"] == "crypto"
        assert data["amount_usdt"] == 3.00

    @pytest.mark.asyncio
    async def test_payment_status_completed_subscription(self, client):
        """Test that completed subscription returns correct data."""
        from datetime import datetime, timedelta, timezone
        from uuid import uuid4

        from domain.entities.subscription_plan import PlanType, SubscriptionPlan

        # Mock a completed subscription
        now = datetime.now(timezone.utc)
        mock_subscription = SubscriptionPlan(
            id=uuid4(),
            user_id=12345,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=500,
            payment_id="miniapp_txn_sub_999xyz",
            starts_at=now,
            expires_at=now + timedelta(days=30),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        with (
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresDataPackageRepository"
            ) as mock_pkg_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresCryptoOrderRepository"
            ) as mock_crypto_repo,
            patch(
                "infrastructure.api.routes.miniapp_payments.PostgresSubscriptionRepository"
            ) as mock_sub_repo,
        ):
            mock_pkg_repo.return_value.get_by_telegram_payment_id = AsyncMock(return_value=None)
            mock_crypto_repo.return_value.get_by_tron_dealer_order_id = AsyncMock(return_value=None)
            # Subscription repo returns the subscription
            mock_sub_repo.return_value.get_by_payment_id = AsyncMock(return_value=mock_subscription)

            response = await client.get("/api/v1/miniapp/api/payment-status/txn_sub_999xyz")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "completed"
        assert data["type"] == "subscription"
        assert data["plan_type"] == "one_month"
        assert "activated_at" in data
