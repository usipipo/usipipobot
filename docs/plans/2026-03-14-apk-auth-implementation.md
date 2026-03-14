# APK Android - Módulo de Autenticación Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar las pantallas de Splash, Login y OTP para el flujo de autenticación de la APK Android usando Kivy + KivyMD.

**Architecture:** Clean Architecture adaptada a KivyMD:
- `screens/`: Pantallas con lógica UI y navegación
- `services/`: Lógica de negocio (API calls, validaciones)
- `storage/`: Almacenamiento seguro (JWT en Keystore)
- `kv/`: Diseños en lenguaje KV
- `components/`: Widgets reutilizables

**Tech Stack:** Kivy 2.3.x, KivyMD 2.0.x, httpx (async HTTP), keyring (Android Keystore), pydantic (validación)

---

## 📋 Índice de Tareas

### Fase 0: Configuración Inicial (COMPLETADA)
- [x] Task 0.1: Crear estructura de directorios `android_app/`
- [x] Task 0.2: Crear `buildozer.spec` inicial

### Fase 0: Continuación
- [ ] Task 0.3: Crear `requirements-android.txt`
- [ ] Task 0.4: Crear `main.py` entry point
- [ ] Task 0.5: Crear `app.py` con MDApp y ScreenManager

### Fase 1: Diseño Visual Base
- [ ] Task 1.1: Crear `assets/fonts/` con fuentes (placeholders)
- [ ] Task 1.2: Crear `assets/images/` con logo (placeholder)
- [ ] Task 1.3: Crear `src/config.py` con colores cyberpunk
- [ ] Task 1.4: Crear `src/utils/logger.py` para logging

### Fase 2: Capa de Servicios
- [ ] Task 2.1: Crear `src/storage/secure_storage.py`
- [ ] Task 2.2: Crear `src/services/api_client.py`
- [ ] Task 2.3: Crear `src/services/auth_service.py`
- [ ] Task 2.4: Crear tests para servicios

### Fase 3: Componentes UI
- [ ] Task 3.1: Crear `src/components/otp_input.py`
- [ ] Task 3.2: Crear `src/components/neon_button.py`
- [ ] Task 3.3: Crear `src/kv/components.kv`

### Fase 4: Pantallas de Autenticación
- [ ] Task 4.1: Crear `src/screens/splash_screen.py` + `splash.kv`
- [ ] Task 4.2: Crear `src/screens/login_screen.py` + `login.kv`
- [ ] Task 4.3: Crear `src/screens/otp_screen.py` + `otp.kv`
- [ ] Task 4.4: Crear `src/screens/dashboard_screen.py`

### Fase 5: Integración y Testing
- [ ] Task 5.1: Conectar flujo completo
- [ ] Task 5.2: Probar en desktop
- [ ] Task 5.3: Configurar GitHub Actions workflow
- [ ] Task 5.4: Documentar README.md

---

## 🚀 DETALLE DE TAREAS

### Task 0.3: Crear `requirements-android.txt`

**Files:**
- Create: `android_app/requirements-android.txt`

**Step 1: Crear archivo con dependencias (versiones corregidas)**

```txt
# Core
kivy==2.3.0
kivymd==2.0.1.dev0

# Async support for Kivy
asynckivy==0.4.0

# HTTP
httpx==0.27.0

# Security
cryptography==46.0.5
keyring==24.3.0
certifi==2024.2.2

# Validation
pydantic==2.12.5

# Utilities
qrcode==7.4.2
Pillow==12.1.1
loguru==0.7.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
```

**Step 2: Commit**

```bash
git add android_app/requirements-android.txt
git commit -m "chore: agregar requirements-android.txt"
```

---

### Task 0.4: Crear `main.py` entry point

**Files:**
- Create: `android_app/main.py`

**Step 1: Crear entry point de Kivy**

```python
"""
uSipipo VPN - Android APK
Entry point for Kivy application.
"""
from src.app import uSipipoApp

if __name__ == '__main__':
    app = uSipipoApp()
    app.run()
```

**Step 2: Verificar que importa correctamente**

```bash
cd android_app
source venv/bin/activate  # si existe
python -c "from src.app import uSipipoApp; print('OK')"
```

**Step 3: Commit**

```bash
git add android_app/main.py
git commit -m "feat: agregar entry point main.py"
```

---

### Task 0.5: Crear `app.py` con MDApp y ScreenManager

**Files:**
- Create: `android_app/src/app.py`

**Step 1: Crear clase principal de la app (colores importados de config.py)**

```python
"""
Main application class for uSipipo VPN Android APK.
"""
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from loguru import logger
import os

# Importar configuración y colores desde config.py
from src.config import COLORS


class uSipipoApp(MDApp):
    """Main application class."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.accent_palette = "Pink"
        self.screen_manager = None

    def build(self):
        """Build the application."""
        self.title = "uSipipo VPN"
        
        # Configurar colores globales desde config.py (NO duplicar)
        for color_name, color_value in COLORS.items():
            self.theme_cls.colors[color_name] = color_value

        # Crear screen manager
        self.screen_manager = MDScreenManager()
        
        # Cargar archivos KV
        self._load_kv_files()
        
        # Registrar pantallas (se irán agregando en tareas futuras)
        # self.screen_manager.add_widget(SplashScreen(name="splash"))
        # self.screen_manager.add_widget(LoginScreen(name="login"))
        # etc.

        logger.info("uSipipoApp construida exitosamente")
        return self.screen_manager

    def _load_kv_files(self):
        """Load all KV files from kv directory."""
        kv_dir = os.path.join(os.path.dirname(__file__), "kv")
        for kv_file in os.listdir(kv_dir):
            if kv_file.endswith(".kv"):
                kv_path = os.path.join(kv_dir, kv_file)
                logger.debug(f"Cargando KV: {kv_path}")
                Builder.load_file(kv_path)

    def on_start(self):
        """Called when the app is started."""
        logger.info("uSipipoApp iniciada")

    def on_stop(self):
        """Called when the app is stopped."""
        logger.info("uSipipoApp detenida")


if __name__ == "__main__":
    app = uSipipoApp()
    app.run()
```

