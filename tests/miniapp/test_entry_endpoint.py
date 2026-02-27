"""
Tests para el endpoint de entrada de la Mini App.

Author: uSipipo Team
Version: 1.0.0
"""

import pytest
from httpx import ASGITransport, AsyncClient

from infrastructure.api.server import create_app


@pytest.fixture
async def client():
    """Cliente de pruebas para la API."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_entry_endpoint_returns_200(client):
    """Test que el endpoint de entrada es accesible sin autenticación."""
    response = await client.get("/miniapp/entry")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_entry_endpoint_contains_telegram_sdk(client):
    """Test que la página de entrada incluye el SDK de Telegram WebApp."""
    response = await client.get("/miniapp/entry")
    assert response.status_code == 200
    assert b"telegram-web-app.js" in response.content


@pytest.mark.asyncio
async def test_entry_endpoint_contains_redirect_logic(client):
    """Test que la página de entrada tiene lógica de redirección JavaScript."""
    response = await client.get("/miniapp/entry")
    assert response.status_code == 200
    assert b"tgWebAppData" in response.content
    assert b"/miniapp/" in response.content


@pytest.mark.asyncio
async def test_entry_endpoint_contains_loading_spinner(client):
    """Test que la página de entrada tiene spinner de carga."""
    response = await client.get("/miniapp/entry")
    assert response.status_code == 200
    assert b"spinner" in response.content or b"loading" in response.content.lower()


@pytest.mark.asyncio
async def test_entry_endpoint_has_error_handling(client):
    """Test que la página de entrada maneja errores."""
    response = await client.get("/miniapp/entry")
    assert response.status_code == 200
    assert b"error" in response.content.lower() or b"Error" in response.content


@pytest.mark.asyncio
async def test_dashboard_requires_authentication(client):
    """Test que el dashboard aún requiere autenticación."""
    response = await client.get("/miniapp/")
    assert response.status_code == 401
    assert "No autorizado" in response.text or "Unauthorized" in response.text


@pytest.mark.asyncio
async def test_entry_endpoint_contains_usipipo_branding(client):
    """Test que la página de entrada tiene el branding de uSipipo."""
    response = await client.get("/miniapp/entry")
    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"usipipo" in content_lower or b"vpn" in content_lower
