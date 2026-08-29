"""Dithering algorithms for ASCII Lab."""
import numpy as np
from PIL import Image


class DitheringStep:
    """Apply dithering to grayscale image before character mapping."""

    SUPPORTED_ALGORITHMS = ["floyd-steinberg", "atkinson", "ordered", "none"]

    def __init__(self, algorithm: str = "none", levels: int = None):
        """Initialize dithering step.

        Args:
            algorithm: Dithering algorithm name.
            levels: Number of quantization levels. If None, uses charset length.
        """
        algo = algorithm.lower().replace("_", "-")
        if algo not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported dithering algorithm: {algorithm}")
        self.algorithm = algo
        self.levels = levels

    def process(self, image: Image.Image) -> Image.Image:
        if image is None:
            raise ValueError("Invalid image: None")
        if self.algorithm == "none":
            return image

        img_array = np.array(image).astype(float)

        # If levels not specified, we'll quantize to a reasonable range
        # Actual quantization happens in mapping, so here we just spread error
        if self.algorithm == "floyd-steinberg":
            result = self._floyd_steinberg(img_array)
        elif self.algorithm == "atkinson":
            result = self._atkinson(img_array)
        elif self.algorithm == "ordered":
            result = self._ordered(img_array)
        else:
            result = img_array

        result = np.clip(result, 0, 255).astype(np.uint8)
        return Image.fromarray(result, mode="L")

    def _floyd_steinberg(self, img: np.ndarray) -> np.ndarray:
        """Floyd-Steinberg error diffusion."""
        height, width = img.shape
        for y in range(height):
            for x in range(width):
                old_pixel = img[y, x]
                new_pixel = round(old_pixel / 255) * 255
                img[y, x] = new_pixel
                error = old_pixel - new_pixel

                if x + 1 < width:
                    img[y, x + 1] += error * 7 / 16
                if y + 1 < height:
                    if x > 0:
                        img[y + 1, x - 1] += error * 3 / 16
                    img[y + 1, x] += error * 5 / 16
                    if x + 1 < width:
                        img[y + 1, x + 1] += error * 1 / 16
        return img

    def _atkinson(self, img: np.ndarray) -> np.ndarray:
        """Atkinson error diffusion (Macintosh classic)."""
        height, width = img.shape
        for y in range(height):
            for x in range(width):
                old_pixel = img[y, x]
                new_pixel = round(old_pixel / 255) * 255
                img[y, x] = new_pixel
                error = (old_pixel - new_pixel) / 8

                neighbors = [
                    (x + 1, y), (x + 2, y),
                    (x - 1, y + 1), (x, y + 1), (x + 1, y + 1),
                    (x, y + 2),
                ]
                for nx, ny in neighbors:
                    if 0 <= nx < width and 0 <= ny < height:
                        img[ny, nx] += error
        return img

    def _ordered(self, img: np.ndarray) -> np.ndarray:
        """Ordered dithering using Bayer 4x4 matrix."""
        bayer_4x4 = np.array([
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5]
        ]) / 16.0 - 0.5

        height, width = img.shape
        tiled = np.tile(bayer_4x4, (height // 4 + 1, width // 4 + 1))
        tiled = tiled[:height, :width]

        # Add threshold offset and quantize
        img = img + tiled * 255
        return np.clip(img, 0, 255)