"""
Rutas de administración para la Mini App.

Incluye visualización de logs del sistema (solo administradores).

Author: uSipipo Team
Version: 1.0.0
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from miniapp.routes_common import MiniAppContext, require_admin
from utils.logger import logger

router = APIRouter(tags=["Mini App - Admin"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, ctx: MiniAppContext = Depends(require_admin)):
    """Página de logs del sistema (solo administrador)."""
    logger.info(f"🖥️ Admin {ctx.user.id} accessed logs page")
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "user": ctx.user,
        },
    )


@router.get("/api/logs")
async def api_get_logs(lines: int = 100, ctx: MiniAppContext = Depends(require_admin)):
    """API: Obtiene los últimos logs del sistema (solo administrador)."""
    try:
        from utils.logger import logger as app_logger

        log_lines = app_logger.get_last_logs(lines=lines)

        # Parse log lines into structured format
        parsed_logs = []
        for line in log_lines.strip().split("\n"):
            if not line.strip():
                continue

            # Try to parse log format: "YYYY-MM-DD HH:mm:ss | LEVEL | message"
            parts = line.split(" | ", 2)
            if len(parts) >= 3:
                timestamp = parts[0].strip()
                level = parts[1].strip()
                message = parts[2].strip()
            elif len(parts) == 2:
                timestamp = parts[0].strip()
                level = "INFO"
                message = parts[1].strip()
            else:
                timestamp = datetime.now().isoformat()
                level = "INFO"
                message = line

            parsed_logs.append(
                {
                    "timestamp": timestamp,
                    "level": level,
                    "message": message,
                }
            )

        logger.debug(f"📋 Admin {ctx.user.id} fetched {len(parsed_logs)} log lines")
        return {
            "logs": parsed_logs,
            "total": len(parsed_logs),
        }

    except Exception as e:
        logger.error(f"Error fetching logs for admin {ctx.user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al obtener logs")
