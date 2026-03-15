"""
Data progress bar component for uSipipo VPN Android APK.
Shows data usage with color-coded progress bar.
"""

from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivymd.uix.card import MDCard


class DataProgressBar(MDCard):
    """
    Reusable data progress bar component.

    Features:
    - Percentage-based progress (0-100)
    - Color-coded based on usage level
    - Customizable label and value text
    - Cyberpunk styling
    """

    # Data properties
    percentage = NumericProperty(0.0)
    label_text = StringProperty("Datos")
    value_text = StringProperty("0 GB / 5 GB")

    # Color properties (defaults to cyan)
    bar_color = ListProperty([0, 0.941, 1, 1])  # neon_cyan

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_color()

    def _update_color(self):
        """Update bar color based on percentage."""
        if self.percentage <= 60:
            self.bar_color = [0, 0.941, 1, 1]  # neon_cyan
        elif self.percentage <= 85:
            self.bar_color = [1, 0.584, 0, 1]  # amber
        else:
            self.bar_color = [1, 0.267, 0.267, 1]  # error/red

    def on_percentage(self, instance, value):
        """Called when percentage changes."""
        self._update_color()

    def set_data(self, used_bytes: int, limit_bytes: int):
        """
        Set data usage and automatically calculate percentage.

        Args:
            used_bytes: Bytes used
            limit_bytes: Total bytes limit
        """
        if limit_bytes > 0:
            self.percentage = min(100.0, (used_bytes / limit_bytes) * 100)
        else:
            self.percentage = 0.0

        # Format bytes to human-readable
        self.value_text = f"{self._format_bytes(used_bytes)} / {self._format_bytes(limit_bytes)}"

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
