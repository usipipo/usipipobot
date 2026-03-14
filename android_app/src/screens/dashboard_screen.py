"""
Dashboard screen for uSipipo VPN Android APK.
Main screen showing user summary, VPN keys, data usage, and quick actions.
"""
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.snackbar import Snackbar
from loguru import logger
from datetime import datetime
from typing import Optional, Dict, Any, List
import asyncio

from src.services.dashboard_service import DashboardService
from src.services.auth_service import AuthService
from src.storage.preferences_storage import PreferencesStorage


class DashboardScreen(MDScreen):
    """
    Main dashboard screen with complete user overview.

    Features:
    - Welcome card with user info
    - Data usage cards with progress bars
    - Active VPN keys summary
    - Referral credits display
    - Package status
    - Quick actions (New Key, Buy GB, Support)
    - Recent keys list
    - Pull-to-refresh
    - Bottom navigation
    - Auto-refresh every 60 seconds
    - Offline detection
    """

    # User properties
    username = StringProperty("Usuario")
    full_name = StringProperty("")
    user_avatar = StringProperty("")

    # Data properties
    data_used = StringProperty("0 GB")
    data_limit = StringProperty("5 GB")
    data_percentage = NumericProperty(0.0)
    data_progress_color = ListProperty([0, 0.941, 1, 1])  # neon_cyan

    # Keys properties
    active_keys_count = NumericProperty(0)
    max_keys = NumericProperty(2)
    recent_keys = ListProperty([])
    total_keys = NumericProperty(0)  # For "Ver todas" link

    # Package properties
    package_type = StringProperty("Sin paquete")
    package_days_remaining = StringProperty("")
    package_color = ListProperty([0.878, 0.878, 0.878, 1])  # text_primary

    # Referral properties
    referral_credits = NumericProperty(0)
    referral_count = NumericProperty(0)

    # Status properties
    is_authenticated = BooleanProperty(False)
    is_loading = BooleanProperty(True)
    is_suspended = BooleanProperty(False)
    has_pending_debt = BooleanProperty(False)
    consumption_mode_enabled = BooleanProperty(False)
    is_offline = BooleanProperty(False)

    # Last update
    last_update = StringProperty("")

    # Auto-refresh
    _auto_refresh_event = None
    _refresh_interval = 60  # seconds

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = AuthService()
        self.dashboard_service: Optional[DashboardService] = None
        self.dialog = None
        self.refresh_layout = None
        self._refresh_callback = None
        self._offline_check_event = None

    def on_enter(self):
        """Called when screen is entered."""
        logger.debug("Dashboard screen entered")
        self.load_dashboard_data()
        self._start_auto_refresh()
        self._start_offline_check()

    def on_leave(self):
        """Called when screen is left."""
        self._stop_auto_refresh()
        self._stop_offline_check()

    def _start_auto_refresh(self):
        """Start auto-refresh timer."""
        self._stop_auto_refresh()  # Cancel any existing timer
        self._auto_refresh_event = Clock.schedule_interval(
            lambda dt: self._auto_refresh_callback(),
            self._refresh_interval
        )
        logger.debug(f"Auto-refresh started (interval: {self._refresh_interval}s)")

    def _stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self._auto_refresh_event:
            self._auto_refresh_event.cancel()
            self._auto_refresh_event = None
            logger.debug("Auto-refresh stopped")

    def _auto_refresh_callback(self):
        """Callback for auto-refresh."""
        if not self.is_offline:
            logger.debug("Auto-refreshing dashboard data")
            self.load_dashboard_data(force_refresh=False)

    def _start_offline_check(self):
        """Start periodic offline check."""
        self._stop_offline_check()
        self._offline_check_event = Clock.schedule_interval(
            lambda dt: self._check_offline_status(),
            10  # Check every 10 seconds
        )

    def _stop_offline_check(self):
        """Stop offline check."""
        if self._offline_check_event:
            self._offline_check_event.cancel()
            self._offline_check_event = None

    def _check_offline_status(self):
        """Check if device is offline."""
        was_offline = self.is_offline
        self.is_offline = not self._has_internet_connection()
        
        if self.is_offline != was_offline:
            if self.is_offline:
                logger.warning("Device went offline")
                Snackbar(
                    text="Sin conexión. Los datos pueden no estar actualizados.",
                    duration=5,
                    bg_color=[1, 0.267, 0.267, 1]  # Red
                ).open()
            else:
                logger.info("Device back online")
                self.load_dashboard_data(force_refresh=True)

    def _has_internet_connection(self) -> bool:
        """
        Check if device has internet connection.
        
        Returns:
            True if online, False if offline
        """
        try:
            # Android-specific check
            from jnius import autoclass
            Context = autoclass('android.content.Context')
            ConnectivityManager = autoclass('android.net.ConnectivityManager')
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            cm = activity.getSystemService(Context.CONNECTIVITY_SERVICE)
            network_info = cm.getActiveNetworkInfo()
            return network_info is not None and network_info.isConnected()
        except Exception:
            # Desktop or error: assume online
            return True

    def setup_pull_to_refresh(self):
        """Setup pull-to-refresh layout."""
        # Get the refresh layout from KV if available
        if self.ids.get('refresh_layout'):
            self.refresh_layout = self.ids.refresh_layout
            logger.debug("Pull-to-refresh layout configured")

    def load_dashboard_data(self, force_refresh: bool = False):
        """
        Load dashboard data from API or cache.
        
        Args:
            force_refresh: If True, bypass cache and fetch from API
        """
        self.is_loading = True
        
        # Get current user
        telegram_id = self.auth_service.get_current_user()
        if not telegram_id:
            logger.warning("No authenticated user, redirecting to login")
            self.is_authenticated = False
            Clock.schedule_once(lambda dt: self._redirect_to_login(), 0.5)
            return
        
        self.is_authenticated = True
        self.dashboard_service = DashboardService(telegram_id=str(telegram_id))
        
        # Load data asynchronously
        Clock.schedule_once(lambda dt: self._fetch_dashboard(force_refresh), 0)

    def _redirect_to_login(self):
        """Redirect to login screen."""
        if self.manager:
            self.manager.current = "login"

    async def _fetch_dashboard_async(self, force_refresh: bool):
        """Fetch dashboard data asynchronously."""
        try:
            if force_refresh:
                data = await self.dashboard_service.refresh_dashboard()
            else:
                data = await self.dashboard_service.get_dashboard_summary()
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._update_dashboard(data))
            
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            Clock.schedule_once(lambda dt: self._handle_load_error(e))

    def _fetch_dashboard(self, force_refresh: bool = False):
        """Fetch dashboard data (async wrapper)."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._fetch_dashboard_async(force_refresh))
        
        with ThreadPoolExecutor() as executor:
            executor.submit(run_async)

    def _update_dashboard(self, data: Dict[str, Any]):
        """
        Update dashboard UI with fetched data.
        
        Args:
            data: Dashboard data from API
        """
        try:
            # User info
            user = data.get("user", {})
            self.username = user.get("username", "Usuario")
            self.full_name = user.get("full_name", "")
            self.user_avatar = user.get("photo_url", "")
            self.is_suspended = user.get("status") == "suspended"
            self.has_pending_debt = user.get("has_pending_debt", False)
            self.consumption_mode_enabled = user.get("consumption_mode_enabled", False)
            
            # Format last login
            last_login = user.get("last_login")
            if last_login:
                self.last_update = DashboardService.format_relative_time(last_login)
            else:
                self.last_update = "Nunca"
            
            # Data summary
            data_summary = data.get("data_summary", {})
            used_bytes = data_summary.get("total_used_bytes", 0)
            limit_bytes = data_summary.get("total_limit_bytes", 0)
            
            self.data_used = DashboardService.format_bytes(used_bytes)
            self.data_limit = DashboardService.format_bytes(limit_bytes)
            
            percentage = DashboardService.calculate_percentage(used_bytes, limit_bytes)
            self.data_percentage = percentage
            self.data_progress_color = self._get_progress_color(percentage)
            
            # Active keys
            active_keys = data.get("active_keys", [])
            self.active_keys_count = len([k for k in active_keys if k.get("is_active", False)])
            self.max_keys = data.get("max_keys", 2)  # Get from API or default
            self.total_keys = len(active_keys)  # For "Ver todas" link

            # Recent keys (max 3)
            self.recent_keys = []
            for key in active_keys[:3]:
                key_data = {
                    "id": key.get("id", ""),
                    "name": key.get("name", "Sin nombre"),
                    "type": key.get("key_type", "outline"),
                    "used": DashboardService.format_bytes(key.get("used_bytes", 0)),
                    "is_active": key.get("is_active", False),
                    "color": [0, 0.941, 1, 1] if key.get("key_type") == "outline" else [0.6, 0, 1, 1]
                }
                self.recent_keys.append(key_data)
            
            # Package info
            package = data.get("active_package")
            if package:
                pkg_type = package.get("package_type", "unknown")
                pkg_types = {
                    "basic": "Básico",
                    "standard": "Estándar",
                    "advanced": "Avanzado",
                    "premium": "Premium"
                }
                self.package_type = pkg_types.get(pkg_type, "Desconocido")
                
                days_remaining = package.get("days_remaining")
                if days_remaining is not None:
                    self.package_days_remaining = f"{days_remaining} días"
                    if days_remaining < 3:
                        self.package_color = [1, 0.267, 0.267, 1]  # red
                    elif days_remaining < 7:
                        self.package_color = [1, 0.584, 0, 1]  # amber
                    else:
                        self.package_color = [0, 1, 0.255, 1]  # green
                else:
                    self.package_days_remaining = ""
                    self.package_color = [0.878, 0.878, 0.878, 1]
            else:
                self.package_type = "Sin paquete"
                self.package_days_remaining = ""
                self.package_color = [0.541, 0.541, 0.604, 1]  # text_secondary
            
            # Referral credits
            self.referral_credits = data.get("referral_credits", 0)
            
            # Update UI state
            self.is_loading = False
            
            logger.debug("Dashboard updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            self._handle_load_error(e)

    def _get_progress_color(self, percentage: float) -> List[float]:
        """Get progress bar color based on percentage."""
        if percentage <= 60:
            return [0, 0.941, 1, 1]  # neon_cyan
        elif percentage <= 85:
            return [1, 0.584, 0, 1]  # amber
        else:
            return [1, 0.267, 0.267, 1]  # error

    def _handle_load_error(self, error: Exception):
        """Handle dashboard load error."""
        self.is_loading = False
        logger.error(f"Dashboard load error: {error}")
        
        # Show error snackbar
        Snackbar(
            text="Error cargando datos. Verifica tu conexión.",
            duration=3
        ).open()

    def on_refresh(self):
        """Handle pull-to-refresh action."""
        logger.info("Dashboard refresh requested")
        self.load_dashboard_data(force_refresh=True)
        
        # Reset pull-to-refresh layout
        if self.refresh_layout:
            self.refresh_layout.done()

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
                        theme_text_color="Custom",
                        text_color=[0, 0.941, 1, 1],
                        on_release=self.dismiss_dialog
                    ),
                    MDFlatButton(
                        text="SALIR",
                        theme_text_color="Custom",
                        text_color=[1, 0.267, 0.267, 1],
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
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def run_logout():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.logout_async())
        
        with ThreadPoolExecutor() as executor:
            executor.submit(run_logout)

    async def logout_async(self):
        """Perform logout asynchronously."""
        try:
            await self.auth_service.logout()
            logger.info("Logout completado")
            Clock.schedule_once(lambda dt: self._navigate_to_splash())
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            Clock.schedule_once(lambda dt: self._navigate_to_splash())

    def _navigate_to_splash(self):
        """Navigate to splash screen."""
        if self.manager:
            self.manager.current = "splash"

    def on_profile_pressed(self):
        """Handle profile button press."""
        logger.info("Navigating to profile screen")
        if self.manager:
            self.manager.current = "profile"

    def on_keys_pressed(self):
        """Handle VPN keys button press."""
        logger.info("Navigating to keys screen")
        if self.manager:
            self.manager.current = "keys_list"

    def on_buy_pressed(self):
        """Handle buy packages button press."""
        logger.info("Navigating to shop screen")
        if self.manager:
            self.manager.current = "shop"

    def on_support_pressed(self):
        """Handle support button press."""
        logger.info("Navigating to support screen")
        if self.manager:
            self.manager.current = "tickets"

    def on_new_key_pressed(self):
        """Handle new key quick action."""
        logger.info("Navigating to create key screen")
        if self.manager:
            self.manager.current = "create_key"

    def on_buy_gb_pressed(self):
        """Handle buy GB quick action."""
        logger.info("Navigating to shop screen")
        if self.manager:
            self.manager.current = "shop"

    def on_key_detail_pressed(self, key_id: str):
        """Handle key detail navigation."""
        logger.info(f"Viewing key detail: {key_id}")
        if self.manager:
            # Pass key_id to detail screen
            from kivy.app import App
            app = App.get_running_app()
            if hasattr(app, 'current_key_id'):
                app.current_key_id = key_id
            self.manager.current = "key_detail"

    def on_menu_pressed(self):
        """Handle hamburger menu button press."""
        logger.info("Opening navigation drawer")
        # Open navigation drawer if available
        if self.ids.get('nav_drawer'):
            self.ids.nav_drawer.set_state("open")
        else:
            # Fallback: show menu dialog
            self._show_menu_dialog()

    def _show_menu_dialog(self):
        """Show menu dialog as fallback."""
        menu_items = [
            ("👤 Perfil", lambda x: self._navigate_and_close("profile")),
            ("🔑 Mis Claves", lambda x: self._navigate_and_close("keys_list")),
            ("💰 Comprar Paquete", lambda x: self._navigate_and_close("shop")),
            ("🎁 Referidos", lambda x: self._navigate_and_close("referrals")),
            ("🔧 Soporte", lambda x: self._navigate_and_close("tickets")),
            ("⚙️ Configuración", lambda x: self._navigate_and_close("settings")),
        ]
        
        buttons = [
            MDFlatButton(
                text=item[0],
                theme_text_color="Custom",
                text_color=[0, 0.941, 1, 1],
                on_release=item[1]
            )
            for item in menu_items
        ]
        
        buttons.append(
            MDFlatButton(
                text="CANCELAR",
                theme_text_color="Custom",
                text_color=[0.878, 0.878, 0.878, 1],
                on_release=self.dismiss_dialog
            )
        )
        
        if not self.dialog:
            self.dialog = MDDialog(
                title="Menú",
                type="simple",
                items=[],
                buttons=buttons
            )
        self.dialog.open()

    def _navigate_and_close(self, screen_name: str):
        """Navigate to screen and close dialog."""
        self.dismiss_dialog(None)
        if self.manager and self.manager.has_screen(screen_name):
            self.manager.current = screen_name