**Step 2: Verificar que la app se puede instanciar**

```bash
cd android_app
python -c "from src.app import uSipipoApp; app = uSipipoApp(); print('App OK')"
```

**Step 3: Commit**

```bash
git add android_app/src/app.py
git commit -m "feat: crear clase principal uSipipoApp con MDApp"
```

---

### Task 1.3: Crear `src/config.py` con configuración

**Files:**
- Create: `android_app/src/config.py`

**Step 1: Crear configuración de la APK**

```python
"""
Configuration for uSipipo VPN Android APK.
"""
import os

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
```

**Step 2: Commit**

```bash
git add android_app/src/config.py
git commit -m "feat: agregar configuración de la APK"
```

---

### Task 2.1: Crear `src/storage/secure_storage.py`

**Files:**
- Create: `android_app/src/storage/secure_storage.py`
- Test: `android_app/tests/test_secure_storage.py`

**Step 1: Crear almacenamiento seguro para JWT**

```python
"""
Secure storage for JWT tokens using Android Keystore via keyring.
"""
import keyring
from loguru import logger
from typing import Optional

from src.config import JWT_STORAGE_SERVICE


class SecureStorage:
    """Secure storage using Android Keystore."""

    SERVICE_NAME = JWT_STORAGE_SERVICE

    @staticmethod
    def save_jwt(telegram_id: str, jwt_token: str) -> None:
        """Save JWT token securely."""
        try:
            keyring.set_password(SecureStorage.SERVICE_NAME, telegram_id, jwt_token)
            logger.info(f"JWT guardado para usuario {telegram_id}")
        except Exception as e:
            logger.error(f"Error guardando JWT: {e}")
            raise

    @staticmethod
    def get_jwt(telegram_id: str) -> Optional[str]:
        """Retrieve JWT token securely."""
        try:
            token = keyring.get_password(SecureStorage.SERVICE_NAME, telegram_id)
            if token:
                logger.debug(f"JWT recuperado para usuario {telegram_id}")
            return token
        except Exception as e:
            logger.error(f"Error recuperando JWT: {e}")
            return None

    @staticmethod
    def delete_jwt(telegram_id: str) -> None:
        """Delete JWT token securely."""
        try:
            keyring.delete_password(SecureStorage.SERVICE_NAME, telegram_id)
            logger.info(f"JWT eliminado para usuario {telegram_id}")
        except Exception as e:
            logger.error(f"Error eliminando JWT: {e}")
            raise

    @staticmethod
    def clear_all() -> None:
        """Clear all stored tokens (for logout)."""
        # Nota: keyring no tiene método para listar todas las claves
        # El caller debe pasar el telegram_id específico
        pass
```

**Step 2: Crear test para secure_storage**

```python
"""Tests for secure_storage module."""
import pytest
from src.storage.secure_storage import SecureStorage


class TestSecureStorage:
    """Test secure storage operations."""

    def test_save_and_get_jwt(self):
        """Test saving and retrieving JWT."""
        telegram_id = "test_user_123"
        jwt_token = "test.jwt.token.here"

        # Save
        SecureStorage.save_jwt(telegram_id, jwt_token)

        # Get
        retrieved = SecureStorage.get_jwt(telegram_id)
        assert retrieved == jwt_token

        # Cleanup
        SecureStorage.delete_jwt(telegram_id)

    def test_get_nonexistent_jwt(self):
        """Test retrieving non-existent JWT."""
        token = SecureStorage.get_jwt("nonexistent_user")
        assert token is None

    def test_delete_jwt(self):
        """Test deleting JWT."""
        telegram_id = "test_user_456"
        jwt_token = "another.test.token"

        # Save then delete
        SecureStorage.save_jwt(telegram_id, jwt_token)
        SecureStorage.delete_jwt(telegram_id)

        # Verify deleted
        token = SecureStorage.get_jwt(telegram_id)
        assert token is None
```

**Step 3: Ejecutar tests**

```bash
cd android_app
pytest tests/test_secure_storage.py -v
```

**Step 4: Commit**

```bash
git add android_app/src/storage/ android_app/tests/test_secure_storage.py
git commit -m "feat: crear secure_storage para JWT con keyring"
```

---

### Task 2.2: Crear `src/services/api_client.py`

**Files:**
- Create: `android_app/src/services/api_client.py`
- Test: `android_app/tests/test_api_client.py`

**Step 1: Crear cliente HTTP asíncrono**

