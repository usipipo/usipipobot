"""
Telegram Handler Utilities

This module provides Telegram-specific utilities for handlers.

Nota: Este módulo ha sido refactorizado. Las implementaciones se han
movido a submódulos especializados para mantener archivos bajo 300 líneas:
- telegram_format_utils.py: Funciones de formato (bytes, fechas, moneda, etc.)
- telegram_validation_utils.py: Validación y sanitización de texto
- telegram_callback_utils.py: Helpers de callback data y utilidades generales
- telegram_message_handler.py: Clase TelegramUtils para manejo seguro de mensajes

Este archivo mantiene las exportaciones para compatibilidad hacia atrás.

Author: uSipipo Team
Version: 3.0.0 - Refactored into sub-modules
"""

from utils.telegram_callback_utils import (
    calculate_page_bounds,
    chunk_list,
    create_callback_data,
    extract_id_from_callback,
    generate_unique_id,
    is_admin,
    parse_callback_data,
    safe_get,
)

# Re-exportar todo desde los submódulos para mantener compatibilidad
from utils.telegram_format_utils import (
    format_bytes,
    format_currency,
    format_datetime,
    format_percentage,
    format_relative_time,
    format_user_name,
)
from utils.telegram_message_handler import (
    TelegramHandlerUtils,
    TelegramUtils,
)
from utils.telegram_validation_utils import (
    escape_markdown,
    sanitize_text,
    truncate_string,
    validate_email,
    validate_phone_number,
)

__all__ = [
    # Format utilities
    "format_bytes",
    "format_datetime",
    "format_relative_time",
    "format_currency",
    "format_percentage",
    "format_user_name",
    # Validation utilities
    "sanitize_text",
    "validate_phone_number",
    "validate_email",
    "escape_markdown",
    "truncate_string",
    # Callback & general utilities
    "extract_id_from_callback",
    "create_callback_data",
    "parse_callback_data",
    "safe_get",
    "chunk_list",
    "generate_unique_id",
    "is_admin",
    "calculate_page_bounds",
    # Telegram message handler
    "TelegramUtils",
    "TelegramHandlerUtils",
]
