"""
Rutas públicas para la Mini App (no requieren autenticación).

Incluye la página de entrada y política de privacidad.

Author: uSipipo Team
Version: 1.0.2 - Separated direct web route from API router
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import settings

router = APIRouter(tags=["Mini App Web - Public"])

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "miniapp" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render_entry_html(request: Request):
    """Render entry.html template (shared between direct and API routes)."""
    return templates.TemplateResponse(
        "entry.html",
        {
            "request": request,
            "bot_username": settings.BOT_USERNAME,
        },
    )


# NOTE: Direct web route for Telegram WebApp button is defined in server.py
# It's added via app.add_api_route("/miniapp/entry", ...) without the router prefix


@router.get("/public/entry", response_class=HTMLResponse)
async def miniapp_entry(request: Request):
    """
    Página de entrada pública para la Mini App (ruta con prefijo API).

    Esta página se carga sin autenticación para obtener initData
    del SDK de Telegram y redirigir al dashboard autenticado.
    """
    return render_entry_html(request)


@router.get("/public/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """
    Página pública de Política de Privacidad.

    Requerido por Telegram para bots con Mini Apps.
    Esta página es accesible sin autenticación.
    """
    return templates.TemplateResponse(
        "privacy.html",
        {
            "request": request,
        },
    )