```python
"""
HTTP client for API communication with JWT handling.
"""
import httpx
from loguru import logger
from typing import Optional, Dict, Any

from src.config import BASE_URL, REQUEST_TIMEOUT
from src.storage.secure_storage import SecureStorage


class ApiClient:
    """Async HTTP client with automatic JWT injection."""

    def __init__(self, telegram_id: Optional[str] = None):
        self.base_url = BASE_URL
        self.telegram_id = telegram_id
        self.timeout = REQUEST_TIMEOUT

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with JWT token if available."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.telegram_id:
            token = SecureStorage.get_jwt(self.telegram_id)
            if token:
                headers["Authorization"] = f"Bearer {token}"

        return headers

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        use_auth: bool = False
    ) -> Dict[str, Any]:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        headers = await self._get_headers() if use_auth else {}

        logger.debug(f"POST {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise

    async def get(
        self,
        endpoint: str,
        use_auth: bool = False
    ) -> Dict[str, Any]:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        headers = await self._get_headers() if use_auth else {}

        logger.debug(f"GET {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise
```

**Step 2: Crear test para api_client**

```python
"""Tests for api_client module."""
import pytest
import pytest_asyncio
from src.services.api_client import ApiClient


class TestApiClient:
    """Test API client operations."""

    @pytest.mark.asyncio
    async def test_api_client_initialization(self):
        """Test API client initializes correctly."""
        client = ApiClient(telegram_id="123456")
        assert client.base_url is not None
        assert client.telegram_id == "123456"
        assert client.timeout == 30
```

**Step 3: Commit**

```bash
git add android_app/src/services/ android_app/tests/test_api_client.py
git commit -m "feat: crear ApiClient HTTP asíncrono"
```

---

### Task 2.3: Crear `src/services/auth_service.py`

**Files:**
- Create: `android_app/src/services/auth_service.py`
- Create: `android_app/src/storage/preferences_storage.py`
- Test: `android_app/tests/test_auth_service.py`

**Step 1: Crear preferences storage para último usuario**

```python
"""
Preferences storage for non-sensitive app preferences.
Uses JSON file for simple key-value storage.
"""
import json
import os
from loguru import logger

from src.config import APP_DATA_DIR


class PreferencesStorage:
    """Storage for app preferences (non-sensitive data)."""

    FILE_PATH = os.path.join(APP_DATA_DIR, "preferences.json")

    @staticmethod
    def _ensure_dir():
        """Ensure data directory exists."""
        os.makedirs(APP_DATA_DIR, exist_ok=True)

    @staticmethod
    def _read() -> dict:
        """Read preferences from file."""
        PreferencesStorage._ensure_dir()
        if not os.path.exists(PreferencesStorage.FILE_PATH):
            return {}
        try:
            with open(PreferencesStorage.FILE_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @staticmethod
    def _write(data: dict) -> None:
        """Write preferences to file."""
        PreferencesStorage._ensure_dir()
        with open(PreferencesStorage.FILE_PATH, "w") as f:
            json.dump(data, f)

    @staticmethod
    def get_last_user_id() -> str | None:
        """Get last logged-in user telegram_id."""
        data = PreferencesStorage._read()
        return data.get("last_telegram_id")

    @staticmethod
    def set_last_user_id(telegram_id: str) -> None:
        """Set last logged-in user telegram_id."""
        data = PreferencesStorage._read()
        data["last_telegram_id"] = telegram_id
        PreferencesStorage._write(data)
        logger.debug(f"Last user ID saved: {telegram_id}")

    @staticmethod
    def clear() -> None:
        """Clear all preferences."""
        if os.path.exists(PreferencesStorage.FILE_PATH):
            os.remove(PreferencesStorage.FILE_PATH)
```

**Step 2: Actualizar `config.py` con APP_DATA_DIR**

```python
# Agregar al inicio de config.py
import os

# Data directory for app preferences
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".usipipo_apk")
```

**Step 3: Crear servicio de autenticación corregido**

