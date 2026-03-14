"""
Login screen for uSipipo VPN Android APK.
"""

import asynckivy as ak
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from loguru import logger
from src.services.auth_service import AuthService


class LoginScreen(MDScreen):
    """Login screen with Telegram identifier input."""

    identifier = StringProperty("")
    is_loading = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.dialog = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Login screen entered")
        # Pre-fill last user if available
        last_user = self.auth_service.current_telegram_id
        if last_user:
            self.ids.identifier_field.text = last_user

    def on_leave(self):
        """Called when screen is left."""
        pass

    def on_login_pressed(self):
        """Handle login button press."""
        identifier = self.ids.identifier_field.text.strip()

        if not identifier:
            self.show_error("Por favor ingresa tu usuario de Telegram")
            return

        # Validate format (@username or telegram_id)
        if not self.validate_identifier(identifier):
            self.show_error("Formato inválido. Usa @usuario o ID numérico")
            return

        # Request OTP
        self.is_loading = True
        ak.start(self.request_otp_async(identifier))

    async def request_otp_async(self, identifier: str):
        """Request OTP asynchronously."""
        try:
            response = await self.auth_service.request_otp(identifier)

            if response.get("success"):
                # Navigate to OTP screen
                otp_screen = self.manager.get_screen("otp")
                otp_screen.identifier = identifier
                otp_screen.expires_in = response.get("expires_in_seconds", 300)
                self.manager.current = "otp"
            else:
                self.show_error(response.get("message", "Error al solicitar OTP"))
        except Exception as e:
            logger.error(f"Error requesting OTP: {e}")
            self.show_error(f"Error de conexión: {str(e)}")
        finally:
            self.is_loading = False

    def validate_identifier(self, identifier: str) -> bool:
        """Validate Telegram identifier format."""
        # Allow @username format
        if identifier.startswith("@"):
            return len(identifier) > 1

        # Allow numeric telegram_id
        if identifier.isdigit():
            return len(identifier) >= 5

        return False

    def show_error(self, message: str):
        """Show error dialog."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="Error",
                text=message,
                buttons=[MDFlatButton(text="OK", on_release=self.dismiss_dialog)],
            )
        else:
            self.dialog.text = message
        self.dialog.open()

    def dismiss_dialog(self, instance):
        """Dismiss error dialog."""
        self.dialog.dismiss()

    def on_signup_pressed(self):
        """Handle signup button press."""
        # Open Telegram bot URL
        logger.info("Opening Telegram bot for signup")
        # This would use plyer or similar to open URL
        # For now, just show info
        self.show_info("Abre el bot de Telegram: @usipipo_bot")

    def show_info(self, message: str):
        """Show info dialog."""
        dialog = MDDialog(
            title="Información",
            text=message,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()
