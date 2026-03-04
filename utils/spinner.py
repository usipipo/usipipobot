"""
Sistema de Spinner para mejorar UX en operaciones asíncronas del bot.

Este módulo proporciona decoradores y utilidades para mostrar spinners
durante operaciones que pueden tomar tiempo, mejorando la experiencia
del usuario al proporcionar feedback visual inmediato.

Nota: Este módulo ha sido refactorizado. Las implementaciones se han
movido a submódulos especializados para mantener archivos bajo 300 líneas:
- spinner_styles.py: Constantes y configuraciones visuales
- spinner_core.py: Clase SpinnerManager
- spinner_decorators.py: Decoradores para funciones

Este archivo mantiene las exportaciones para compatibilidad hacia atrás.
"""

# Re-exportar todo desde los submódulos para mantener compatibilidad
from utils.spinner_core import SpinnerManager
from utils.spinner_decorators import (
    admin_spinner_callback,
    database_spinner,
    database_spinner_callback,
    payment_spinner,
    registration_spinner,
    shop_spinner_callback,
    vpn_spinner,
    with_animated_spinner,
    with_spinner,
)
from utils.spinner_styles import SpinnerStyles

__all__ = [
    "SpinnerManager",
    "SpinnerStyles",
    "with_spinner",
    "with_animated_spinner",
    "database_spinner",
    "shop_spinner_callback",
    "admin_spinner_callback",
    "database_spinner_callback",
    "vpn_spinner",
    "registration_spinner",
    "payment_spinner",
]
