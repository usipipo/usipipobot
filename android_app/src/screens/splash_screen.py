"""
Splash screen for uSipipo VPN Android APK.
"""

import asynckivy as ak
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from loguru import logger
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