```python
"""
Authentication service for OTP and JWT management.
"""
from loguru import logger
from typing import Optional, Dict, Any

from src.services.api_client import ApiClient
from src.storage.secure_storage import SecureStorage
from src.storage.preferences_storage import PreferencesStorage
from src.config import OTP_LENGTH


class AuthService:
    """Service for handling authentication flow."""

    def __init__(self):
        self.api_client = ApiClient()
        # NO usar class attribute - cada instancia tiene su propio estado
        self._current_telegram_id: Optional[str] = None

    @property
    def current_telegram_id(self) -> Optional[str]:
        """Get current telegram_id from memory or preferences."""
        if self._current_telegram_id:
            return self._current_telegram_id
        # Fallback a preferences si no está en memoria
        return PreferencesStorage.get_last_user_id()

    @current_telegram_id.setter
    def current_telegram_id(self, value: str) -> None:
        """Set current telegram_id and persist to preferences."""
        self._current_telegram_id = value
        PreferencesStorage.set_last_user_id(value)

    async def request_otp(self, identifier: str) -> Dict[str, Any]:
        """
        Request OTP code for authentication.

        Args:
            identifier: Telegram username (@user) or telegram_id

        Returns:
            Response with message and expires_in_seconds
        """
        logger.info(f"Solicitando OTP para {identifier}")

        response = await self.api_client.post(
            "/auth/request-otp",
            data={"identifier": identifier}
        )

        logger.info("OTP solicitado exitosamente")
        return response

    async def verify_otp(
        self,
        identifier: str,
        otp_code: str
    ) -> Dict[str, Any]:
        """
        Verify OTP code and receive JWT token.

        Args:
            identifier: Telegram username or telegram_id
            otp_code: 6-digit OTP code

        Returns:
            Response with access_token and user info
        """
        logger.info(f"Verificando OTP para {identifier}")

        response = await self.api_client.post(
            "/auth/verify-otp",
            data={
                "identifier": identifier,
                "otp": otp_code
            }
        )

        # Guardar JWT si la verificación es exitosa
        if "access_token" in response:
            telegram_id = str(response["user"]["telegram_id"])
            self.current_telegram_id = telegram_id
            SecureStorage.save_jwt(
                telegram_id,
                response["access_token"]
            )
            logger.info(f"JWT guardado para usuario {telegram_id}")

        return response

    async def logout(self) -> None:
        """Logout and clear JWT token."""
        telegram_id = self.current_telegram_id
        if telegram_id:
            # Llamar al endpoint de logout
            try:
                self.api_client.telegram_id = telegram_id
                await self.api_client.post(
                    "/auth/logout",
                    data={},
                    use_auth=True
                )
            except Exception as e:
                logger.warning(f"Error en logout del backend: {e}")

            # Limpiar JWT local y preferences
            SecureStorage.delete_jwt(telegram_id)
            PreferencesStorage.clear()
            self._current_telegram_id = None
            logger.info("Logout completado")

    async def is_authenticated(self) -> bool:
        """Check if user has valid JWT token."""
        telegram_id = self.current_telegram_id
        if not telegram_id:
            return False

        token = SecureStorage.get_jwt(telegram_id)
        if not token:
            return False

        # TODO: Validar expiración del JWT decodificando el payload
        # Por ahora, solo verificamos que existe el token
        return True

    def get_current_user(self) -> Optional[str]:
        """Get current authenticated user telegram_id."""
        return self.current_telegram_id
```

**Step 2: Commit**

```bash
git add android_app/src/services/auth_service.py
git commit -m "feat: crear AuthService para flujo OTP"
```

---

### Task 4.1: Crear `src/screens/splash_screen.py` + `splash.kv`

**Files:**
- Create: `android_app/src/screens/splash_screen.py`
- Create: `android_app/src/kv/splash.kv`

**Step 1: Crear pantalla de splash (corregida con AuthService en instancia)**

```python
"""
Splash screen for uSipipo VPN Android APK.
"""
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from loguru import logger
import asynckivy as ak

from src.services.auth_service import AuthService


class SplashScreen(MDScreen):
    """Splash screen with logo and automatic auth check."""

    logo_text = StringProperty("uSipipo VPN")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Instancia única - NO class attribute
        self.auth_service = AuthService()

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Splash screen: verificando autenticación")
        # Verificar autenticación después de breve delay para animación
        ak.start(self._check_auth_async())

    async def _check_auth_async(self):
        """Async auth check."""
        # Esperar 1.5 segundos para mostrar el splash
        await ak.sleep(1.5)

        is_auth = await self.auth_service.is_authenticated()

        if is_auth:
            logger.info("Usuario autenticado, yendo al dashboard")
            self.manager.current = "dashboard"
        else:
            logger.info("Usuario no autenticado, yendo al login")
            self.manager.current = "login"

    def on_leave(self):
        """Called when screen is left."""
        pass
```

**Step 2: Crear diseño KV para splash**

```kv
#:import HexColor kivy.utils.HexColor

<SplashScreen>:
    name: "splash"

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_cls.bg_darkest if hasattr(app.theme_cls, 'bg_darkest') else HexColor("#0a0a0f")
        padding: "20dp"
        spacing: "20dp"

        # Logo area
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            pos_hint: {"center_x": 0.5}

            # Logo icon (placeholder - usar Image con logo real)
            MDIcon:
                icon: "shield-account"
                font_size: "96sp"
                theme_text_color: "Custom"
                text_color: app.theme_cls.accent_color if hasattr(app.theme_cls, 'accent_color') else HexColor("#00f0ff")
                pos_hint: {"center_x": 0.5}
                size_hint_x: None
                width: self.texture_size[0]

            # App name
            MDLabel:
                text: root.logo_text
                font_style: "Headline"
                halign: "center"
                theme_text_color: "Custom"
                text_color: app.theme_cls.accent_color if hasattr(app.theme_cls, 'accent_color') else HexColor("#00f0ff")
                size_hint_y: None
                height: self.texture_size[1]
                font_name: "JetBrainsMono-Bold" if app.get_source_path("assets/fonts/JetBrainsMono-Bold.ttf") else "Roboto"

            # Tagline
            MDLabel:
                text: "VPN Manager"
                font_style: "Subtitle"
                halign: "center"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: self.texture_size[1]

        # Loading indicator
        MDBoxLayout:
            size_hint_y: None
            height: "50dp"
            pos_hint: {"center_x": 0.5}

            MDSpinner:
                size_hint: None, None
                size: "46dp", "46dp"
                pos_hint: {"center_x": 0.5}
                active: True
```

**Step 3: Commit**

```bash
git add android_app/src/screens/splash_screen.py android_app/src/kv/splash.kv
git commit -m "feat: crear SplashScreen con verificación de auth"
```

---

### Task 4.2: Crear `src/screens/login_screen.py` + `login.kv`

