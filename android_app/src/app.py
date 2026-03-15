"""
Main application class for uSipipo VPN Android APK.
"""

import os

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from loguru import logger

# Importar configuración y colores desde config.py
from src.config import COLORS
from src.screens.create_key_screen import CreateKeyScreen
from src.screens.create_key_success_screen import CreateKeySuccessScreen
from src.screens.dashboard_screen import DashboardScreen
from src.screens.key_detail_screen import KeyDetailScreen
from src.screens.keys_list_screen import KeysListScreen
from src.screens.login_screen import LoginScreen
from src.screens.otp_screen import OtpScreen

# Import screens
from src.screens.splash_screen import SplashScreen


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

        # Registrar pantallas
        self.screen_manager.add_widget(SplashScreen(name="splash"))
        self.screen_manager.add_widget(LoginScreen(name="login"))
        self.screen_manager.add_widget(OtpScreen(name="otp"))
        self.screen_manager.add_widget(DashboardScreen(name="dashboard"))
        self.screen_manager.add_widget(KeysListScreen(name="keys_list"))
        self.screen_manager.add_widget(KeyDetailScreen(name="key_detail"))
        self.screen_manager.add_widget(CreateKeyScreen(name="create_key"))
        self.screen_manager.add_widget(CreateKeySuccessScreen(name="create_key_success"))

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
