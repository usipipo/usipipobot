"""
Test to verify purchase page buttons are functional.

This test verifies that:
1. The purchase page renders correctly
2. Package and slot data is passed to the template
3. Buttons have correct onclick handlers
"""

from unittest.mock import MagicMock

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
    mock_ctx.user.first_name = "Test"
    mock_ctx.query_id = "test_query_id"
    return mock_ctx


@pytest.fixture
async def client():
    """Test client for the API with mocked auth."""
    app = create_app()
    app.dependency_overrides[get_current_user] = mock_get_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_purchase_page_renders(client):
    """Test that purchase page renders with package and slot data."""
    response = await client.get("/api/v1/miniapp/purchase")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    html = response.text

    # Verify page title
    assert "Comprar Datos" in html or "Tienda" in html

    # Verify packages are rendered
    assert "Paquete" in html or "GB" in html

    # Verify slots are rendered
    assert "Slots" in html or "Claves" in html

    # Verify buttons have onclick handlers
    assert "showPaymentMethods" in html

    # Verify payment modal exists
    assert "paymentModal" in html

    print("✅ Purchase page renders correctly with all required elements")


@pytest.mark.asyncio
async def test_purchase_page_buttons_have_correct_handlers(client):
    """Test that buttons have correct onclick handlers with parameters."""
    response = await client.get("/api/v1/miniapp/purchase")

    assert response.status_code == 200
    html = response.text

    # Verify button onclick patterns for packages
    # Should have pattern: onclick="showPaymentMethods('package', 'basic', 100, 0.83)"
    assert "showPaymentMethods('package'" in html or 'showPaymentMethods("package"' in html

    # Verify button onclick patterns for slots
    # Should have pattern: onclick="showPaymentMethods('slots', 'slots_3', 300, 3.00)"
    assert "showPaymentMethods('slots'" in html or 'showPaymentMethods("slots"' in html

    # Verify button onclick patterns for subscriptions
    # Should have pattern: onclick="showPaymentMethods('subscription', 'one_month', 360, 3.00)"
    assert (
        "showPaymentMethods('subscription'" in html or 'showPaymentMethods("subscription"' in html
    )

    print("✅ All buttons have correct onclick handlers")


@pytest.mark.asyncio
async def test_purchase_page_javascript_functions(client):
    """Test that JavaScript functions are properly defined in the page."""
    response = await client.get("/api/v1/miniapp/purchase")

    assert response.status_code == 200
    html = response.text

    # Verify key JavaScript functions exist
    assert "function showPaymentMethods" in html
    assert "function closePaymentModal" in html
    assert "function payWithStars" in html
    assert "function payWithCrypto" in html

    # Verify console logging is present for debugging
    assert "console.log" in html

    print("✅ All required JavaScript functions are defined")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
