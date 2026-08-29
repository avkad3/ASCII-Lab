"""Image resizing with aspect ratio correction."""
from typing import Tuple
from PIL import Image


class ResizeStep:
    """Resize image to target dimensions with aspect ratio correction.

    Terminal/browser characters are typically taller than wide (~0.5 aspect ratio).
    We compensate by scaling height to preserve visual proportions.
    """

    # Typical terminal character aspect ratio (width / height)
    CHAR_ASPECT_RATIO = 0.5

    def __init__(self, width: int, height: int = None, preserve_aspect: bool = True):
        self.target_width = width
        self.target_height = height
        self.preserve_aspect = preserve_aspect

    def process(self, image: Image.Image) -> Image.Image:
        if image is None or image.size == (0, 0):
            raise ValueError("Invalid image: empty or None")

        orig_width, orig_height = image.size

        if self.preserve_aspect:
            # Account for character aspect ratio
            # If chars are 0.5 as wide as they are tall, we need 2x as many columns
            # as rows to represent the same visual proportion
            ratio = self.target_width / orig_width
            new_height = int(orig_height * ratio * self.CHAR_ASPECT_RATIO)
            new_height = max(1, new_height)
        else:
            new_height = self.target_height or int(orig_height * (self.target_width / orig_width))

        return image.resize((self.target_width, new_height), Image.Resampling.LANCZOS)