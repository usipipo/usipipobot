"""
Dashboard screen for uSipipo VPN Android APK.
"""
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from loguru import logger

from src.services.auth_service import AuthService


class DashboardScreen(MDScreen):
    """Main dashboard screen after authentication."""

    username = StringProperty("Usuario")
    is_authenticated = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.dialog = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Dashboard screen entered")
        self.load_user_data()

    def on_leave(self):
        """Called when screen is left."""
        pass

    def load_user_data(self):
        """Load user data from auth service."""
        telegram_id = self.auth_service.get_current_user()
        if telegram_id:
            self.username = f"@{telegram_id}" if not telegram_id.isdigit() else f"User #{telegram_id}"
            self.is_authenticated = True
        else:
            self.is_authenticated = False
            # Redirect to login
            logger.warning("No authenticated user, redirecting to login")
            self.manager.current = "login"

    def on_logout_pressed(self):
        """Handle logout button press."""
        self.show_logout_confirmation()

    def show_logout_confirmation(self):
        """Show logout confirmation dialog."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="Cerrar Sesión",
                text="¿Estás seguro que deseas cerrar sesión?",
                buttons=[
                    MDFlatButton(
                        text="CANCELAR",
                        on_release=self.dismiss_dialog
                    ),
                    MDFlatButton(
                        text="SALIR",
                        on_release=self.confirm_logout
                    )
                ]
            )
        self.dialog.open()

    def dismiss_dialog(self, instance):
        """Dismiss dialog."""
        self.dialog.dismiss()

    def confirm_logout(self, instance):
        """Confirm and perform logout."""
        self.dialog.dismiss()
        self.dialog = None
        
        # Perform logout
        import asynckivy as ak
        ak.start(self.logout_async())

    async def logout_async(self):
        """Perform logout asynchronously."""
        try:
            await self.auth_service.logout()
            logger.info("Logout completado")
            self.manager.current = "splash"
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            self.manager.current = "splash"

    def on_profile_pressed(self):
        """Handle profile button press."""
        logger.info("Profile pressed - TODO: Navigate to profile screen")
        # TODO: Navigate to profile screen

    def on_keys_pressed(self):
        """Handle VPN keys button press."""
        logger.info("Keys pressed - TODO: Navigate to keys screen")
        # TODO: Navigate to keys screen

    def on_packages_pressed(self):
        """Handle data packages button press."""
        logger.info("Packages pressed - TODO: Navigate to packages screen")
        # TODO: Navigate to packages screen

    def on_support_pressed(self):
        """Handle support button press."""
        logger.info("Support pressed - TODO: Navigate to support screen")
        # TODO: Navigate to support screen
