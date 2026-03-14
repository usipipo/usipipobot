"""
VPN Key card component for uSipipo VPN Android APK.
Shows VPN key information with status and usage.
"""
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivymd.uix.card import MDCard
from kivymd.uix.ripplebehavior import CommonRippleBehavior


class VpnKeyCard(CommonRippleBehavior, MDCard):
    """
    Reusable VPN key card component.
    
    Features:
    - Key name and type indicator
    - Data usage display
    - Status badge
    - Color-coded by key type (Outline/WireGuard)
    - Click to view details
    """

    # Key properties
    key_name = StringProperty("Mi VPN")
    key_type = StringProperty("outline")  # outline | wireguard
    key_usage = StringProperty("0 GB usados")
    key_status = StringProperty("Activa")
    
    # Computed properties
    key_type_icon = StringProperty("check-circle")
    key_type_color = ListProperty([0, 0.941, 1, 1])  # neon_cyan for Outline
    status_color = ListProperty([0, 1, 0.255, 1])  # terminal_green

    # State
    is_active = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0.102, 0.102, 0.141, 1]  # bg_card

    def on_key_type(self, instance, value):
        """Update colors when key type changes."""
        self._update_type_colors()

    def on_is_active(self, instance, value):
        """Update status when active state changes."""
        self._update_status()

    def _update_type_colors(self):
        """Update colors based on key type."""
        if self.key_type == "outline":
            self.key_type_color = [0, 0.941, 1, 1]  # neon_cyan
            self.key_type_icon = "check-circle"
        elif self.key_type == "wireguard":
            self.key_type_color = [0.6, 0, 1, 1]  # purple
            self.key_type_icon = "shield-check"
        else:
            self.key_type_color = [0.541, 0.541, 0.604, 1]  # text_secondary
            self.key_type_icon = "help-circle"

    def _update_status(self):
        """Update status display."""
        if self.is_active:
            self.key_status = "Activa"
            self.status_color = [0, 1, 0.255, 1]  # terminal_green
        else:
            self.key_status = "Inactiva"
            self.status_color = [0.541, 0.541, 0.604, 1]  # text_secondary

    def set_key_data(self, key_data: dict):
        """
        Set key data from API response.
        
        Args:
            key_data: Dict with key information:
                - name: Key name
                - key_type: outline | wireguard
                - used_bytes: Bytes used
                - is_active: Boolean
        """
        self.key_name = key_data.get("name", "Sin nombre")
        self.key_type = key_data.get("key_type", "outline")
        self.is_active = key_data.get("is_active", True)
        
        # Format usage
        used_bytes = key_data.get("used_bytes", 0)
        self.key_usage = self._format_bytes(used_bytes) + " usados"
        
        # Update displays
        self._update_type_colors()
        self._update_status()

    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes to human-readable string."""
        if bytes_value >= 1_073_741_824:  # 1 GB
            return f"{bytes_value / 1_073_741_824:.2f} GB"
        elif bytes_value >= 1_048_576:  # 1 MB
            return f"{bytes_value / 1_048_576:.2f} MB"
        elif bytes_value >= 1_024:  # 1 KB
            return f"{bytes_value / 1_024:.2f} KB"
        else:
            return f"{bytes_value} B"
