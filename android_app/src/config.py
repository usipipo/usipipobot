"""
Configuration for uSipipo VPN Android APK.
"""

import os

from loguru import logger

# Data directory for app preferences
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".usipipo_apk")

# Backend API URL
# Priority: USIPIPO_API_URL env var > PUBLIC_URL + /api/v1 > empty (must be configured)
_public_url = os.getenv("PUBLIC_URL", "").strip()
_fallback_url = os.getenv("USIPIPO_API_URL", "")
if _fallback_url:
    BASE_URL = _fallback_url
elif _public_url:
    BASE_URL = f"{_public_url.rstrip('/')}/api/v1"
else:
    BASE_URL = ""
    logger.warning("BASE_URL no configurada. Configura USIPIPO_API_URL o PUBLIC_URL.")

# Validate HTTPS in production
if os.getenv("APP_ENV", "development").lower() == "production":
    if not BASE_URL:
        raise ValueError("USIPIPO_API_URL o PUBLIC_URL debe estar configurada en producción.")
    if not BASE_URL.startswith("https://"):
        raise ValueError(f"BASE_URL debe usar HTTPS en producción. Actual: {BASE_URL}")

# Timeouts
REQUEST_TIMEOUT = 30  # segundos

# JWT Settings
JWT_STORAGE_SERVICE = "usipipo_jwt"
JWT_EXPIRY_BUFFER_SECONDS = 30  # Refresh JWT if less than 30s remaining

# OTP Settings
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutos
OTP_MAX_ATTEMPTS = 3  # Máximo intentos fallidos antes de bloqueo

# UI Colors (Cyberpunk theme)
COLORS = {
    "bg_void": [0.039, 0.039, 0.059, 1],  # #0a0a0f
    "bg_surface": [0.071, 0.071, 0.102, 1],  # #12121a
    "bg_card": [0.102, 0.102, 0.141, 1],  # #1a1a24
    "neon_cyan": [0, 0.941, 1, 1],  # #00f0ff
    "neon_magenta": [1, 0, 0.667, 1],  # #ff00aa
    "terminal_green": [0, 1, 0.255, 1],  # #00ff41
    "amber": [1, 0.584, 0, 1],  # #ff9500
    "text_primary": [0.878, 0.878, 0.878, 1],  # #e0e0e0
    "text_secondary": [0.541, 0.541, 0.604, 1],  # #8a8a9a
    "text_muted": [0.353, 0.353, 0.416, 1],  # #5a5a6a
    "error": [1, 0.267, 0.267, 1],  # #ff4444
    "success": [0, 1, 0.255, 1],  # #00ff41 (terminal green)
}

# Version
APP_VERSION = "1.0.0"

# Environment
APP_ENV = os.getenv("APP_ENV", "development")
IS_PRODUCTION = APP_ENV.lower() == "production"