**Files:**
- Create: `android_app/src/screens/login_screen.py`
- Create: `android_app/src/kv/login.kv`

**Step 1: Crear pantalla de login (corregida con asynckivy)**

```python
"""
Login screen for uSipipo VPN Android APK.
"""
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton
from kivymd.uix.button import MDButtonText
from loguru import logger
import asynckivy as ak

from src.services.auth_service import AuthService


class LoginScreen(MDScreen):
    """Login screen for entering Telegram identifier."""

    identifier_text = StringProperty("")
    is_loading = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Instancia única por pantalla - NO class attribute
        self.auth_service = AuthService()
        self.dialog = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Login screen: listo para ingresar identificador")

    def validate_identifier(self, identifier: str) -> bool:
        """Validate Telegram identifier format."""
        identifier = identifier.strip()

        if not identifier:
            self.show_error("El identificador no puede estar vacío")
            return False

        if identifier.startswith("@"):
            # Username: 5-32 caracteres alfanuméricos + guiones bajos
            username = identifier[1:]
            if not (5 <= len(username) <= 32):
                self.show_error("Username debe tener 5-32 caracteres")
                return False
            if not all(c.isalnum() or c == '_' for c in username):
                self.show_error("Username solo puede contener letras, números y guiones bajos")
                return False
        else:
            # Telegram ID: debe ser numérico
            if not identifier.isdigit():
                self.show_error("Debe ser username (@usuario) o telegram_id válido")
                return False

        return True

    def send_otp(self):
        """Send OTP to the provided identifier (sync wrapper for async)."""
        ak.start(self._send_otp_async())

    async def _send_otp_async(self):
        """Async implementation of send_otp."""
        identifier = self.ids.identifier_input.text.strip()

        if not self.validate_identifier(identifier):
            return

        self.is_loading = True

        try:
            response = await self.auth_service.request_otp(identifier)
            logger.info(f"OTP enviado: {response.get('message')}")

            # Guardar identifier para usar en verificación
            self.auth_service.current_telegram_id = identifier

            # Navegar a pantalla OTP
            self.manager.current = "otp"

        except Exception as e:
            logger.error(f"Error solicitando OTP: {e}")
            self.show_error(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def show_error(self, message: str):
        """Show error dialog with close button."""
        dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDButton(
                    MDButtonText(text="Cerrar"),
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        dialog.open()

    def on_leave(self):
        """Called when screen is left."""
        if self.dialog:
            self.dialog.dismiss()
```

**Step 2: Crear diseño KV para login**

```kv
#:import HexColor kivy.utils.HexColor

<LoginScreen>:
    name: "login"

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_cls.bg_darkest if hasattr(app.theme_cls, 'bg_darkest') else HexColor("#0a0a0f")
        padding: "20dp"
        spacing: "20dp"

        # Header
        MDLabel:
            text: "Iniciar Sesión"
            font_style: "Headline"
            theme_text_color: "Custom"
            text_color: app.theme_cls.accent_color if hasattr(app.theme_cls, 'accent_color') else HexColor("#00f0ff")
            size_hint_y: None
            height: self.texture_size[1]

        MDLabel:
            text: "Ingresa tu @username o telegram_id de Telegram"
            font_style: "Body"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: self.texture_size[1]

        MDLabel:
            text: "Debes tener una cuenta activa en @uSipipoBot"
            font_style: "Caption"
            theme_text_color: "Hint"
            size_hint_y: None
            height: self.texture_size[1]

        # Identifier input
        MDTextField:
            id: identifier_input
            hint_text: "@username o telegram_id"
            mode: "rectangle"
            size_hint_y: None
            height: "56dp"
            icon_left: "account"

        # Send button
        MDRaisedButton:
            text: "Enviar Código"
            size_hint_x: 1
            size_hint_y: None
            height: "48dp"
            disabled: root.is_loading
            on_release: root.send_otp()

            MDBoxLayout:
                MDSpinner:
                    size_hint: None, None
                    size: "20dp", "20dp"
                    active: root.is_loading
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}

                MDLabel:
                    text: "Enviando..." if root.is_loading else "Enviar Código"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: [0, 0, 0, 1] if not root.is_loading else [0.5, 0.5, 0.5, 1]
```

**Step 3: Commit**

```bash
git add android_app/src/screens/login_screen.py android_app/src/kv/login.kv
git commit -m "feat: crear LoginScreen para ingreso de identificador"
```

---

### Task 4.3: Crear `src/screens/otp_screen.py` + `otp.kv`

**Files:**
- Create: `android_app/src/screens/otp_screen.py`
- Create: `android_app/src/kv/otp.kv`

**Step 1: Crear pantalla OTP (corregida con asynckivy y sin class attributes)**

