"""System tray icon image generation."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def create_icon_image():
    """Create system tray icon image.

    Returns:
        PIL.Image: Icon image for system tray

    Raises:
        ImportError: If PIL/Pillow is not installed
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.error("PIL/Pillow is not installed. Install with: pip install pillow")
        raise ImportError(
            "PIL/Pillow is required for tray icon. "
            "Install with: pip install 'claude-monitor[tray]'"
        )

    # Create 64x64 icon
    width = 64
    height = 64

    # Claude theme colors
    bg_color = "#5865F2"  # Claude purple/blue
    fg_color = "white"

    # Create base image
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Draw 'C' letter for Claude
    # Outer circle
    draw.ellipse([8, 8, 56, 56], fill=fg_color, outline=fg_color)
    # Inner circle (to create 'C' shape)
    draw.ellipse([16, 16, 48, 48], fill=bg_color, outline=bg_color)
    # Rectangle to create opening of 'C'
    draw.rectangle([32, 16, 56, 48], fill=bg_color, outline=bg_color)

    return image


def create_status_icon(status: str = "normal", show_warning: bool = False):
    """Create icon with status indicator.

    Args:
        status: Status type ('normal', 'warning', 'error', 'idle')
        show_warning: Whether to show warning indicator

    Returns:
        PIL.Image: Icon with status indicator
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        logger.error("PIL/Pillow is not installed")
        raise ImportError(
            "PIL/Pillow is required for tray icon. "
            "Install with: pip install 'claude-monitor[tray]'"
        )

    # Get base icon
    image = create_icon_image()
    draw = ImageDraw.Draw(image)

    # Status color mapping
    status_colors = {
        "normal": "#00D26A",  # Green
        "warning": "#FAA81A",  # Orange
        "error": "#ED4245",  # Red
        "idle": "#99AAB5",  # Gray
    }

    # Draw status indicator (small circle in bottom-right)
    if status in status_colors or show_warning:
        indicator_color = status_colors.get(
            status if not show_warning else "warning", status_colors["normal"]
        )

        # Draw indicator circle
        indicator_pos = [46, 46, 60, 60]  # Bottom-right corner
        draw.ellipse(indicator_pos, fill=indicator_color, outline="white", width=1)

    return image


def create_animated_icon_frames(num_frames: int = 8):
    """Create frames for animated icon (loading indicator).

    Args:
        num_frames: Number of animation frames

    Returns:
        List[PIL.Image]: List of icon frames for animation
    """
    try:
        from PIL import Image, ImageDraw
        import math
    except ImportError:
        logger.error("PIL/Pillow is not installed")
        raise ImportError(
            "PIL/Pillow is required for tray icon. "
            "Install with: pip install 'claude-monitor[tray]'"
        )

    frames = []
    base_image = create_icon_image()

    for frame in range(num_frames):
        # Copy base image
        img = base_image.copy()
        draw = ImageDraw.Draw(img)

        # Calculate rotation angle
        angle = (frame / num_frames) * 360

        # Draw rotating indicator
        center_x, center_y = 52, 52  # Bottom-right
        radius = 6
        indicator_radius = 2

        # Calculate indicator position
        rad = math.radians(angle)
        x = center_x + radius * math.cos(rad)
        y = center_y + radius * math.sin(rad)

        # Draw indicator
        draw.ellipse(
            [x - indicator_radius, y - indicator_radius, x + indicator_radius, y + indicator_radius],
            fill="#FAA81A",
            outline="white",
        )

        frames.append(img)

    return frames
