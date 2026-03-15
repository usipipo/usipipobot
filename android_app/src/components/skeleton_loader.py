"""
Skeleton loader component for uSipipo VPN Android APK.
Shows loading placeholder with shimmer effect.
"""

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivymd.uix.card import MDCard


class SkeletonLoader(MDCard):
    """
    Skeleton loader component for loading states.

    Features:
    - Shimmer animation effect
    - Customizable size
    - Cyberpunk styling
    - Multiple preset sizes
    """

    # Color properties
    base_color = ListProperty([0.15, 0.15, 0.2, 1])
    shimmer_color = ListProperty([0.2, 0.2, 0.25, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._animation = None
        self._start_shimmer()

    def _start_shimmer(self):
        """Start shimmer animation."""
        # Simple pulse animation for now
        # Can be enhanced with gradient shimmer effect
        anim = Animation(md_bg_color=[*self.base_color[:3], 0.8], duration=0.8) + Animation(
            md_bg_color=[*self.base_color[:3], 1.0], duration=0.8
        )
        anim.repeat = True
        anim.start(self)
        self._animation = anim

    def _stop_shimmer(self):
        """Stop shimmer animation."""
        if self._animation:
            self._animation.stop(self)
            self._animation = None

    def on_remove(self, widget):
        """Clean up animation when removed."""
        self._stop_shimmer()
        super().on_remove(widget)

    @classmethod
    def create_text_line(cls, width_ratio=1.0, **kwargs):
        """
        Create a skeleton text line.

        Args:
            width_ratio: Width ratio relative to parent (0.0-1.0)
            **kwargs: Additional arguments

        Returns:
            SkeletonLoader instance configured for text line
        """
        skeleton = cls(**kwargs)
        skeleton.size_hint = (width_ratio, None)
        skeleton.height = 20
        return skeleton

    @classmethod
    def create_card(cls, height=100, **kwargs):
        """
        Create a skeleton card placeholder.

        Args:
            height: Card height in dp
            **kwargs: Additional arguments

        Returns:
            SkeletonLoader instance configured for card
        """
        skeleton = cls(**kwargs)
        skeleton.size_hint = (1, None)
        skeleton.height = height
        return skeleton

    @classmethod
    def create_avatar(cls, size=40, **kwargs):
        """
        Create a skeleton avatar placeholder.

        Args:
            size: Avatar size in dp
            **kwargs: Additional arguments

        Returns:
            SkeletonLoader instance configured for avatar
        """
        skeleton = cls(**kwargs)
        skeleton.size_hint = (None, None)
        skeleton.size = (size, size)
        skeleton.radius = [size / 2]  # Circular
        return skeleton