```python
"""
OTP verification screen for uSipipo VPN Android APK.
"""
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton
from kivymd.uix.button import MDButtonText
from kivymd.uix.snackbar import Snackbar
from loguru import logger
import asynckivy as ak

from src.services.auth_service import AuthService


class OtpScreen(MDScreen):
    """OTP verification screen with 6-digit input."""

    is_loading = BooleanProperty(False)
    countdown = StringProperty("05:00")
    can_resend = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Instancia única - NO class attribute
        self.auth_service = AuthService()
        self._countdown_seconds = 300  # Se resetea en on_enter
        self._clock_event = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("OTP screen: esperando código")
        # Resetear countdown cada vez que entra
        self._countdown_seconds = 300
        self.start_countdown()

    def start_countdown(self):
        """Start countdown timer."""
        self.can_resend = False
        self.update_countdown_display()

        if self._clock_event:
            self._clock_event.cancel()

        self._clock_event = Clock.schedule_interval(self.tick, 1)

    def tick(self, dt):
        """Decrement countdown."""
        self._countdown_seconds -= 1

        if self._countdown_seconds <= 0:
            self.can_resend = True
            self.countdown = "00:00"
            if self._clock_event:
                self._clock_event.cancel()
        else:
            self.update_countdown_display()

    def update_countdown_display(self):
        """Update countdown display."""
        minutes = self._countdown_seconds // 60
        seconds = self._countdown_seconds % 60
        self.countdown = f"{minutes:02d}:{seconds:02d}"

    def verify_otp(self):
        """Verify OTP code (sync wrapper)."""
        ak.start(self._verify_otp_async())

    async def _verify_otp_async(self):
        """Async implementation of verify_otp."""
        # Concatenar los 6 campos
        otp = "".join([self.ids[f"otp_{i}"].text for i in range(1, 7)])

        if len(otp) != 6 or not otp.isdigit():
            self.show_error("El código debe tener 6 dígitos")
            return

        self.is_loading = True

        try:
            identifier = self.auth_service.current_telegram_id
            response = await self.auth_service.verify_otp(identifier, otp)

            logger.info(f"OTP verificado: {response.get('user', {}).get('telegram_id')}")

            # Navegar al dashboard
            self.manager.current = "dashboard"

        except Exception as e:
            logger.error(f"Error verificando OTP: {e}")
            self.show_error(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def resend_otp(self):
        """Resend OTP code (sync wrapper)."""
        if not self.can_resend:
            return
        ak.start(self._resend_otp_async())

    async def _resend_otp_async(self):
        """Async implementation of resend_otp."""
        self.is_loading = True

        try:
            identifier = self.auth_service.current_telegram_id
            await self.auth_service.request_otp(identifier)
            logger.info("OTP reenviado")
            self.start_countdown()
            self.show_info("Nuevo código enviado")

        except Exception as e:
            logger.error(f"Error reenviando OTP: {e}")
            self.show_error(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def show_error(self, message: str):
        """Show error dialog with close button."""
        dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDButton(
                    MDButtonText(text="Cerrar"),
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        dialog.open()

    def show_info(self, message: str):
        """Show info snackbar."""
        Snackbar(text=message).open()

    def on_leave(self):
        """Called when screen is left."""
        if self._clock_event:
            self._clock_event.cancel()
```

**Step 2: Crear diseño KV para OTP**

```kv
#:import HexColor kivy.utils.HexColor

<OtpScreen>:
    name: "otp"

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: app.theme_cls.bg_darkest if hasattr(app.theme_cls, 'bg_darkest') else HexColor("#0a0a0f")
        padding: "20dp"
        spacing: "20dp"

        # Header
        MDLabel:
            text: "Verificar Código"
            font_style: "Headline"
            theme_text_color: "Custom"
            text_color: app.theme_cls.accent_color if hasattr(app.theme_cls, 'accent_color') else HexColor("#00f0ff")
            size_hint_y: None
            height: self.texture_size[1]

        MDLabel:
            text: "Ingresa el código de 6 dígitos que te enviamos a Telegram"
            font_style: "Body"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: self.texture_size[1]

        # Countdown timer
        MDLabel:
            text: root.countdown
            font_style: "H5"
            theme_text_color: "Custom"
            text_color: HexColor("#ff9500") if root._countdown_seconds < 60 else (HexColor("#00f0ff") if not root.can_resend else HexColor("#ff4444"))
            halign: "center"
            size_hint_y: None
            height: self.texture_size[1]
            font_name: "JetBrainsMono-Bold"

        # OTP input (6 individual fields - placeholder implementation)
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "60dp"
            spacing: "10dp"
            pos_hint: {"center_x": 0.5}

            # 6 single-digit inputs (simplified - en producción usar widget personalizado)
            MDTextField:
                id: otp_1
                hint_text: "1"
                max_text_length: 1
                mode: "rectangle"
                size_hint_x: None
                width: "40dp"
                halign: "center"

            MDTextField:
                id: otp_2
                hint_text: "2"
                max_text_length: 1
                mode: "rectangle"
                size_hint_x: None
                width: "40dp"
                halign: "center"

            MDTextField:
                id: otp_3
                hint_text: "3"
                max_text_length: 1
                mode: "rectangle"
                size_hint_x: None
                width: "40dp"
                halign: "center"

            MDTextField:
                id: otp_4
                hint_text: "4"
                max_text_length: 1
                mode: "rectangle"
                size_hint_x: None
                width: "40dp"
                halign: "center"

            MDTextField:
                id: otp_5
                hint_text: "5"
                max_text_length: 1
                mode: "rectangle"
                size_hint_x: None
                width: "40dp"
                halign: "center"

            MDTextField:
                id: otp_6
                hint_text: "6"
                max_text_length: 1
                mode: "rectangle"
                size_hint_x: None
                width: "40dp"
                halign: "center"

        # Verify button
        MDRaisedButton:
            text: "Verificar"
            size_hint_x: 1
            size_hint_y: None
            height: "48dp"
            disabled: root.is_loading
            on_release:
                otp = "".join([root.ids[f"otp_{i}"].text for i in range(1, 7)])
                root.verify_otp(otp)

        # Resend link (usar MDTextButton, no MDLabel con on_touch_down)
        MDBoxLayout:
            size_hint_y: None
            height: "40dp"
            pos_hint: {"center_x": 0.5}

        MDLabel:
            text: "¿No recibiste el código? "
            theme_text_color: "Secondary"
            size_hint_x: None
            width: self.texture_size[0]

        MDTextButton:
            text: "Reenviar"
            disabled: not root.can_resend or root.is_loading
            on_release: root.resend_otp()
            size_hint_x: None
            width: self.texture_size[0]
```

