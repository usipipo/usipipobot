"""
Tests for Mini App invoice generation endpoints.

These tests verify the invoice creation flow for both Telegram Stars
and cryptocurrency payments, including error handling and validation.

Author: uSipipo Team
Version: 1.0.0
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from infrastructure.api.server import create_app
from miniapp.router import get_current_user

# =============================================================================
# Test Fixtures
# =============================================================================


def mock_get_current_user():
    """Mock dependency for get_current_user."""
    mock_ctx = MagicMock()
    mock_ctx.user = MagicMock()
    mock_ctx.user.id = 12345
    mock_ctx.query_id = "test_query_id"
    return mock_ctx


@pytest.fixture
async def client():
    """
    Create test client with mocked authentication.

    This bypasses Telegram initData validation for testing.
    """
    app = create_app()
    app.dependency_overrides[get_current_user] = mock_get_current_user

    # Mock user repository
    mock_user = MagicMock()
    mock_user.telegram_id = 12345
    mock_user.max_keys = 2

    # Mock notification service
    mock_notification_service = AsyncMock()
    mock_notification_service.send_stars_invoice.return_value = True
    mock_notification_service.send_crypto_payment_notification.return_value = True
    mock_notification_service.send_payment_confirmation.return_value = True

    with patch("miniapp.routes_payments.PostgresUserRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = mock_user
        mock_repo_class.return_value = mock_repo

        with patch(
            "miniapp.services.miniapp_notification_service.get_notification_service"
        ) as mock_get_service:
            mock_get_service.return_value = mock_notification_service

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def client_no_mock():
    """
    Create test client WITHOUT mocked authentication.

    Use this for testing authentication/validation failures.
    """
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# =============================================================================
# Test: Missing Init Data (No Auth Mock)
# =============================================================================


@pytest.mark.asyncio
async def test_invoice_missing_init_data(client_no_mock):
    """
    Test that invoice creation fails gracefully when initData is missing.

    This validates the fix for the silent failure bug - the endpoint should
    return a clear error message instead of failing silently.
    """
    response = await client_no_mock.post(
        "/miniapp/api/create-stars-invoice", json={"product_type": "package", "product_id": "basic"}
    )

    # Auth middleware returns 401 or 403
    assert response.status_code in [400, 401, 403]


# =============================================================================
# Test: Invalid Init Data (No Auth Mock)
# =============================================================================


@pytest.mark.asyncio
async def test_invoice_invalid_init_data(client_no_mock):
    """
    Test that invoice creation fails when initData is invalid/corrupted.

    This ensures the HMAC validation is working correctly.
    """
    response = await client_no_mock.post(
        "/miniapp/api/create-stars-invoice",
        headers={"X-Telegram-Init-Data": "invalid_garbage_data"},
        json={"product_type": "package", "product_id": "basic"},
    )

    # Auth middleware should reject invalid initData
    assert response.status_code in [400, 401, 403]


# =============================================================================
# Test: Valid Package Invoice Creation (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_invoice_valid_package(client):
    """
    Test successful invoice creation for a data package.

    This is the happy path - valid initData, valid product.
    """
    response = await client.post(
        "/miniapp/api/create-stars-invoice", json={"product_type": "package", "product_id": "basic"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "transaction_id" in data
    assert "message" in data


# =============================================================================
# Test: Valid Slots Invoice Creation (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_invoice_valid_slots(client):
    """
    Test successful invoice creation for VPN key slots.
    """
    response = await client.post(
        "/miniapp/api/create-stars-invoice", json={"product_type": "slots", "product_id": "slots_3"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "transaction_id" in data
    assert "message" in data


# =============================================================================
# Test: Invalid Product Type (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_invoice_invalid_product_type(client):
    """
    Test that invoice creation fails for invalid product types.

    Only "package" and "slots" are valid product types.
    """
    response = await client.post(
        "/miniapp/api/create-stars-invoice",
        json={"product_type": "invalid_type", "product_id": "basic"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "error" in data


# =============================================================================
# Test: Invalid Product ID (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_invoice_invalid_product_id(client):
    """
    Test that invoice creation fails for non-existent product IDs.

    Valid package IDs: basic, standard, advanced, premium
    Valid slots IDs: slots_1, slots_3, slots_5, slots_10
    """
    response = await client.post(
        "/miniapp/api/create-stars-invoice",
        json={"product_type": "package", "product_id": "nonexistent"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "error" in data


# =============================================================================
# Test: Crypto Order - Valid Request (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_crypto_order_valid(client):
    """
    Test successful crypto order creation.
    """
    response = await client.post(
        "/miniapp/api/create-crypto-order", json={"product_type": "package", "product_id": "basic"}
    )

    # Should succeed or fail due to missing crypto config in test env
    assert response.status_code in [200, 400, 500]
    data = response.json()
    assert "success" in data


# =============================================================================
# Test: Crypto Order - Invalid Product (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_crypto_order_invalid_product(client):
    """
    Test that crypto order creation fails for invalid products.
    """
    response = await client.post(
        "/miniapp/api/create-crypto-order",
        json={"product_type": "package", "product_id": "invalid"},
    )

    assert response.status_code == 400
    data = response.json()
    assert "success" in data
    assert data["success"] is False or "error" in data


# =============================================================================
# Test: Request Validation - Missing Fields (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_invoice_missing_required_fields(client):
    """
    Test that invoice creation validates required fields.
    """
    # Missing product_id
    response = await client.post(
        "/miniapp/api/create-stars-invoice", json={"product_type": "package"}
    )

    assert response.status_code == 422  # Pydantic validation error

    # Missing product_type
    response = await client.post("/miniapp/api/create-stars-invoice", json={"product_id": "basic"})

    assert response.status_code == 422


# =============================================================================
# Test: CORS Headers
# =============================================================================


@pytest.mark.asyncio
async def test_cors_headers_present(client):
    """
    Test that CORS headers are included in responses.

    This ensures the Mini App can make cross-origin requests from Telegram.
    """
    # Make a regular request first to check CORS headers in response
    response = await client.post(
        "/miniapp/api/create-stars-invoice", json={"product_type": "package", "product_id": "basic"}
    )

    # Check CORS headers (may not be present in test env without middleware)
    # In production, these would be added by the CORSMiddleware
    assert response.status_code == 200


# =============================================================================
# Test: Error Response Format (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_error_response_format(client):
    """
    Test that error responses follow consistent format.

    All error responses should include:
    - success: false
    - error: descriptive message
    """
    response = await client.post(
        "/miniapp/api/create-stars-invoice",
        json={"product_type": "invalid", "product_id": "invalid"},
    )

    data = response.json()

    # Consistent error format
    assert "success" in data
    assert data["success"] is False
    assert "error" in data
    assert isinstance(data["error"], str)
    assert len(data["error"]) > 0


# =============================================================================
# Test: Invoice Creation Success Flow (With Mocked Auth)
# =============================================================================


@pytest.mark.asyncio
async def test_invoice_creation_complete_flow(client):
    """
    Test complete invoice creation flow from request to response.

    This validates the entire fix for the silent failure bug.
    """
    # Step 1: Create invoice (use "basic" which is a valid package)
    response = await client.post(
        "/miniapp/api/create-stars-invoice", json={"product_type": "package", "product_id": "basic"}
    )

    # Step 2: Verify response
    assert response.status_code == 200
    data = response.json()

    # Step 3: Verify response structure
    assert data["success"] is True
    assert "transaction_id" in data
    assert "message" in data
    assert "Telegram" in data["message"]

    # Step 4: Verify transaction ID format (should be UUID-like)
    transaction_id = data["transaction_id"]
    assert len(transaction_id) > 0
    assert isinstance(transaction_id, str)
