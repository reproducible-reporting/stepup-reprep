#!/usr/bin/env python3
"""Write an environment variable to a jpg image."""

from PIL import Image, ImageDraw

from stepup.core.api import getenv


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Converts a hex color string (e.g., '#FFFFFF') to an RGB tuple.

    Parameters
    ----------
    hex_color: The hex color string.

    Returns
    -------
    A tuple of three integers representing the RGB values.
    """
    hex_color = hex_color.lstrip("#")  # Remove the '#' if present
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


# Take colors from environment variables.
fg_color = hex_to_rgb(getenv("FG_COLOR", "#0044AA"))
bg_color = hex_to_rgb(getenv("BG_COLOR", "#FFCC00"))

# Draw a plus.
img = Image.new("RGB", (200, 200), bg_color)
draw = ImageDraw.Draw(img)
draw.line([(20, 20), (180, 180)], fill=fg_color, width=10)
draw.line([(180, 20), (20, 180)], fill=fg_color, width=10)
img.save("image.jpg")