**Step 3: Commit**

```bash
git add android_app/src/screens/otp_screen.py android_app/src/kv/otp.kv
git commit -m "feat: crear OtpScreen para verificación de código"
```

---

### Task 4.4: Crear `src/screens/dashboard_screen.py` (placeholder)

**Files:**
- Create: `android_app/src/screens/dashboard_screen.py`
- Create: `android_app/src/kv/dashboard.kv`

**Step 1: Crear pantalla dashboard (placeholder)**

```python
"""
Dashboard screen (placeholder) for uSipipo VPN Android APK.
"""
from kivymd.uix.screen import MDScreen
from loguru import logger


class DashboardScreen(MDScreen):
    """Dashboard screen - placeholder for future implementation."""

    def on_enter(self):
        """Called when screen is entered."""
        logger.info("Dashboard screen: placeholder - próximamente")

    def on_leave(self):
        """Called when screen is left."""
        pass
```

**Step 2: Crear diseño KV simple**

```kv
<DashboardScreen>:
    name: "dashboard"

    MDBoxLayout:
        orientation: "vertical"
        padding: "20dp"
        spacing: "20dp"

        MDLabel:
            text: "Dashboard"
            font_style: "Headline"
            halign: "center"
            size_hint_y: None
            height: self.texture_size[1]

        MDLabel:
            text: "Próximamente..."
            font_style: "Body"
            halign: "center"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: self.texture_size[1]
```

**Step 3: Commit**

```bash
git add android_app/src/screens/dashboard_screen.py android_app/src/kv/dashboard.kv
git commit -m "feat: crear DashboardScreen placeholder"
```

---

### Task 5.1: Conectar flujo completo en `app.py`

**Files:**
- Modify: `android_app/src/app.py`

**Step 1: Actualizar app.py para registrar pantallas**

```python
# Agregar al inicio de app.py
from src.screens.splash_screen import SplashScreen
from src.screens.login_screen import LoginScreen
from src.screens.otp_screen import OtpScreen
from src.screens.dashboard_screen import DashboardScreen

# Modificar el método build()
def build(self):
    """Build the application."""
    self.title = "uSipipo VPN"

    # Configurar colores globales
    for color_name, color_value in CYBERPUNK_COLORS.items():
        self.theme_cls.colors[color_name] = color_value

    # Crear screen manager
    self.screen_manager = MDScreenManager()

    # Registrar pantallas
    self.screen_manager.add_widget(SplashScreen(name="splash"))
    self.screen_manager.add_widget(LoginScreen(name="login"))
    self.screen_manager.add_widget(OtpScreen(name="otp"))
    self.screen_manager.add_widget(DashboardScreen(name="dashboard"))

    logger.info("uSipipoApp construida exitosamente")
    return self.screen_manager
```

**Step 2: Cargar archivos KV**

```python
# Agregar al inicio de app.py
from kivy.core.window import Window
from kivy.lang import Builder
import os

# Cargar archivos KV
KV_DIR = os.path.join(os.path.dirname(__file__), "kv")
for kv_file in os.listdir(KV_DIR):
    if kv_file.endswith(".kv"):
        Builder.load_file(os.path.join(KV_DIR, kv_file))
```

**Step 3: Probar la aplicación en desktop**

```bash
cd android_app
python main.py
```

**Step 4: Commit**

```bash
git add android_app/src/app.py
git commit -m "feat: conectar flujo completo de pantallas"
```

---

### Task 5.3: Configurar GitHub Actions workflow

**Files:**
- Create: `.github/workflows/build_apk.yml`

**Step 1: Crear workflow de compilación completo (con dependencias de sistema)**

```yaml
name: Build APK

on:
  push:
    tags:
      - 'apk-v*'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 360  # 6 horas máximo

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            openjdk-17-jdk \
            build-essential \
            autoconf \
            automake \
            libtool \
            libffi-dev \
            libssl-dev \
            zlib1g-dev \
            git \
            zip \
            unzip \
            wget
          java -version

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install buildozer cython==0.29.36

      - name: Cache Android SDK
        uses: actions/cache@v4
        with:
          path: |
            ~/.android
            ~/.gradle
          key: ${{ runner.os }}-android-sdk-${{ hashFiles('android_app/buildozer.spec') }}
          restore-keys: |
            ${{ runner.os }}-android-sdk-

      - name: Build APK (Debug)
        working-directory: android_app
        run: |
          buildozer android debug

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: usipipo-apk-debug
          path: android_app/bin/*.apk

      - name: Create Release (on tag)
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: android_app/bin/*.apk
          draft: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Step 2: Commit**

```bash
git add .github/workflows/build_apk.yml
git commit -m "ci: agregar workflow de compilación de APK"
```

---

### Task 5.4: Documentar README.md

**Files:**
- Create: `android_app/README.md`

**Step 1: Crear README del proyecto APK**

```markdown
# uSipipo VPN - Android APK

