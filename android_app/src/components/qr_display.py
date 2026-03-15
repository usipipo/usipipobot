"""
QR Code display component for VPN key connection strings.
"""

import io
from typing import Optional

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.image import Image
from loguru import logger
from PIL import Image as PILImage


class QrDisplay(Image):
    """
    Component for displaying QR codes from connection strings.

    Features:
    - Generates QR code from connection string (ss://...)
    - Displays as Kivy Image texture
    - Handles async generation to avoid UI blocking
    - Supports placeholder while generating
    """

    # Connection string (ss://... or WireGuard config)
    qr_data = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pending_data = None
        self.allow_stretch = True
        self.keep_ratio = True

    def on_qr_data(self, instance, value):
        """Update QR code when data changes."""
        if value:
            # Schedule generation to avoid blocking UI
            Clock.schedule_once(lambda dt: self._generate_qr(value), 0)
        else:
            self.texture = None

    def _generate_qr(self, data: str) -> None:
        """
        Generate QR code from connection string.

        Args:
            data: Connection string to encode in QR code
        """
        try:
            import qrcode

            # Create QR code
            qr = qrcode.QRCode(
                version=1,  # Smallest size
                error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Generate image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Save to bytes
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            # Load into Kivy texture
            self._load_texture_from_bytes(buf.read())

            logger.debug(f"QR code generated successfully ({len(data)} chars)")

        except ImportError:
            logger.error("qrcode library not available. Install with: pip install qrcode")
            self._show_error_placeholder("QR library not available")
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            self._show_error_placeholder("Error generating QR")

    def _load_texture_from_bytes(self, data: bytes) -> None:
        """
        Load texture from image bytes.

        Args:
            data: PNG image bytes
        """
        try:
            # Create Kivy Image from bytes
            img = PILImage.open(io.BytesIO(data))
            img = img.transpose(PILImage.FLIP_TOP_BOTTOM)  # Flip for Kivy

            # Convert to bytes in Kivy-friendly format
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            # Load texture
            self.source = None  # Clear source
            self.texture = None

            # Use PIL to load and create texture
            img = PILImage.open(buf)
            width, height = img.size
            pixels = img.tobytes("raw", "RGBA")

            # Create texture
            from kivy.graphics.texture import Texture

            texture = Texture.create(size=(width, height), colorfmt="rgba")
            texture.blit_buffer(pixels, colorfmt="rgba", bufferfmt="ubyte")
            texture.flip_vertical()  # Flip back

            self.texture = texture
            logger.debug(f"Texture loaded: {width}x{height}")

        except Exception as e:
            logger.error(f"Error loading texture: {e}")
            self._show_error_placeholder("Error loading QR")

    def _show_error_placeholder(self, message: str) -> None:
        """
        Show error placeholder when QR generation fails.

        Args:
            message: Error message to display
        """
        # For now, just clear the texture
        # In a full implementation, we'd show a visual error state
        self.texture = None
        logger.warning(f"QR placeholder: {message}")

    def clear(self) -> None:
        """Clear the QR code display."""
        self.qr_data = ""
        self.texture = None
