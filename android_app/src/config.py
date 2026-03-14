"""
Configuration for uSipipo VPN Android APK.
"""
import os

# Data directory for app preferences
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".usipipo_apk")

# Backend API URL (cambiar en producción)
BASE_URL = os.getenv("USIPIPO_API_URL", "https://tu-server.com/api/v1")

# Timeouts
REQUEST_TIMEOUT = 30  # segundos

# JWT Settings
JWT_STORAGE_SERVICE = "usipipo_jwt"

# OTP Settings
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutos

# UI Colors (Cyberpunk theme)
COLORS = {
    "bg_void": [0.039, 0.039, 0.059, 1],      # #0a0a0f
    "bg_surface": [0.071, 0.071, 0.102, 1],   # #12121a
    "bg_card": [0.102, 0.102, 0.141, 1],      # #1a1a24
    "neon_cyan": [0, 0.941, 1, 1],            # #00f0ff
    "neon_magenta": [1, 0, 0.667, 1],         # #ff00aa
    "terminal_green": [0, 1, 0.255, 1],       # #00ff41
    "amber": [1, 0.584, 0, 1],                # #ff9500
    "text_primary": [0.878, 0.878, 0.878, 1], # #e0e0e0
    "text_secondary": [0.541, 0.541, 0.604, 1], # #8a8a9a
    "text_muted": [0.353, 0.353, 0.416, 1],   # #5a5a6a
    "error": [1, 0.267, 0.267, 1],            # #ff4444
}

# Version
APP_VERSION = "1.0.0"