APK Android para gestión de VPN uSipipo, construida con Kivy + KivyMD.

## Requisitos de Desarrollo

- Python 3.11+
- Linux (para compilación con Buildozer)
- Android SDK/NDK (descargado automáticamente por Buildozer)

## Estructura del Proyecto

```
android_app/
├── main.py                 # Entry point
├── buildozer.spec          # Configuración de compilación
├── requirements-android.txt # Dependencias Python
├── src/
│   ├── app.py              # Clase principal MDApp
│   ├── config.py           # Configuración
│   ├── screens/            # Pantallas
│   ├── services/           # Servicios (API, auth)
│   ├── storage/            # Almacenamiento seguro
│   ├── components/         # Widgets personalizados
│   └── kv/                 # Archivos KV (diseños)
├── assets/
│   ├── fonts/              # Fuentes (JetBrains Mono, Roboto)
│   └── images/             # Imágenes (logo, íconos)
└── tests/                  # Tests unitarios
```

## Desarrollo en Desktop

```bash
# Instalar dependencias
pip install -r requirements-android.txt

# Ejecutar en desktop
python main.py
```

## Compilación de APK

### Debug (desarrollo)

```bash
buildozer android debug
```

El APK se genera en `bin/usipipo-1.0.0-debug.apk`

### Release (producción)

```bash
# Configurar keystore en buildozer.spec
buildozer android release
```

## Testing

```bash
pytest tests/ -v
```

## Flujo de Autenticación

1. **Splash Screen**: Verifica si hay JWT guardado
2. **Login Screen**: Ingresa @username o telegram_id
3. **OTP Screen**: Ingresa código de 6 dígitos
4. **Dashboard**: Pantalla principal (autenticado)

## Colores del Tema Cyberpunk

| Color | Hex | RGB |
|-------|-----|-----|
| bg-void | #0a0a0f | [0.039, 0.039, 0.059] |
| neon-cyan | #00f0ff | [0, 0.941, 1] |
| neon-magenta | #ff00aa | [1, 0, 0.667] |
| terminal-green | #00ff41 | [0, 1, 0.255] |

## Licencia

Propietario - uSipipo VPN
```

**Step 2: Commit**

```bash
git add android_app/README.md
git commit -m "docs: agregar README de la APK Android"
```

---

## ✅ Criterios de Aceptación - Módulo Auth Completo

Marcar solo si TODOS se cumplen:

- [ ] La APK compila sin errores (`buildozer android debug`)
- [ ] Splash screen muestra logo y verifica autenticación
- [ ] Login screen valida formato de identifier (@username o telegram_id)
- [ ] OTP screen tiene 6 campos para dígitos y contador regresivo
- [ ] El flujo completo funciona: Splash → Login → OTP → Dashboard
- [ ] JWT se guarda en Android Keystore (keyring)
- [ ] Los colores cyberpunk coinciden con la especificación
- [ ] Las fuentes JetBrains Mono se cargan correctamente
- [ ] Los tests unitarios pasan (`pytest tests/ -v`)
- [ ] GitHub Actions compila la APK exitosamente

---

*Plan creado: 2026-03-14*
*Actualizado: 2026-03-14 - Correcciones de bugs críticos aplicadas*

---

## 🔧 Correcciones Aplicadas (Code Review)

### Bugs Críticos Corregidos

1. **`AuthService` como class attribute** → Movido a `__init__()` en cada pantalla
2. **Async en Kivy sin `asynckivy`** → Agregado `asynckivy==0.4.0` y wrappers sync/async
3. **`is_authenticated()` siempre False** → Agregado `PreferencesStorage` para persistir último usuario
4. **`_countdown_seconds` class attribute** → Movido a instancia, reset en `on_enter()`

### Bugs de Build Corregidos

5. **GitHub Actions incompleto** → Agregadas todas las dependencias de sistema (openjdk-17, build-essential, etc.)
6. **Sin caché de Android SDK** → Agregado `actions/cache@v4` para SDK y Gradle

### Problemas de UX Corregidos

7. **`on_touch_down` en MDLabel** → Reemplazado con `MDTextButton` para resend OTP
8. **`MDDialog` sin botón de cierre** → Agregado botón "Cerrar" en todos los dialogs

### Mejoras de Calidad

9. **`loguru` faltante en requirements** → Agregada `loguru==0.7.2`
10. **Colores duplicados** → `app.py` ahora importa `COLORS` de `config.py`
11. **Versiones desactualizadas** → Actualizadas a versiones del repo principal (cryptography 46.0.5, pydantic 2.12.5, Pillow 12.1.1)

---

## ✅ Checklist Pre-Implementación

Antes de ejecutar este plan, verificar:

- [ ] Todas las correcciones anteriores están reflejadas en el código
- [ ] `asynckivy` está en `requirements-android.txt`
- [ ] `PreferencesStorage` está implementado antes que `AuthService`
- [ ] Las pantallas usan `ak.start()` para corrutinas async
- [ ] Los dialogs tienen botón de cierre
- [ ] El workflow de GitHub Actions tiene dependencias de sistema completas

