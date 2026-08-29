"""Grayscale conversion step."""
from PIL import Image


class GrayscaleStep:
    """Convert image to grayscale."""

    def process(self, image: Image.Image) -> Image.Image:
        if image is None:
            raise ValueError("Invalid image: None")
        if image.mode == "L":
            return image
        return image.convert("L")