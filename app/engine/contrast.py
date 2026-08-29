"""Brightness, contrast, and gamma adjustment."""
import numpy as np
from PIL import Image, ImageEnhance, ImageOps


class ContrastStep:
    """Adjust brightness, contrast, and gamma of an image."""

    def __init__(
        self,
        brightness: float = 1.0,
        contrast: float = 1.0,
        gamma: float = 1.0,
        invert: bool = False,
    ):
        self.brightness = max(0.0, brightness)
        self.contrast = max(0.0, contrast)
        self.gamma = max(0.01, gamma)
        self.invert = invert

    def process(self, image: Image.Image) -> Image.Image:
        if image is None:
            raise ValueError("Invalid image: None")

        # Brightness
        if self.brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(self.brightness)

        # Contrast
        if self.contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(self.contrast)

        # Gamma correction
        if self.gamma != 1.0:
            image = self._apply_gamma(image)

        # Invert
        if self.invert:
            if image.mode == "L":
                image = ImageOps.invert(image)
            else:
                image = ImageOps.invert(image.convert("RGB")).convert(image.mode)

        return image

    def _apply_gamma(self, image: Image.Image) -> Image.Image:
        """Apply gamma correction using lookup table."""
        bands = image.getbands()
        lut = [int(255 * ((i / 255.0) ** (1.0 / self.gamma))) for i in range(256)]
        return image.point(lut * len(bands))