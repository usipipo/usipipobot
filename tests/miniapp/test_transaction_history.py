"""
Tests for transaction history endpoint.

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from domain.entities.crypto_order import CryptoOrder, CryptoOrderStatus
from domain.entities.data_package import DataPackage, PackageType
from domain.entities.subscription_plan import PlanType, SubscriptionPlan
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
    """Test client for the API with mocked auth."""
    app = create_app()
    # Override the auth dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user

    # Mock repositories
    mock_user = MagicMock()
    mock_user.telegram_id = 12345
    mock_user.max_keys = 2

    with patch(
        "infrastructure.api.routes.miniapp_payments.PostgresUserRepository"
    ) as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo_class.return_value = mock_repo

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

    # Clean up overrides after test
    app.dependency_overrides.clear()


class TestTransactionHistory:
    """Tests for /api/v1/miniapp/transactions endpoint."""

    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, client):
        """Test getting transactions for user with no transaction history."""
        # Mock repositories to return empty lists
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
            # Setup mocks to return empty lists (use AsyncMock for async methods)
            mock_pkg_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_pkg_repo.return_value.count_by_user = AsyncMock(return_value=0)
            mock_crypto_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_crypto_repo.return_value.count_by_user = AsyncMock(return_value=0)
            mock_sub_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_sub_repo.return_value.count_by_user = AsyncMock(return_value=0)

            response = await client.get("/api/v1/miniapp/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transactions"] == []
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 20
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["pages"] == 0

    @pytest.mark.asyncio
    async def test_get_transactions_with_packages(self, client):
        """Test getting transactions for user with data packages."""
        now = datetime.now(timezone.utc)

        # Mock a data package
        mock_package = DataPackage(
            id=uuid4(),
            user_id=12345,
            package_type=PackageType.BASIC,
            data_limit_bytes=10737418240,  # 10 GB
            data_used_bytes=0,
            stars_paid=250,
            telegram_payment_id="miniapp_txn_123",
            purchased_at=now,
            expires_at=now + timedelta(days=30),
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
            # Setup mocks
            mock_pkg_repo.return_value.get_by_user_paginated = AsyncMock(
                return_value=[mock_package]
            )
            mock_pkg_repo.return_value.count_by_user = AsyncMock(return_value=1)
            mock_crypto_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_crypto_repo.return_value.count_by_user = AsyncMock(return_value=0)
            mock_sub_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_sub_repo.return_value.count_by_user = AsyncMock(return_value=0)

            response = await client.get("/api/v1/miniapp/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["transactions"]) == 1
        tx = data["transactions"][0]
        assert tx["type"] == "package"
        assert tx["description"] == "Paquete 10 GB"
        assert tx["amount"] == -250  # Negative for money spent
        assert tx["status"] == "completed"
        assert tx["payment_method"] == "stars"

    @pytest.mark.asyncio
    async def test_get_transactions_pagination(self, client):
        """Test that pagination works correctly."""
        now = datetime.now(timezone.utc)

        # Create 25 mock packages (more than default page limit of 20)
        mock_packages = [
            DataPackage(
                id=uuid4(),
                user_id=12345,
                package_type=PackageType.BASIC,
                data_limit_bytes=10737418240,
                data_used_bytes=0,
                stars_paid=250,
                telegram_payment_id=f"miniapp_txn_{i}",
                purchased_at=now - timedelta(days=i),
                expires_at=now + timedelta(days=30),
                is_active=True,
            )
            for i in range(25)
        ]

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
            # Mock returns all 25 items (repository fetches with limit=1000)
            # The endpoint will then paginate in-memory
            mock_pkg_repo.return_value.get_by_user_paginated = AsyncMock(return_value=mock_packages)
            mock_pkg_repo.return_value.count_by_user = AsyncMock(return_value=25)
            mock_crypto_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_crypto_repo.return_value.count_by_user = AsyncMock(return_value=0)
            mock_sub_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_sub_repo.return_value.count_by_user = AsyncMock(return_value=0)

            response = await client.get("/api/v1/miniapp/transactions?page=1&limit=20")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["transactions"]) == 20
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 20
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["pages"] == 2  # ceil(25/20) = 2

    @pytest.mark.asyncio
    async def test_get_transactions_filter_by_type(self, client):
        """Test filtering transactions by type."""
        now = datetime.now(timezone.utc)

        # Mock a crypto order
        mock_crypto_order = CryptoOrder(
            id=uuid4(),
            user_id=12345,
            package_type="basic",
            amount_usdt=3.00,
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            tron_dealer_order_id="txn_crypto_123",
            status=CryptoOrderStatus.COMPLETED,
            created_at=now,
            expires_at=now + timedelta(minutes=30),
            tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            confirmed_at=now,
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
            # Setup mocks - only return crypto orders
            mock_pkg_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_pkg_repo.return_value.count_by_user = AsyncMock(return_value=0)
            mock_crypto_repo.return_value.get_by_user_paginated = AsyncMock(
                return_value=[mock_crypto_order]
            )
            mock_crypto_repo.return_value.count_by_user = AsyncMock(return_value=1)
            mock_sub_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_sub_repo.return_value.count_by_user = AsyncMock(return_value=0)

            response = await client.get("/api/v1/miniapp/transactions?type=crypto")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["transactions"]) == 1
        tx = data["transactions"][0]
        assert tx["type"] == "crypto"
        assert tx["amount_usdt"] == 3.00
        assert tx["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_transactions_filter_by_status(self, client):
        """Test filtering transactions by status."""
        now = datetime.now(timezone.utc)

        # Mock a pending crypto order
        mock_pending_crypto = CryptoOrder(
            id=uuid4(),
            user_id=12345,
            package_type="basic",
            amount_usdt=3.00,
            wallet_address="0x1234567890abcdef1234567890abcdef12345678",
            tron_dealer_order_id="txn_pending_123",
            status=CryptoOrderStatus.PENDING,
            created_at=now,
            expires_at=now + timedelta(minutes=30),
            tx_hash=None,
            confirmed_at=None,
        )

        # Mock a completed package
        mock_completed_package = DataPackage(
            id=uuid4(),
            user_id=12345,
            package_type=PackageType.BASIC,
            data_limit_bytes=10737418240,
            data_used_bytes=0,
            stars_paid=250,
            telegram_payment_id="miniapp_txn_456",
            purchased_at=now,
            expires_at=now + timedelta(days=30),
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
            # Setup mocks - return both, but filter should only show pending
            mock_pkg_repo.return_value.get_by_user_paginated = AsyncMock(
                return_value=[mock_completed_package]
            )
            mock_pkg_repo.return_value.count_by_user = AsyncMock(return_value=1)
            mock_crypto_repo.return_value.get_by_user_paginated = AsyncMock(
                return_value=[mock_pending_crypto]
            )
            mock_crypto_repo.return_value.count_by_user = AsyncMock(return_value=1)
            mock_sub_repo.return_value.get_by_user_paginated = AsyncMock(return_value=[])
            mock_sub_repo.return_value.count_by_user = AsyncMock(return_value=0)

            response = await client.get("/api/v1/miniapp/transactions?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Should only show pending transactions (crypto order in this case)
        assert len(data["transactions"]) == 1
        tx = data["transactions"][0]
        assert tx["status"] == "pending"
        assert tx["type"] == "crypto"

    @pytest.mark.asyncio
    async def test_get_transactions_limit_validation(self, client):
        """Test that limit parameter is validated (max 100)."""
        response = await client.get("/api/v1/miniapp/transactions?limit=150")

        # Should either reject with 422 or cap at 100
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data["pagination"]["limit"] <= 100

    @pytest.mark.asyncio
    async def test_get_transactions_mixed_types(self, client):
        """Test getting transactions with mixed types (packages, crypto, subscriptions)."""
        now = datetime.now(timezone.utc)

        # Mock a data package
        mock_package = DataPackage(
            id=uuid4(),
            user_id=12345,
            package_type=PackageType.BASIC,
            data_limit_bytes=10737418240,
            data_used_bytes=0,
            stars_paid=250,
            telegram_payment_id="miniapp_txn_pkg",
            purchased_at=now - timedelta(days=2),
            expires_at=now + timedelta(days=28),
            is_active=True,
        )

        # Mock a crypto order
        mock_crypto = CryptoOrder(
            id=uuid4(),
            user_id=12345,
            package_type="advanced",
            amount_usdt=5.00,
            wallet_address="0xabcdef1234567890abcdef1234567890abcdef12",
            tron_dealer_order_id="txn_crypto_789",
            status=CryptoOrderStatus.COMPLETED,
            created_at=now - timedelta(days=1),
            expires_at=now + timedelta(minutes=29),
            tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            confirmed_at=now - timedelta(days=1),
        )

        # Mock a subscription
        mock_subscription = SubscriptionPlan(
            id=uuid4(),
            user_id=12345,
            plan_type=PlanType.ONE_MONTH,
            stars_paid=500,
            payment_id="miniapp_txn_sub",
            starts_at=now - timedelta(days=3),
            expires_at=now + timedelta(days=27),
            is_active=True,
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=3),
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
            # Setup mocks - return all three types
            mock_pkg_repo.return_value.get_by_user_paginated = AsyncMock(
                return_value=[mock_package]
            )
            mock_pkg_repo.return_value.count_by_user = AsyncMock(return_value=1)
            mock_crypto_repo.return_value.get_by_user_paginated = AsyncMock(
                return_value=[mock_crypto]
            )
            mock_crypto_repo.return_value.count_by_user = AsyncMock(return_value=1)
            mock_sub_repo.return_value.get_by_user_paginated = AsyncMock(
                return_value=[mock_subscription]
            )
            mock_sub_repo.return_value.count_by_user = AsyncMock(return_value=1)

            response = await client.get("/api/v1/miniapp/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["transactions"]) == 3
        types = {tx["type"] for tx in data["transactions"]}
        assert types == {"package", "crypto", "subscription"}


class TestTransactionsPage:
    """Tests for /miniapp/transactions HTML page."""

    @pytest.mark.asyncio
    async def test_transactions_page_renders(self, client):
        """Test that the transactions HTML page renders correctly."""
        response = await client.get("/miniapp/transactions")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Historial de Transacciones" in response.text
        assert "uSipipo VPN" in response.text

    @pytest.mark.asyncio
    async def test_transactions_page_contains_filters(self, client):
        """Test that the transactions page contains filter buttons."""
        response = await client.get("/miniapp/transactions")

        assert response.status_code == 200
        # Check for filter buttons
        assert 'onclick="filterTransactions' in response.text
        assert "filter-all" in response.text
        assert "filter-package" in response.text
        assert "filter-crypto" in response.text
        assert "filter-subscription" in response.text

    @pytest.mark.asyncio
    async def test_transactions_page_contains_javascript(self, client):
        """Test that the transactions page contains required JavaScript."""
        response = await client.get("/miniapp/transactions")

        assert response.status_code == 200
        # Check for JavaScript functions
        assert "async function loadTransactions" in response.text
        assert "function renderTransactions" in response.text
        assert "function filterTransactions" in response.text
        assert "/miniapp/transactions" in response.text  # API endpoint in JS
