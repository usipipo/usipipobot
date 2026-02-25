"""
Tests para el endpoint de Política de Privacidad de la Mini App.

Author: uSipipo Team
Version: 1.0.0
"""

import pytest
from httpx import AsyncClient, ASGITransport
from infrastructure.api.server import create_app


@pytest.fixture
async def client():
    """Cliente de pruebas para la API."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_privacy_endpoint_returns_200(client):
    """Test que el endpoint de privacidad es accesible sin autenticación."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_privacy_endpoint_contains_title(client):
    """Test que la página tiene título de Política de Privacidad."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    content = response.content.decode("utf-8").lower()
    assert "política de privacidad" in content or "privacy policy" in content


@pytest.mark.asyncio
async def test_privacy_endpoint_contains_usipipo_branding(client):
    """Test que la página tiene el branding de uSipipo."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"usipipo" in content_lower


@pytest.mark.asyncio
async def test_privacy_endpoint_contains_telegram_links(client):
    """Test que la página contiene enlaces a políticas de Telegram."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    assert b"telegram.org/privacy" in response.content
    assert b"telegram.org/tos/bots" in response.content


@pytest.mark.asyncio
async def test_privacy_endpoint_contains_data_collection_section(client):
    """Test que la página describe la recopilación de datos."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"datos" in content_lower or b"data" in content_lower


@pytest.mark.asyncio
async def test_privacy_endpoint_contains_user_rights(client):
    """Test que la página describe los derechos del usuario."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"derechos" in content_lower or b"rights" in content_lower


@pytest.mark.asyncio
async def test_privacy_endpoint_contains_ccpa_section(client):
    """Test que la página incluye sección CCPA para usuarios de California."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"ccpa" in content_lower or b"california" in content_lower


@pytest.mark.asyncio
async def test_privacy_endpoint_contains_contact_section(client):
    """Test que la página incluye información de contacto."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"contacto" in content_lower or b"contact" in content_lower or b"soporte" in content_lower


@pytest.mark.asyncio
async def test_privacy_endpoint_no_authentication_required(client):
    """Test que el endpoint de privacidad NO requiere autenticación."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    assert "No autorizado" not in response.text
    assert "Unauthorized" not in response.text


@pytest.mark.asyncio
async def test_privacy_endpoint_contains_vpn_specific_info(client):
    """Test que la página menciona información específica del servicio VPN."""
    response = await client.get("/miniapp/privacy")
    assert response.status_code == 200
    content_lower = response.content.lower()
    assert b"vpn" in content_lower or b"clave" in content_lower or b"key" in content_lower
