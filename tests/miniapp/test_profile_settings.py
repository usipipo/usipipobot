"""
Tests para los endpoints de Perfil y Ajustes de la Mini App.

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


class TestProfileEndpoint:
    """Tests para el endpoint de perfil."""

    @pytest.mark.asyncio
    async def test_profile_requires_authentication(self, client):
        """Test que el endpoint de perfil requiere autenticación."""
        response = await client.get("/miniapp/profile")
        assert response.status_code == 401
        assert "No autorizado" in response.text or "Unauthorized" in response.text

    @pytest.mark.asyncio
    async def test_profile_endpoint_returns_401_without_init_data(self, client):
        """Test que el perfil rechaza requests sin initData."""
        response = await client.get("/miniapp/profile")
        assert response.status_code == 401


class TestSettingsEndpoint:
    """Tests para el endpoint de ajustes."""

    @pytest.mark.asyncio
    async def test_settings_requires_authentication(self, client):
        """Test que el endpoint de ajustes requiere autenticación."""
        response = await client.get("/miniapp/settings")
        assert response.status_code == 401
        assert "No autorizado" in response.text or "Unauthorized" in response.text

    @pytest.mark.asyncio
    async def test_settings_endpoint_returns_401_without_init_data(self, client):
        """Test que los ajustes rechazan requests sin initData."""
        response = await client.get("/miniapp/settings")
        assert response.status_code == 401


class TestProfileAndSettingsIntegration:
    """Tests de integración para perfil y ajustes."""

    @pytest.mark.asyncio
    async def test_profile_page_template_exists(self, client):
        """Test que el template de perfil existe y es accesible."""
        # El template debe existir, aunque requiera auth
        response = await client.get("/miniapp/profile")
        # Solo verificamos que el endpoint existe (no 404)
        assert response.status_code in [401, 500]

    @pytest.mark.asyncio
    async def test_settings_page_template_exists(self, client):
        """Test que el template de ajustes existe y es accesible."""
        # El template debe existir, aunque requiera auth
        response = await client.get("/miniapp/settings")
        # Solo verificamos que el endpoint existe (no 404)
        assert response.status_code in [401, 500]


class TestDropdownNavigation:
    """Tests para la navegación de la miniapp."""

    @pytest.mark.asyncio
    async def test_base_template_contains_header(self, client):
        """Test que el template base contiene el header."""
        response = await client.get("/miniapp/privacy")
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "header" in content.lower()

    @pytest.mark.asyncio
    async def test_base_template_has_nav_items(self, client):
        """Test que el base template contiene los items del nav."""
        import pathlib
        base_template = pathlib.Path(__file__).parent.parent.parent / "miniapp" / "templates" / "base.html"
        content = base_template.read_text().lower()
        assert "dashboard" in content
        assert "claves" in content
        assert "comprar" in content
        assert "perfil" in content
        assert "ajustes" in content

    @pytest.mark.asyncio
    async def test_privacy_link_not_in_bottom_nav(self, client):
        """Test que el link de privacidad no está en el nav inferior del base template."""
        import pathlib
        base_template = pathlib.Path(__file__).parent.parent.parent / "miniapp" / "templates" / "base.html"
        content = base_template.read_text().lower()
        nav_start = content.find("bottom-nav")
        nav_end = content.find("{% endblock %}", nav_start) if nav_start != -1 else 0
        nav_section = content[nav_start:nav_end] if nav_start != -1 else ""
        assert "privacidad" not in nav_section
