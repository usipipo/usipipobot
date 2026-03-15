"""
OTP verification screen for uSipipo VPN Android APK.
"""

import asynckivy as ak
from kivy.clock import Clock
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from loguru import logger
from src.services.auth_service import AuthService


class OtpScreen(MDScreen):
    """OTP verification screen with countdown timer."""

    identifier = StringProperty("")
    expires_in = NumericProperty(300)  # 5 minutes default
    time_remaining = NumericProperty(300)
    is_loading = BooleanProperty(False)
    is_resending = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.dialog = None
        self._countdown_event = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug(f"OTP screen entered for {self.identifier}")
        self.time_remaining = self.expires_in
        self._start_countdown()
        # Focus OTP input
        Clock.schedule_once(lambda dt: self.ids.otp_input.focus_first(), 0.5)

    def on_leave(self):
        """Called when screen is left."""
        self._stop_countdown()

    def _start_countdown(self):
        """Start countdown timer."""
        self._stop_countdown()  # Stop any existing timer
        self._countdown_event = Clock.schedule_interval(self._update_countdown, 1)

    def _stop_countdown(self):
        """Stop countdown timer."""
        if self._countdown_event:
            self._countdown_event.cancel()
            self._countdown_event = None

    def _update_countdown(self, dt):
        """Update countdown timer."""
        self.time_remaining -= 1
        if self.time_remaining <= 0:
            self._stop_countdown()
            self.time_remaining = 0

    def get_time_display(self) -> str:
        """Get formatted time remaining display."""
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        return f"{minutes:02d}:{seconds:02d}"

    def on_otp_complete(self, otp):
        """Handle OTP input complete."""
        if len(otp) == 6 and not self.is_loading:
            self.verify_otp(otp)

    def on_verify_pressed(self):
        """Handle verify button press."""
        otp = self.ids.otp_input.otp
        if len(otp) != 6:
            self.show_error("Ingresa el código de 6 dígitos")
            return
        self.verify_otp(otp)

    def verify_otp(self, otp: str):
        """Verify OTP code."""
        self.is_loading = True
        ak.start(self.verify_otp_async(otp))

    async def verify_otp_async(self, otp: str):
        """Verify OTP asynchronously."""
        try:
            response = await self.auth_service.verify_otp(identifier=self.identifier, otp_code=otp)

            if response.get("access_token"):
                logger.info("OTP verificado exitosamente")
                # Navigate to dashboard
                self.manager.current = "dashboard"
            else:
                self.show_error(response.get("message", "Código inválido"))
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            self.show_error(f"Error de conexión: {str(e)}")
        finally:
            self.is_loading = False

    def on_resend_pressed(self):
        """Handle resend OTP button press."""
        if self.is_resending or self.time_remaining > 0:
            return

        self.is_resending = True
        ak.start(self.resend_otp_async())

    async def resend_otp_async(self):
        """Resend OTP asynchronously."""
        try:
            response = await self.auth_service.request_otp(self.identifier)

            if response.get("success"):
                self.time_remaining = response.get("expires_in_seconds", 300)
                self._start_countdown()
                self.ids.otp_input.clear()
                self.show_success("Código reenviado")
            else:
                self.show_error(response.get("message", "Error al reenviar"))
        except Exception as e:
            logger.error(f"Error resending OTP: {e}")
            self.show_error(f"Error de conexión: {str(e)}")
        finally:
            self.is_resending = False

    def on_back_pressed(self):
        """Handle back button press."""
        self.manager.current = "login"

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

    def show_success(self, message: str):
        """Show success dialog."""
        dialog = MDDialog(
            title="Éxito",
            text=message,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()
