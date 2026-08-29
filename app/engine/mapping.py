"""Character mapping for ASCII rendering."""
from typing import List, Tuple
import numpy as np
from PIL import Image


# Predefined character sets
CHARSETS = {
    "STANDARD": "@%#*+=-:. ",
    "DENSE": "@#%*+=-:. ",
    "MINIMAL": "#. ",
    "BLOCKS": "█▓▒░ ",
    "BINARY": "01",
    "TERMINAL": "@#S%?*+;:",
    "EDGE": "/\\|-_+*",
}


class CharacterMappingStep:
    """Map grayscale pixel values to ASCII characters."""

    def __init__(self, charset: str = None, mode: str = "density"):
        self.mode = mode
        if charset is None:
            charset = CHARSETS["STANDARD"]
        self.charset = self._normalize_charset(charset)

    def _normalize_charset(self, charset: str) -> str:
        """Ensure charset is valid and ordered from dark to light."""
        if not charset:
            raise ValueError("Character set cannot be empty")
        seen = set()
        result = []
        for c in charset:
            if c not in seen:
                seen.add(c)
                result.append(c)
        if not result:
            raise ValueError("Character set cannot be empty after deduplication")
        return "".join(result)

    def process(self, image: Image.Image) -> Tuple[List[str], int, int]:
        """Convert image to 2D array of characters."""
        if image is None:
            raise ValueError("Invalid image: None")

        img_array = np.array(image)
        height, width = img_array.shape[:2]

        if img_array.dtype != np.uint8:
            img_array = (img_array / img_array.max() * 255).astype(np.uint8)

        num_chars = len(self.charset)
        indices = (img_array.astype(float) / 255.0 * (num_chars - 1)).astype(int)
        indices = np.clip(indices, 0, num_chars - 1)

        rows = []
        for y in range(height):
            row = "".join(self.charset[indices[y, x]] for x in range(width))
            rows.append(row)

        return rows, width, height