"""Color handling for ASCII rendering."""
from typing import List, Tuple, Optional
import numpy as np
from PIL import Image


class ColorStep:
    """Extract color information for color ASCII rendering."""

    def __init__(self, mode: str = "monochrome"):
        """Initialize color step.

        Args:
            mode: 'monochrome', 'original', or 'terminal'
        """
        self.mode = mode

    def process(self, image: Image.Image) -> Optional[np.ndarray]:
        """Extract color data from image.

        Returns:
            RGB array if color mode is active, None otherwise.
        """
        if self.mode == "monochrome":
            return None

        if image.mode == "RGB":
            return np.array(image)
        elif image.mode == "RGBA":
            return np.array(image)[:, :, :3]
        elif image.mode == "L":
            # Grayscale - convert to RGB
            gray = np.array(image)
            return np.stack([gray, gray, gray], axis=-1)
        else:
            rgb_image = image.convert("RGB")
            return np.array(rgb_image)